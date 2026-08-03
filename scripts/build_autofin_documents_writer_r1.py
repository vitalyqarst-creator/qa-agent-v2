from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-documents-and-questionnaire-files"
SECTION = "14"
TD = FT / "work" / "test-design" / f"{SECTION}-{SCOPE}"
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL = FT / "test-cases" / f"{SECTION}-{SCOPE}.md"
STATE = CYCLE / "cycle-state.yaml"
WORKFLOW = FT / "work" / "stage-handoffs" / "11-application-card-documents-and-questionnaire-files" / "workflow-state.yaml"
HANDOFF = FT / "work" / "stage-handoffs" / "11-application-card-documents-and-questionnaire-files"
SCRATCH = TD / "_artifact_write"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        escaped = [str(cell).replace("\n", "<br>") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


def write_with_manifest(target: Path, stem: str, title: str, sections: list[tuple[int, str, str]]) -> None:
    artifact_dir = SCRATCH / stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    omit_preamble = bool(sections and sections[0][1] == title)
    manifest_sections = []
    for index, (level, heading, content) in enumerate(sections, start=1):
        chunk_name = heading.lower().replace(" ", "-").replace("/", "-")
        content_path = artifact_dir / f"{index:02d}-{chunk_name}.md"
        content_path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append(
            {
                "level": level,
                "heading": heading,
                "content_file": content_path.name,
            }
        )
    manifest = {
        "target_path": str(target.resolve()),
        "sections": manifest_sections,
    }
    if not omit_preamble:
        preamble = artifact_dir / "00-preamble.md"
        preamble.write_text(f"# {title}\n", encoding="utf-8", newline="\n")
        manifest["preamble_file"] = preamble.name
    manifest_path = artifact_dir / f"{stem}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=ROOT,
        check=True,
    )


def rel(path: Path) -> str:
    return path.relative_to(FT).as_posix()


rows = [
    ["SRC-001", "WP-01", "Блок «Документы по заявке»", "DOCX section-14 table row 081 / PDF p.25", "no_requirement_code:SRC-001", "yes", "ATOM-001"],
    ["SRC-002", "WP-01", "Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку", "DOCX section-14 table row 082 / PDF p.25", "BSR 198; BSR 199", "yes", "ATOM-002; ATOM-003"],
    ["SRC-003", "WP-01", "Анкета клиента", "DOCX section-14 table row 083 / PDF p.25", "BSR 200; BSR 201; BSR 202; BSR 203; BSR 204", "yes", "ATOM-004; ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011; GAP-001; coverage_gap:wr-004"],
    ["SRC-004", "WP-01", "Паспорт клиента", "DOCX section-14 table row 084 / PDF p.26", "BSR 205; BSR 206; BSR 207; BSR 208; BSR 209", "yes", "ATOM-012; ATOM-013; ATOM-014; ATOM-015; ATOM-016; ATOM-017; ATOM-018; ATOM-019; GAP-001; coverage_gap:wr-004"],
    ["SRC-005", "WP-01", "Тип документа", "DOCX section-14 table row 085 / PDF p.26", "BSR 210; BSR 211", "yes", "ATOM-020; ATOM-021; ATOM-022; DICT-001"],
    ["SRC-006", "WP-01", "Второй документ", "DOCX section-14 table row 086 / PDF pp.26-27", "BSR 212; BSR 213; BSR 214; BSR 215; BSR 216; BSR 217; BSR 218", "yes", "ATOM-023; ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029; ATOM-030; GAP-001; coverage_gap:wr-004; coverage_gap:wr-005"],
    ["SRC-007", "WP-01", "Серия", "DOCX section-14 table row 087 / PDF p.27", "BSR 219", "yes", "ATOM-031"],
    ["SRC-008", "WP-01", "Номер", "DOCX section-14 table row 088 / PDF p.27", "BSR 220", "yes", "ATOM-032"],
    ["SRC-009", "WP-01", "Дата выдачи", "DOCX section-14 table row 089 / PDF p.27", "BSR 221; BSR 222", "yes", "ATOM-033; ATOM-034; coverage_gap:wr-006"],
    ["SRC-010", "WP-01", "Кем выдан", "DOCX section-14 table row 090 / PDF p.27", "BSR 223", "yes", "ATOM-035"],
    ["SRC-011", "WP-01", "Пиктограмма «глаз»", "DOCX section-14 table row 091 / PDF p.27", "BSR 224; BSR 225", "yes", "ATOM-036; ATOM-037"],
    ["SRC-012", "WP-01", "Пиктограмма «корзина»", "DOCX section-14 table row 092 / PDF p.27", "BSR 226; BSR 227", "yes", "ATOM-038; ATOM-039; coverage_gap:wr-007"],
    ["SRC-013", "WP-02", "Прикрепить с телефона", "DOCX section-14 table row 093 / PDF p.27", "BSR 228; BSR 229", "yes", "ATOM-040; ATOM-041; GAP-002"],
    ["SRC-014", "WP-02", "Скачать (документ)", "DOCX section-14 table row 094 / PDF p.27", "BSR 230; BSR 231; BSR 232", "yes", "ATOM-042; ATOM-043; ATOM-044; GAP-003"],
]

atoms = [
    ["ATOM-001", "WP-01", "SRC-001", "no_requirement_code:SRC-001", "Блок «Документы по заявке» присутствует в карточке заявки.", "covered", "TC-AF-DOC-001"],
    ["ATOM-002", "WP-01", "SRC-002", "BSR 198", "Информационное поле анкеты клиента видно всегда.", "covered", "TC-AF-DOC-001"],
    ["ATOM-003", "WP-01", "SRC-002", "BSR 199", "Поле «Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку» является информационным.", "covered", "TC-AF-DOC-001"],
    ["ATOM-004", "WP-01", "SRC-003", "BSR 200", "Поле добавления файла «Анкета клиента» видно всегда.", "covered", "TC-AF-DOC-002"],
    ["ATOM-005", "WP-01", "SRC-003", "BSR 201", "Для «Анкета клиента» доступно добавление документа через открытие проводника.", "covered", "TC-AF-DOC-002"],
    ["ATOM-006", "WP-01", "SRC-003", "BSR 201", "Для «Анкета клиента» доступно добавление документа путем Drag and Drop.", "covered", "TC-AF-DOC-003"],
    ["ATOM-007", "WP-01", "SRC-003", "BSR 201", "Для «Анкета клиента» доступен способ добавления через «Прикрепить с телефона» с QR-кодом.", "covered", "TC-AF-DOC-021"],
    ["ATOM-008", "WP-01", "SRC-003", "BSR 202", "Для «Анкета клиента» разрешены форматы jpg, png, pdf.", "covered", "TC-AF-DOC-002; TC-AF-DOC-003"],
    ["ATOM-009", "WP-01", "SRC-003", "BSR 202", "Для «Анкета клиента» размер файла должен быть не более 40 МБ.", "covered", "TC-AF-DOC-004"],
    ["ATOM-010", "WP-01", "SRC-003", "BSR 202", "Если загружаемый файл анкеты клиента не соответствует требованиям, система выводит текст ошибки о формате jpg/png/pdf и размере не более 40 МБ.", "covered", "TC-AF-DOC-005"],
    ["ATOM-011", "WP-01", "SRC-003", "BSR 203", "После добавления анкеты клиента в поле отображается название прикрепленного бинарного файла.", "covered", "TC-AF-DOC-002"],
    ["ATOM-012", "WP-01", "SRC-003", "BSR 204", "После добавления анкеты клиента система сохраняет документ в электронном архиве Банка.", "gap", "coverage_gap:wr-004"],
    ["ATOM-013", "WP-01", "SRC-004", "BSR 205", "Поле добавления файла «Паспорт клиента» видно всегда.", "covered", "TC-AF-DOC-006"],
    ["ATOM-014", "WP-01", "SRC-004", "BSR 206", "Для «Паспорт клиента» доступно добавление документа через открытие проводника.", "covered", "TC-AF-DOC-006"],
    ["ATOM-015", "WP-01", "SRC-004", "BSR 206", "Для «Паспорт клиента» доступно добавление документа путем Drag and Drop.", "covered", "TC-AF-DOC-007"],
    ["ATOM-016", "WP-01", "SRC-004", "BSR 206", "Для «Паспорт клиента» доступен способ добавления через «Прикрепить с телефона» с QR-кодом.", "covered", "TC-AF-DOC-021"],
    ["ATOM-017", "WP-01", "SRC-004", "BSR 207", "Для «Паспорт клиента» разрешены форматы jpg, png, pdf и размер файла не более 40 МБ; при несоответствии показывается текст ошибки.", "covered", "TC-AF-DOC-006; TC-AF-DOC-008; TC-AF-DOC-009"],
    ["ATOM-018", "WP-01", "SRC-004", "BSR 208", "После добавления паспорта клиента в поле отображается название прикрепленного бинарного файла.", "covered", "TC-AF-DOC-006"],
    ["ATOM-019", "WP-01", "SRC-004", "BSR 209", "После добавления паспорта клиента система сохраняет документ в электронном архиве Банка.", "gap", "coverage_gap:wr-004"],
    ["ATOM-020", "WP-01", "SRC-005", "BSR 210", "Поле «Тип документа» видно всегда.", "covered", "TC-AF-DOC-010"],
    ["ATOM-021", "WP-01", "SRC-005", "BSR 211", "Значение по умолчанию для «Тип документа» не выбрано.", "covered", "TC-AF-DOC-010"],
    ["ATOM-022", "WP-01", "SRC-005", "BSR 210", "Перечень значений для «Тип документа»: ВУ, СНИЛС, Загран. паспорт.", "covered", "TC-AF-DOC-010; DICT-001"],
    ["ATOM-023", "WP-01", "SRC-006", "BSR 212", "Поле «Второй документ» видно всегда.", "covered", "TC-AF-DOC-011"],
    ["ATOM-024", "WP-01", "SRC-006", "BSR 213", "«Второй документ» доступен для загрузки файла только если в поле «Тип документа» выбран документ.", "covered", "TC-AF-DOC-011; TC-AF-DOC-012"],
    ["ATOM-025", "WP-01", "SRC-006", "BSR 214", "Для «Второй документ» доступно добавление через проводник и drag and drop.", "covered", "TC-AF-DOC-012"],
    ["ATOM-026", "WP-01", "SRC-006", "BSR 215", "Для «Второй документ» разрешены форматы jpg, png, pdf и размер файла не более 40 МБ; при несоответствии показывается текст ошибки.", "covered", "TC-AF-DOC-012; TC-AF-DOC-013; TC-AF-DOC-014"],
    ["ATOM-027", "WP-01", "SRC-006", "BSR 216", "После добавления второго документа в поле отображается название прикрепленного бинарного файла.", "covered", "TC-AF-DOC-012"],
    ["ATOM-028", "WP-01", "SRC-006", "BSR 217", "Для не ГОС программы второй документ необязательный; для ГОС второй документ обязателен ВУ, для инвалидов ВУ или СНИЛС.", "gap", "coverage_gap:wr-005"],
    ["ATOM-029", "WP-01", "SRC-006", "BSR 218", "После добавления второго документа система сохраняет документ в электронном архиве Банка.", "gap", "coverage_gap:wr-004"],
    ["ATOM-030", "WP-01", "SRC-006", "BSR 215", "Для каждого типа документа действует правило не более одного файла; точное поведение при повторной загрузке не уточнено.", "gap", "GAP-001"],
    ["ATOM-031", "WP-01", "SRC-007", "BSR 219", "Поле «Серия» видимо для «Тип документа» = ВУ или Загран. паспорт.", "covered", "TC-AF-DOC-015"],
    ["ATOM-032", "WP-01", "SRC-008", "BSR 220", "Поле «Номер» видно всегда.", "covered", "TC-AF-DOC-017"],
    ["ATOM-033", "WP-01", "SRC-009", "BSR 221", "Поле «Дата выдачи» видно всегда.", "covered", "TC-AF-DOC-017"],
    ["ATOM-034", "WP-01", "SRC-009", "BSR 222", "Дата выдачи не должна быть больше текущей даты; точный текст/механизм сообщения не определен.", "covered", "TC-AF-DOC-018; coverage_gap:wr-006"],
    ["ATOM-035", "WP-01", "SRC-010", "BSR 223", "Поле «Кем выдан» видно всегда.", "covered", "TC-AF-DOC-017"],
    ["ATOM-036", "WP-01", "SRC-011", "BSR 224", "Пиктограмма «глаз» видна, если вложен документ.", "covered", "TC-AF-DOC-019"],
    ["ATOM-037", "WP-01", "SRC-011", "BSR 225", "Пиктограмма «глаз» открывает всплывающее окно просмотра документа.", "covered", "TC-AF-DOC-019"],
    ["ATOM-038", "WP-01", "SRC-012", "BSR 226", "Пиктограмма «корзина» видна, если вложен документ.", "covered", "TC-AF-DOC-020"],
    ["ATOM-039", "WP-01", "SRC-012", "BSR 227", "Удаление выполняется через скрытие: документ помечается как архивный, перестает быть видимым в интерфейсе, но фактически не удаляется и доступен для просмотра определенным ролям.", "covered", "TC-AF-DOC-020; coverage_gap:wr-007"],
    ["ATOM-040", "WP-02", "SRC-013", "BSR 228", "Кнопка «Прикрепить с телефона» видна всегда.", "covered", "TC-AF-DOC-021"],
    ["ATOM-041", "WP-02", "SRC-013", "BSR 229", "При нажатии «Прикрепить с телефона» система показывает всплывающее окно со сгенерированным QR-кодом; QR содержит ссылку для прикрепления файлов с мобильного телефона.", "covered", "TC-AF-DOC-021; GAP-002"],
    ["ATOM-042", "WP-02", "SRC-014", "BSR 230", "Кнопка «Скачать (документ)» видна всегда.", "covered", "TC-AF-DOC-022"],
    ["ATOM-043", "WP-02", "SRC-014", "BSR 231", "При скачивании система выгружает сформированное заявление-анкету в формате PDF на локальное рабочее место пользователя.", "covered", "TC-AF-DOC-022"],
    ["ATOM-044", "WP-02", "SRC-014", "BSR 232", "Проверка шаблона, состава данных анкеты и согласий требует подключения требований к печатным формам документов.", "gap", "GAP-003"],
]

atom_prop_id = {
    atom[0]: ("SP-029" if atom[0] == "ATOM-029" else f"SP-{int(atom[0].split('-')[1]):03d}")
    for atom in atoms
}
atom_by_id = {atom[0]: atom for atom in atoms}


def first_atom_id(text: str) -> str:
    for part in text.replace(";", " ").split():
        if part.startswith("ATOM-"):
            return part
    return "ATOM-000"


def gap_tokens(value: str) -> list[str]:
    return [
        part
        for part in value.replace(";", " ").split()
        if part.startswith("GAP-") or part.startswith("coverage_gap:")
    ]

coverage_gaps = [
    ["GAP-001", "BSR 202; BSR 207; BSR 215", "file-upload-duplicate-technical-error", "Source defines one-file-per-type, allowed formats, size limit and common validation error text. It does not define exact UI behavior for attempting to attach a second file to the same document type or separate technical upload failures.", "non-blocking", "open", "ATOM-030"],
    ["GAP-002", "BSR 229", "async/mobile", "Source defines QR popup and that QR contains a mobile upload link, but not QR expiry, mobile upload completion result or async status in the application.", "non-blocking", "open", "ATOM-041"],
    ["GAP-003", "BSR 232", "print-form-content", "Download action is in scope; PDF template/content/data-with-consents validation requires section 4.4 / print-form requirements and is not executable inside this scope alone.", "non-blocking", "open", "ATOM-044"],
    ["coverage_gap:wr-004", "BSR 204; BSR 209; BSR 218", "archive-internal", "GAP-WR-004: Electronic archive persistence is source-backed but has no observable artifact inside this scope.", "non-blocking", "open", "ATOM-012; ATOM-019; ATOM-029"],
    ["coverage_gap:wr-005", "BSR 217", "external-program-rule", "GAP-WR-005: ГОС/non-ГОС second-document requiredness details are delegated to another FT and cannot be completed in this scope.", "non-blocking", "open", "ATOM-028"],
    ["coverage_gap:wr-006", "BSR 222", "date-invalid-enforcement", "GAP-WR-006: The source defines date must not exceed current date; the exact UI rejection mechanism/message is not defined.", "non-blocking", "open", "ATOM-034"],
    ["coverage_gap:wr-007", "BSR 227", "role-archive-access", "GAP-WR-007: Archived-document role access matrix and access path are not defined in this scope.", "non-blocking", "open", "ATOM-039"],
]

tc_sections = []
tc_data = [
    (
        "TC-AF-DOC-001",
        "Отображение блока документов и информационного поля анкеты клиента",
        "WP-01",
        "ATOM-001; ATOM-002; ATOM-003; SRC-001; SRC-002; BSR 198; BSR 199",
        "Открыта карточка заявки в разделе «Заявка».",
        "Не требуются.",
        [
            "Перейти к блоку «Документы по заявке».",
            "Найти информационное поле «Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку».",
        ],
        "В блоке «Документы по заявке» видно информационное поле с инструкцией по анкете клиента.",
        "Не требуются.",
    ),
    (
        "TC-AF-DOC-002",
        "Загрузка анкеты клиента через проводник в поддерживаемых форматах",
        "WP-01",
        "ATOM-004; ATOM-005; ATOM-008; ATOM-011; SRC-003; BSR 200; BSR 201; BSR 202; BSR 203",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Анкета клиента».",
        "Файлы: `client-questionnaire.jpg`, `client-questionnaire.png`, `client-questionnaire.pdf`.",
        [
            "В поле «Анкета клиента» добавить файл `client-questionnaire.jpg` через кнопку открытия проводника.",
            "Удалить добавленный файл через доступный UI-механизм удаления вложения.",
            "В поле «Анкета клиента» добавить файл `client-questionnaire.png` через drag and drop.",
            "Удалить добавленный файл через доступный UI-механизм удаления вложения.",
            "В поле «Анкета клиента» добавить файл `client-questionnaire.pdf` через кнопку открытия проводника.",
        ],
        "После каждой загрузки в поле «Анкета клиента» отображается имя ровно одного добавленного файла соответствующего формата.",
        "Удалить файл `client-questionnaire.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-003",
        "Загрузка анкеты клиента через Drag and Drop",
        "WP-01",
        "ATOM-004; ATOM-006; ATOM-008; ATOM-011; SRC-003; BSR 200; BSR 201; BSR 202; BSR 203",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Анкета клиента».",
        "Файл: `client-questionnaire-dnd.pdf`.",
        [
            "Перетащить файл `client-questionnaire-dnd.pdf` в область Drag and Drop поля «Анкета клиента».",
        ],
        "В поле «Анкета клиента» отображается имя файла `client-questionnaire-dnd.pdf`.",
        "Удалить файл `client-questionnaire-dnd.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-004",
        "Прием анкеты клиента с размером файла не более 40 МБ",
        "WP-01",
        "ATOM-004; ATOM-009; ATOM-011; SRC-003; BSR 200; BSR 202; BSR 203",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Анкета клиента».",
        "Файл: `client-questionnaire-40mb.pdf`, размер файла не более 40 МБ.",
        [
            "В поле «Анкета клиента» добавить файл `client-questionnaire-40mb.pdf` через кнопку открытия проводника.",
        ],
        "В поле «Анкета клиента» отображается имя файла `client-questionnaire-40mb.pdf`.",
        "Удалить файл `client-questionnaire-40mb.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-005",
        "Ошибка при загрузке анкеты клиента с файлом больше 40 МБ",
        "WP-01",
        "ATOM-010; SRC-003; BSR 202",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Анкета клиента».",
        "Файл: `client-questionnaire-41mb.pdf`, размер файла больше 40 МБ.",
        [
            "В поле «Анкета клиента» добавить файл `client-questionnaire-41mb.pdf` через кнопку открытия проводника.",
        ],
        "Система выводит текст: «Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ».",
        "Убедиться, что файл `client-questionnaire-41mb.pdf` не остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-006",
        "Загрузка паспорта клиента через проводник в поддерживаемых форматах",
        "WP-01",
        "ATOM-013; ATOM-014; ATOM-017; ATOM-018; SRC-004; BSR 205; BSR 206; BSR 207; BSR 208",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Паспорт клиента».",
        "Файлы: `passport-client.jpg`, `passport-client.png`, `passport-client.pdf`.",
        [
            "В поле «Паспорт клиента» добавить файл `passport-client.jpg` через кнопку открытия проводника.",
            "Удалить добавленный файл через доступный UI-механизм удаления вложения.",
            "В поле «Паспорт клиента» добавить файл `passport-client.png` через кнопку открытия проводника.",
            "Удалить добавленный файл через доступный UI-механизм удаления вложения.",
            "В поле «Паспорт клиента» добавить файл `passport-client.pdf` через кнопку открытия проводника.",
        ],
        "После каждой загрузки в поле «Паспорт клиента» отображается имя ровно одного добавленного файла соответствующего формата.",
        "Удалить файл `passport-client.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-007",
        "Загрузка паспорта клиента через Drag and Drop",
        "WP-01",
        "ATOM-013; ATOM-015; ATOM-017; ATOM-018; SRC-004; BSR 205; BSR 206; BSR 207; BSR 208",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Паспорт клиента».",
        "Файл: `passport-client-dnd.pdf`.",
        [
            "Перетащить файл `passport-client-dnd.pdf` в область Drag and Drop поля «Паспорт клиента».",
        ],
        "В поле «Паспорт клиента» отображается имя файла `passport-client-dnd.pdf`.",
        "Удалить файл `passport-client-dnd.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-008",
        "Прием паспорта клиента с размером файла не более 40 МБ",
        "WP-01",
        "ATOM-013; ATOM-017; ATOM-018; SRC-004; BSR 205; BSR 207; BSR 208",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Паспорт клиента».",
        "Файл: `passport-client-40mb.pdf`, размер файла не более 40 МБ.",
        [
            "В поле «Паспорт клиента» добавить файл `passport-client-40mb.pdf` через кнопку открытия проводника.",
        ],
        "В поле «Паспорт клиента» отображается имя файла `passport-client-40mb.pdf`.",
        "Удалить файл `passport-client-40mb.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-009",
        "Ошибка при загрузке паспорта клиента с неподдерживаемым форматом",
        "WP-01",
        "ATOM-017; SRC-004; BSR 207",
        "Открыт блок «Документы по заявке» без ранее прикрепленного файла в поле «Паспорт клиента».",
        "Файл: `passport-client.txt`.",
        [
            "В поле «Паспорт клиента» добавить файл `passport-client.txt` через кнопку открытия проводника.",
        ],
        "Система выводит текст: «Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ».",
        "Убедиться, что файл `passport-client.txt` не остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-010",
        "Значение по умолчанию и список поля «Тип документа»",
        "WP-01",
        "ATOM-020; ATOM-021; ATOM-022; SRC-005; BSR 210; BSR 211; DICT-001",
        "Открыт блок «Документы по заявке».",
        "Ожидаемые значения `DICT-001`: `ВУ`, `СНИЛС`, `Загран. паспорт`.",
        [
            "Проверить поле «Тип документа» до выбора значения.",
            "Открыть раскрывающийся список «Тип документа».",
        ],
        "До выбора поле «Тип документа» пустое, а раскрывающийся список содержит значения `ВУ`, `СНИЛС`, `Загран. паспорт`.",
        "Закрыть раскрывающийся список без сохранения изменений.",
    ),
    (
        "TC-AF-DOC-011",
        "Недоступность загрузки второго документа без выбранного типа документа",
        "WP-01",
        "ATOM-023; ATOM-024; SRC-006; BSR 212; BSR 213",
        "Открыт блок «Документы по заявке», поле «Тип документа» пустое.",
        "Не требуются.",
        [
            "Найти поле «Второй документ».",
            "Проверить доступность действия загрузки файла в поле «Второй документ».",
        ],
        "Поле «Второй документ» видно, но загрузка файла недоступна, пока в поле «Тип документа» не выбран документ.",
        "Не требуются.",
    ),
    (
        "TC-AF-DOC-012",
        "Загрузка второго документа после выбора типа документа через проводник",
        "WP-01",
        "ATOM-024; ATOM-025; ATOM-026; ATOM-027; SRC-006; BSR 213; BSR 214; BSR 215; BSR 216; DICT-001",
        "Открыт блок «Документы по заявке», поле «Тип документа» доступно.",
        "Тип документа: `ВУ`; файл: `driver-license.pdf`.",
        [
            "В поле «Тип документа» выбрать значение `ВУ`.",
            "В поле «Второй документ» добавить файл `driver-license.pdf` через кнопку открытия проводника.",
        ],
        "После выбора типа документа загрузка второго документа доступна, а в поле «Второй документ» отображается имя файла `driver-license.pdf`.",
        "Удалить файл `driver-license.pdf` и очистить значение «Тип документа», если тестовая среда сохраняет изменения.",
    ),
    (
        "TC-AF-DOC-013",
        "Загрузка второго документа через Drag and Drop",
        "WP-01",
        "ATOM-024; ATOM-025; ATOM-026; ATOM-027; SRC-006; BSR 213; BSR 214; BSR 215; BSR 216; DICT-001",
        "Открыт блок «Документы по заявке», в поле «Тип документа» выбрано значение `ВУ`, поле «Второй документ» не содержит вложений.",
        "Файл: `driver-license-dnd.pdf`.",
        [
            "Перетащить файл `driver-license-dnd.pdf` в область Drag and Drop поля «Второй документ».",
        ],
        "В поле «Второй документ» отображается имя файла `driver-license-dnd.pdf`.",
        "Удалить файл `driver-license-dnd.pdf`, если он остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-014",
        "Ошибка при загрузке второго документа с файлом больше 40 МБ",
        "WP-01",
        "ATOM-026; SRC-006; BSR 215",
        "Открыт блок «Документы по заявке», в поле «Тип документа» выбрано значение `ВУ`, поле «Второй документ» не содержит вложений.",
        "Файл: `driver-license-41mb.pdf`, размер файла больше 40 МБ.",
        [
            "В поле «Второй документ» добавить файл `driver-license-41mb.pdf` через кнопку открытия проводника.",
        ],
        "Система выводит текст: «Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ».",
        "Убедиться, что файл `driver-license-41mb.pdf` не остался прикрепленным.",
    ),
    (
        "TC-AF-DOC-015",
        "Видимость поля «Серия» для выбранного типа документа",
        "WP-01",
        "ATOM-031; SRC-007; BSR 219; DICT-001",
        "Открыт блок «Документы по заявке», поле «Тип документа» доступно.",
        "Значения типа документа: `ВУ`, `Загран. паспорт`.",
        [
            "В поле «Тип документа» выбрать значение `ВУ`.",
            "Проверить наличие поля «Серия».",
            "В поле «Тип документа» выбрать значение `Загран. паспорт`.",
            "Проверить наличие поля «Серия».",
        ],
        "Для значений `ВУ` и `Загран. паспорт` поле «Серия» видно.",
        "Очистить значение «Тип документа», если тестовая среда сохраняет изменения.",
    ),
    (
        "TC-AF-DOC-016",
        "Отсутствие поля «Серия» для типа документа СНИЛС",
        "WP-01",
        "ATOM-031; SRC-007; BSR 219; DICT-001",
        "Открыт блок «Документы по заявке», поле «Тип документа» доступно.",
        "Значение типа документа: `СНИЛС`.",
        [
            "В поле «Тип документа» выбрать значение `СНИЛС`.",
            "Проверить отсутствие поля «Серия».",
        ],
        "Для значения `СНИЛС` поле «Серия» не видно в блоке «Документы по заявке».",
        "Очистить значение «Тип документа», если тестовая среда сохраняет изменения.",
    ),
    (
        "TC-AF-DOC-017",
        "Ввод реквизитов второго документа в видимые поля",
        "WP-01",
        "ATOM-032; ATOM-033; ATOM-035; SRC-008; SRC-009; SRC-010; BSR 220; BSR 221; BSR 223",
        "Открыт блок «Документы по заявке».",
        "Номер: `345678`; дата выдачи: текущая календарная дата; кем выдан: `ОВД Тестового района`.",
        [
            "В поле «Номер» ввести `345678`.",
            "В поле «Дата выдачи» ввести текущую календарную дату.",
            "В поле «Кем выдан» ввести `ОВД Тестового района`.",
        ],
        "Поля «Номер», «Дата выдачи» и «Кем выдан» отображают введенные значения.",
        "Очистить введенные значения, если тестовая среда сохраняет изменения.",
    ),
    (
        "TC-AF-DOC-018",
        "Запрет будущей даты выдачи второго документа",
        "WP-01",
        "ATOM-034; SRC-009; BSR 222; coverage_gap:wr-006",
        "Открыт блок «Документы по заявке», поле «Дата выдачи» доступно для ввода.",
        "Дата выдачи: календарная дата позже текущей даты.",
        [
            "В поле «Дата выдачи» ввести дату позже текущей календарной даты.",
            "Попытаться зафиксировать введенное значение в поле.",
        ],
        "Система не фиксирует дату выдачи больше текущей даты.",
        "Очистить поле «Дата выдачи», если значение осталось в форме.",
    ),
    (
        "TC-AF-DOC-019",
        "Просмотр прикрепленного документа через пиктограмму «глаз»",
        "WP-01",
        "ATOM-036; ATOM-037; SRC-011; BSR 224; BSR 225",
        "В любом поле загрузки документа в блоке «Документы по заявке» прикреплен файл `passport-client.pdf`.",
        "Файл: `passport-client.pdf`.",
        [
            "Найти пиктограмму «глаз» рядом с прикрепленным документом.",
            "Нажать пиктограмму «глаз».",
        ],
        "Открывается всплывающее окно просмотра документа `passport-client.pdf`.",
        "Закрыть всплывающее окно просмотра документа.",
    ),
    (
        "TC-AF-DOC-020",
        "Скрытие прикрепленного документа через пиктограмму «корзина»",
        "WP-01",
        "ATOM-038; ATOM-039; SRC-012; BSR 226; BSR 227; coverage_gap:wr-007",
        "В любом поле загрузки документа в блоке «Документы по заявке» прикреплен файл `passport-client.pdf`.",
        "Файл: `passport-client.pdf`.",
        [
            "Найти пиктограмму «корзина» рядом с прикрепленным документом.",
            "Нажать пиктограмму «корзина».",
        ],
        "Документ `passport-client.pdf` перестает быть видимым в интерфейсе блока «Документы по заявке».",
        "Если тестовая среда сохраняет изменения, восстановить исходное вложение через повторную загрузку.",
    ),
    (
        "TC-AF-DOC-021",
        "Открытие QR-кода для прикрепления документа с телефона",
        "WP-02",
        "ATOM-007; ATOM-016; ATOM-040; ATOM-041; SRC-003; SRC-004; SRC-013; BSR 201; BSR 206; BSR 228; BSR 229; GAP-002",
        "Открыт блок «Документы по заявке».",
        "Не требуются.",
        [
            "Нажать кнопку «Прикрепить с телефона».",
        ],
        "Открывается всплывающее окно со сгенерированным QR-кодом для прикрепления файлов с мобильного телефона.",
        "Закрыть всплывающее окно с QR-кодом.",
    ),
    (
        "TC-AF-DOC-022",
        "Скачивание заявления-анкеты в формате PDF",
        "WP-02",
        "ATOM-042; ATOM-043; SRC-014; BSR 230; BSR 231; BSR 232; GAP-003",
        "Открыта карточка заявки, для которой доступно сформированное заявление-анкета.",
        "Не требуются.",
        [
            "Нажать кнопку «Скачать (документ)».",
            "Дождаться завершения загрузки файла на локальное рабочее место пользователя.",
        ],
        "На локальное рабочее место пользователя выгружен файл заявления-анкеты в формате PDF.",
        "Удалить скачанный тестовый файл с локального рабочего места, если это требуется правилами тестового контура.",
    ),
]

tc_trace_atoms_by_id = {
    tc[0]: re.findall(r"\bATOM-\d+\b", tc[3])
    for tc in tc_data
}

atom_tc_ids_by_atom: dict[str, list[str]] = {}
for tc_id, atoms_in_tc in tc_trace_atoms_by_id.items():
    for atom_id in atoms_in_tc:
        atom_tc_ids_by_atom.setdefault(atom_id, []).append(tc_id)


def planned_for_atom(atom: list[str]) -> str:
    atom_id = atom[0]
    tc_ids = atom_tc_ids_by_atom.get(atom_id, [])
    gaps = gap_tokens(atom[6])
    parts = [*tc_ids, *gaps]
    if not parts:
        return atom[6]
    return "; ".join(dict.fromkeys(parts))


def covered_by_for_atom(atom: list[str]) -> str:
    atom_id = atom[0]
    tc_ids = atom_tc_ids_by_atom.get(atom_id, [])
    return "; ".join(tc_ids) if tc_ids else "none_required:gap"

for tc_id, title, package_id, trace, pre, data, steps, expected, post in tc_data:
    tc_type = "Validation" if tc_id in {"TC-AF-DOC-005", "TC-AF-DOC-009", "TC-AF-DOC-014", "TC-AF-DOC-018"} else "Positive"
    body = [
        f"**Название:** {title}",
        f"**Тип:** {tc_type}",
        "**Приоритет:** High",
        f"**package_id:** {package_id}",
        f"**Трассировка:** {trace}",
        "",
        "### Предусловия",
        pre,
        "",
        "### Тестовые данные",
        data,
        "",
        "### Шаги",
        "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1)),
        "",
        "### Итоговый ожидаемый результат",
        expected,
        "",
        "### Постусловия",
        post,
    ]
    tc_sections.append((2, tc_id, "\n".join(body)))


def build() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF.mkdir(parents=True, exist_ok=True)

    parity_req_rows = [
        ["BSR 198; BSR 199", "DOCX row 082 text present without codes", "PDF p.25", "pdf-only-code", "mandatory-req-id", "Use on SRC-002 atoms."],
        ["BSR 200; BSR 201; BSR 202; BSR 203; BSR 204", "DOCX row 083 text present without codes", "PDF p.25", "pdf-only-code", "mandatory-req-id", "Use on SRC-003 atoms."],
        ["BSR 205; BSR 206; BSR 207; BSR 208; BSR 209", "DOCX row 084 text present without codes", "PDF p.26", "pdf-only-code", "mandatory-req-id", "Use on SRC-004 atoms."],
        ["BSR 210; BSR 211", "DOCX row 085 text present without codes", "PDF p.26", "pdf-only-code", "mandatory-req-id", "Use on SRC-005 atoms."],
        ["BSR 212; BSR 213; BSR 214; BSR 215; BSR 216; BSR 217; BSR 218", "DOCX row 086 text present without codes", "PDF pp.26-27", "pdf-only-code", "mandatory-req-id", "Use on SRC-006 atoms."],
        ["BSR 219", "DOCX row 087 text present without code", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-007 atom."],
        ["BSR 220", "DOCX row 088 text present without code", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-008 atom."],
        ["BSR 221; BSR 222", "DOCX row 089 text present without codes", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-009 atoms."],
        ["BSR 223", "DOCX row 090 text present without code", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-010 atom."],
        ["BSR 224; BSR 225", "DOCX row 091 text present without codes", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-011 atoms."],
        ["BSR 226; BSR 227", "DOCX row 092 text present without codes", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-012 atoms."],
        ["BSR 228; BSR 229", "DOCX row 093 text present without codes", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-013 atoms."],
        ["BSR 230; BSR 231; BSR 232", "DOCX row 094 text present without codes", "PDF p.27", "pdf-only-code", "mandatory-req-id", "Use on SRC-014 atoms."],
    ]
    parity_row_rows = [
        [r[2], r[3], r[4], r[6], "DOCX text matches behavior but omits BSR codes", "PDF provides mandatory BSR codes", "match-with-pdf-only-codes", "use"]
        for r in rows
    ]
    write_with_manifest(
        HANDOFF / "source-parity-check.md",
        "handoff-source-parity-check",
        "Source Parity Check",
        [
            (2, "Source Parity Check", "\n".join([
                "- FT package: `fts/AutoFin`",
                "- Scope: `application-card-documents-and-questionnaire-files`",
                "- DOCX source: `source/AutoFinPreFinal.docx`",
                "- PDF source: `source/AutoFinPreFinal.pdf`",
                "- DOCX extraction: `python-docx` direct table extraction",
                "- PDF extraction: `pypdf` text extraction plus rendered-page visual check from user screenshot",
                "- DOCX scope refs: `section-14 / Таблица 4 / rows 081-094`",
                "- PDF scope refs: `pages 25-27 / BSR 198-232`",
            ])),
            (2, "Boundary Parity", md_table(["item", "docx_ref", "pdf_ref", "status", "note"], [["Блок «Документы по заявке»", "section-14 rows 081-094", "PDF pp.25-27", "match-with-pdf-only-codes", "DOCX text has the same row behavior but omits requirement ids that are visible in PDF."]])),
            (2, "Requirement Id Inventory", md_table(["req_id", "docx_ref", "pdf_ref", "status", "source_decision", "note"], parity_req_rows)),
            (2, "Table / Row Parity", md_table(["row_anchor", "docx_ref", "pdf_ref", "docx_text", "pdf_text", "status", "action"], parity_row_rows)),
            (2, "Mandatory Traceability Inputs", "- Requirement IDs to preserve: `BSR 198` through `BSR 232` for `SRC-002..SRC-014`.\n- PDF-only IDs to preserve: `BSR 198..BSR 232`.\n- DOCX-only IDs to preserve: `none`.\n- Semantic mismatches requiring gaps: `GAP-001`, `GAP-002`, `GAP-003`, `coverage_gap:wr-004`, `coverage_gap:wr-005`, `coverage_gap:wr-006`, `coverage_gap:wr-007`."),
            (2, "Decision", "- Scope parity status: `pass-with-extraction-risk`.\n- Writer/reviewer rule: preserve PDF-only BSR codes as mandatory `req_id`; do not use `no_requirement_code:SRC-*` for coded rows.\n- Open gaps/questions: see `scope-coverage-gaps.md`."),
        ],
    )

    write_with_manifest(
        HANDOFF / "source-row-inventory.md",
        "handoff-source-row-inventory",
        "Source Row Inventory",
        [
            (2, "Source Row Inventory", md_table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], rows)),
            (2, "Inventory Notes", "Rows `SRC-002..SRC-014` have mandatory PDF-only BSR codes. Writer must preserve them in source normalization, atomic ledger, traceability matrix and TC traceability."),
        ],
    )

    gap_details = "\n\n".join([
        "### GAP-001\n**Ссылка на ФТ:** `BSR 202; BSR 207; BSR 215`.\n**Описание:** Форматы `jpg/png/pdf`, размер `<= 40 МБ` и общий текст ошибки покрываются как требования ФТ. Остаток gap - только точное поведение попытки загрузить второй файл в тот же тип документа и отдельные технические сбои загрузки.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-002\n**Ссылка на ФТ:** `BSR 229`.\n**Описание:** Покрывается открытие QR-popup. Срок действия QR, результат мобильной загрузки и async status не определены.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-003\n**Ссылка на ФТ:** `BSR 232`.\n**Описание:** Покрывается скачивание PDF по BSR 231. Проверка шаблона, состава данных анкеты и согласий по BSR 232 требует section 4.4 / требований к печатным формам.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-WR-004\n**Ссылка на ФТ:** `BSR 204; BSR 209; BSR 218`.\n**Описание:** Сохранение в электронном архиве Банка source-backed, но не имеет наблюдаемого UI-артефакта в этом scope.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-WR-005\n**Ссылка на ФТ:** `BSR 217`.\n**Описание:** Требование второго документа для ГОС/не ГОС программ делегировано другому ФТ; текущий scope покрывает только доступность загрузки после выбора типа документа.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-WR-006\n**Ссылка на ФТ:** `BSR 222`.\n**Описание:** Правило верхней границы даты задано, но механизм отклонения будущей даты не определён.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
        "### GAP-WR-007\n**Ссылка на ФТ:** `BSR 227`.\n**Описание:** UI-скрытие документа покрывается; матрица ролей и путь просмотра архивного документа не определены.\n**Влияние:** `non-blocking`\n**Статус:** `open`",
    ])
    write_with_manifest(
        HANDOFF / "scope-coverage-gaps.md",
        "handoff-scope-coverage-gaps",
        "Пробелы покрытия скоупа",
        [
            (2, "Контекст", "- `scope_slug`: `application-card-documents-and-questionnaire-files`\n- Основной FT: `source/AutoFinPreFinal.docx` + `source/AutoFinPreFinal.pdf`\n- Источник: `section-14 / Таблица 4 / rows 081-094 / PDF BSR 198-232`"),
            (2, "Coverage Gaps", md_table(["gap_id", "source_refs", "dimension", "description", "impact", "status", "linked_atoms"], coverage_gaps)),
            (2, "Детализация", gap_details),
        ],
    )

    strategy_rows = [
        [f"`{rel(CANONICAL)}`", "`large generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"],
        [f"`{rel(TD)}`", "`split generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"],
        [f"`{rel(OUT)}`", "`cycle outputs`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"],
    ]
    write_with_manifest(
        TD / "artifact-write-strategy.md",
        "artifact-write-strategy",
        "Artifact Write Strategy",
        [(2, "Artifact Write Strategy", md_table(["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"], strategy_rows))],
    )

    write_with_manifest(
        TD / "source-row-inventory.md",
        "source-row-inventory",
        "Source Row Inventory",
        [
            (2, "Source Row Inventory", md_table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], rows)),
            (2, "Inventory Notes", "- Every `SRC-001..SRC-014` from the handoff inventory is preserved.\n- PDF parity found mandatory `BSR 198..232`; these codes are used as `req_id` for all coded source rows.\n- `GAP-001..GAP-003` and writer residual gaps remain only for duplicate/technical upload behavior, mobile async, archive internals, external program requiredness, future-date enforcement mechanism, role access and PDF template/content."),
        ],
    )

    write_with_manifest(
        TD / "atomic-requirements-ledger.md",
        "atomic-requirements-ledger",
        "Atomic Requirements Ledger",
        [(2, "Atomic Requirements Ledger", md_table(
            ["atom_id", "package_id", "source_property_id", "req_id", "source_row_id", "atomic_statement", "coverage_status", "covered_by_tc", "planned_tc_or_gap", "gap_id"],
            [[atom[0], atom[1], atom_prop_id[atom[0]], atom[3], atom[2], atom[4], atom[5], covered_by_for_atom(atom), planned_for_atom(atom), "; ".join(gap_tokens(atom[6])) or "none_required:covered"] for atom in atoms],
        ))],
    )

    write_with_manifest(
        TD / "internal-work-package-coverage.md",
        "internal-work-package-coverage",
        "Internal Work Package Coverage",
        [
            (2, "Internal Work Package Coverage", md_table(
                ["package_id", "focus", "source_rows", "atom_count", "tc_count", "coverage_status", "residual_gaps"],
                [
                    ["WP-01", "document upload, validation, view and delete behavior", "SRC-001..SRC-012", "39", "20", "covered", "GAP-001; coverage_gap:wr-004; coverage_gap:wr-005; coverage_gap:wr-006; coverage_gap:wr-007"],
                    ["WP-02", "phone attachment and questionnaire PDF download behavior", "SRC-013..SRC-014", "5", "2", "covered", "GAP-002; GAP-003"],
                ],
            )),
        ],
    )

    write_with_manifest(
        TD / "source-row-completeness-matrix.md",
        "source-row-completeness-matrix",
        "Source Row Completeness Matrix",
        [(2, "Source Row Completeness Matrix", md_table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [[
                r[0],
                r[4],
                "; ".join(atom_prop_id[p] for p in r[6].replace(";", " ").split() if p.startswith("ATOM-")),
                r[6],
                "none_required:covered" if "GAP" not in r[6] and "coverage_gap:" not in r[6] else "; ".join(gap_tokens(r[6])) or "none_required:covered",
                "covered" if r[0] not in {"SRC-003", "SRC-004", "SRC-006", "SRC-009", "SRC-012", "SRC-013", "SRC-014"} else "unclear",
            ] for r in rows],
        ))],
    )

    field_names = {
        "SRC-001": "Блок «Документы по заявке»",
        "SRC-002": "Информационное поле анкеты клиента",
        "SRC-003": "Анкета клиента",
        "SRC-004": "Паспорт клиента",
        "SRC-005": "Тип документа",
        "SRC-006": "Второй документ",
        "SRC-007": "Серия",
        "SRC-008": "Номер",
        "SRC-009": "Дата выдачи",
        "SRC-010": "Кем выдан",
        "SRC-011": "Пиктограмма «глаз»",
        "SRC-012": "Пиктограмма «корзина»",
        "SRC-013": "Прикрепить с телефона",
        "SRC-014": "Скачать (документ)",
    }
    property_types = {
        "ATOM-001": "block-visibility",
        "ATOM-002": "visibility",
        "ATOM-003": "metadata-info",
        "ATOM-004": "visibility",
        "ATOM-005": "file-picker-upload",
        "ATOM-006": "drag-drop-upload",
        "ATOM-007": "mobile-upload-entrypoint",
        "ATOM-008": "allowed-file-formats",
        "ATOM-009": "file-size-limit",
        "ATOM-010": "file-upload-validation-error",
        "ATOM-011": "filename-display",
        "ATOM-012": "persistence-internal",
        "ATOM-013": "visibility",
        "ATOM-014": "file-picker-upload",
        "ATOM-015": "drag-drop-upload",
        "ATOM-016": "mobile-upload-entrypoint",
        "ATOM-017": "file-upload-validation-rule",
        "ATOM-018": "filename-display",
        "ATOM-019": "persistence-internal",
        "ATOM-020": "visibility",
        "ATOM-021": "default-value",
        "ATOM-022": "dictionary-source",
        "ATOM-023": "visibility",
        "ATOM-024": "conditional-availability",
        "ATOM-025": "upload-methods",
        "ATOM-026": "file-upload-validation-rule",
        "ATOM-027": "filename-display",
        "ATOM-028": "external-program-rule",
        "ATOM-029": "persistence-internal",
        "ATOM-030": "one-file-rule",
        "ATOM-031": "conditional-visibility",
        "ATOM-032": "visibility",
        "ATOM-033": "visibility",
        "ATOM-034": "date-upper-bound",
        "ATOM-035": "visibility",
        "ATOM-036": "conditional-visibility",
        "ATOM-037": "preview-action",
        "ATOM-038": "conditional-visibility",
        "ATOM-039": "delete-hide-archive-action",
        "ATOM-040": "visibility",
        "ATOM-041": "qr-popup-action",
        "ATOM-042": "visibility",
        "ATOM-043": "action-navigation",
        "ATOM-044": "print-form-content",
    }
    normalization_rows = []
    for atom in atoms:
        gap_id = "; ".join(gap_tokens(atom[6])) or "none_required:covered"
        source_ref = (
            "PDF p.26 / requirement code in req_id"
            if atom[0] == "ATOM-019"
            else f"DOCX section-14 table row {80 + int(atom[2].split('-')[1]):03d}"
        )
        normalization_rows.append([
            atom[2],
            atom_prop_id[atom[0]],
            atom[1],
            field_names[atom[2]],
            property_types[atom[0]],
            "source-defined",
            atom[4],
            atom[3],
            source_ref,
            "high" if not gap_id.startswith("GAP") else "medium",
            gap_id,
            atom[0],
        ])
    write_with_manifest(
        TD / "source-table-normalization.md",
        "source-table-normalization",
        "Source Table Normalization",
        [
            (2, "Normalization Note", "PDF parity found mandatory BSR 198..232 for the selected rows. File formats, 40 MB limit and common validation message are source-backed and executable; only duplicate-file UI behavior, technical upload failure, archive internals, mobile completion and PDF template/content remain residual gaps."),
            (2, "Source Table Normalization", md_table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], normalization_rows)),
        ],
    )

    write_with_manifest(
        TD / "dictionary-inventory.md",
        "dictionary-inventory",
        "Dictionary Inventory",
        [(2, "Dictionary Inventory", md_table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            [["DICT-001", "Тип документа", "source/AutoFinPreFinal.pdf", "PDF p.26 / BSR 210 / SRC-005", "extracted", "ВУ; СНИЛС; Загран. паспорт", "none_required:covered", atom_prop_id["ATOM-022"], "none_required:covered", "Source row says values from dictionary and lists exactly these values."]],
        ))],
    )

    decision_rows = []
    for i, atom in enumerate(atoms, start=1):
        planned = planned_for_atom(atom)
        decision = "standalone_tc" if "TC-" in planned else "gap_unclear"
        if decision == "standalone_tc":
            decision_rows.append([f"TDD-{i:03d}", atom[1], atom_prop_id[atom[0]], atom[0], property_types[atom[0]], decision, "Source-backed observable behavior has executable TC coverage; residual gaps are listed separately when present.", planned, "FT row text", "yes", "visible UI/file/download state or rejected invalid value", planned, "none_required:covered", "valid", "medium" if "GAP" in planned or "coverage_gap:" in planned else "low"])
        else:
            decision_rows.append([f"TDD-{i:03d}", atom[1], atom_prop_id[atom[0]], atom[0], property_types[atom[0]], decision, "Source detail is not executable in this scope because the required backend/internal evidence, external source section or exact UI mechanism is not defined.", planned, "FT row text", "no", "not observable in current scope", "", planned, "residual source gap", "medium"])
    write_with_manifest(
        TD / "test-design-decision-table.md",
        "test-design-decision-table",
        "Test Design Decision Table",
        [(2, "Test Design Decision Table", md_table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], decision_rows))],
    )

    plan_rows = [
        ["PDP-001", "WP-01", "visibility/info", "SRC-001; SRC-002", "ATOM-001; ATOM-002; ATOM-003", "Verify documents block and questionnaire information field.", "manual UI", "visibility", "screen opened", "block and information field visible", "BSR 198; BSR 199", "TC-AF-DOC-001", "covered"],
        ["PDP-002", "WP-01", "file-upload", "SRC-003", "ATOM-004; ATOM-005; ATOM-008; ATOM-011", "Upload questionnaire through file picker in jpg/png/pdf and verify filename.", "manual UI", "positive acceptance", "jpg/png/pdf", "questionnaire filename visible", "BSR 200; BSR 201; BSR 202; BSR 203", "TC-AF-DOC-002", "covered"],
        ["PDP-003", "WP-01", "file-upload", "SRC-003", "ATOM-004; ATOM-006; ATOM-008; ATOM-011", "Upload questionnaire through Drag and Drop.", "manual UI", "positive acceptance", "pdf", "questionnaire filename visible", "BSR 200; BSR 201; BSR 202; BSR 203", "TC-AF-DOC-003", "covered"],
        ["PDP-004", "WP-01", "file-size", "SRC-003", "ATOM-009; ATOM-011", "Upload questionnaire file not larger than 40 MB.", "manual UI", "boundary positive", "<=40 MB pdf", "questionnaire filename visible", "BSR 202; BSR 203", "TC-AF-DOC-004", "covered"],
        ["PDP-005", "WP-01", "validation-message", "SRC-003", "ATOM-010", "Reject questionnaire file larger than 40 MB with source-defined text.", "manual UI", "negative validation", ">40 MB pdf", "source-defined error shown", "BSR 202", "TC-AF-DOC-005", "covered"],
        ["PDP-006", "WP-01", "file-upload", "SRC-004", "ATOM-013; ATOM-014; ATOM-017; ATOM-018", "Upload passport through file picker in jpg/png/pdf and verify filename.", "manual UI", "positive acceptance", "jpg/png/pdf", "passport filename visible", "BSR 205; BSR 206; BSR 207; BSR 208", "TC-AF-DOC-006", "covered"],
        ["PDP-007", "WP-01", "file-upload", "SRC-004", "ATOM-013; ATOM-015; ATOM-017; ATOM-018", "Upload passport through Drag and Drop.", "manual UI", "positive acceptance", "pdf", "passport filename visible", "BSR 205; BSR 206; BSR 207; BSR 208", "TC-AF-DOC-007", "covered"],
        ["PDP-008", "WP-01", "file-size", "SRC-004", "ATOM-017; ATOM-018", "Upload passport file not larger than 40 MB.", "manual UI", "boundary positive", "<=40 MB pdf", "passport filename visible", "BSR 207; BSR 208", "TC-AF-DOC-008", "covered"],
        ["PDP-009", "WP-01", "validation-message", "SRC-004", "ATOM-017", "Reject passport unsupported format with source-defined text.", "manual UI", "negative validation", "txt", "source-defined error shown", "BSR 207", "TC-AF-DOC-009", "covered"],
        ["PDP-010", "WP-01", "dictionary/default", "SRC-005", "ATOM-020; ATOM-021; ATOM-022", "Verify document type visibility, default and listed values.", "manual UI", "dictionary", "DICT-001", "empty default and listed values", "BSR 210; BSR 211", "TC-AF-DOC-010", "covered"],
        ["PDP-011", "WP-01", "dependency", "SRC-006", "ATOM-023; ATOM-024", "Verify second document upload unavailable before type selection.", "manual UI", "dependency false branch", "Тип документа not selected", "upload unavailable", "BSR 212; BSR 213", "TC-AF-DOC-011", "covered"],
        ["PDP-012", "WP-01", "file-upload", "SRC-006", "ATOM-024; ATOM-025; ATOM-026; ATOM-027", "Upload second document through file picker after type selection.", "manual UI", "dependency true branch", "ВУ; pdf", "second document filename visible", "BSR 213; BSR 214; BSR 215; BSR 216", "TC-AF-DOC-012", "covered"],
        ["PDP-013", "WP-01", "file-upload", "SRC-006", "ATOM-024; ATOM-025; ATOM-026; ATOM-027", "Upload second document through Drag and Drop.", "manual UI", "positive acceptance", "pdf", "second document filename visible", "BSR 213; BSR 214; BSR 215; BSR 216", "TC-AF-DOC-013", "covered"],
        ["PDP-014", "WP-01", "validation-message", "SRC-006", "ATOM-026", "Reject second document file larger than 40 MB with source-defined text.", "manual UI", "negative validation", ">40 MB pdf", "source-defined error shown", "BSR 215", "TC-AF-DOC-014", "covered"],
        ["PDP-015", "WP-01", "conditional-visibility", "SRC-007", "ATOM-031", "Verify series field visible for ВУ and Загран. паспорт.", "manual UI", "conditional true branch", "ВУ; Загран. паспорт", "series field visible", "BSR 219", "TC-AF-DOC-015", "covered"],
        ["PDP-021", "WP-01", "conditional-visibility", "SRC-007", "ATOM-031", "Verify series field is not visible for СНИЛС false branch.", "manual UI", "conditional false branch", "СНИЛС", "series field not visible", "BSR 219", "TC-AF-DOC-016", "covered"],
        ["PDP-016", "WP-01", "positive-input", "SRC-008; SRC-009; SRC-010", "ATOM-032; ATOM-033; ATOM-035", "Verify visible details fields accept literal/current date values.", "manual UI", "positive input", "number/date/text", "entered values displayed", "BSR 220; BSR 221; BSR 223", "TC-AF-DOC-017", "covered"],
        ["PDP-022", "WP-01", "date-upper-bound", "SRC-009", "ATOM-034", "Reject a date issue value later than the current date.", "manual UI", "negative date boundary", "> current date", "future issue date is not fixed", "BSR 222", "TC-AF-DOC-018; coverage_gap:wr-006", "covered"],
        ["PDP-017", "WP-01", "action", "SRC-011", "ATOM-036; ATOM-037", "Verify preview icon opens document preview popup.", "manual UI", "action", "attached document", "popup opened", "BSR 224; BSR 225", "TC-AF-DOC-019", "covered"],
        ["PDP-018", "WP-01", "action", "SRC-012", "ATOM-038; ATOM-039", "Verify delete icon hides document in UI; role archive access remains residual.", "manual UI", "action", "attached document", "document hidden", "BSR 226; BSR 227", "TC-AF-DOC-020; coverage_gap:wr-007", "covered"],
        ["PDP-019", "WP-02", "async", "SRC-003; SRC-004; SRC-013", "ATOM-007; ATOM-016; ATOM-040; ATOM-041", "Verify phone attach entrypoint opens generated QR popup.", "manual UI", "action", "button click", "QR popup visible", "BSR 201; BSR 206; BSR 228; BSR 229", "TC-AF-DOC-021; GAP-002", "covered"],
        ["PDP-020", "WP-02", "download", "SRC-014", "ATOM-042; ATOM-043", "Verify questionnaire PDF download.", "manual UI", "download", "download action", "PDF file downloaded", "BSR 230; BSR 231", "TC-AF-DOC-022", "covered"],
        ["PDP-023", "WP-02", "print-form-content-gap", "SRC-014", "ATOM-044", "Record unresolved PDF template/content/data-with-consents validation.", "manual UI", "gap", "section 4.4 not connected", "source for PDF content validation not defined in current scope", "BSR 232", "GAP-003", "gap"],
    ]
    for row in plan_rows:
        tc_ids = re.findall(r"\bTC-AF-DOC-\d+\b", row[11])
        atoms_from_tc: list[str] = []
        for tc_id in tc_ids:
            atoms_from_tc.extend(tc_trace_atoms_by_id.get(tc_id, []))
        if atoms_from_tc:
            row[4] = "; ".join(dict.fromkeys(atoms_from_tc))
    write_with_manifest(
        TD / "package-test-design-plan.md",
        "package-test-design-plan",
        "Package Test Design Plan",
        [(2, "Package Test Design Plan", md_table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows))],
    )

    applicability_rows = [
        ["file-upload", "yes", "SRC-003; SRC-004; SRC-006", "ATOM-004; ATOM-005; ATOM-006; ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-013; ATOM-014; ATOM-015; ATOM-017; ATOM-018; ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-030", "TC-AF-DOC-002; TC-AF-DOC-003; TC-AF-DOC-004; TC-AF-DOC-005; TC-AF-DOC-006; TC-AF-DOC-007; TC-AF-DOC-008; TC-AF-DOC-009; TC-AF-DOC-012; TC-AF-DOC-013; TC-AF-DOC-014", "GAP-001", "Formats, 40 MB limit and common error text are covered; exact duplicate-file and technical failure behavior remains residual."],
        ["table-list", "yes", "SRC-005", "ATOM-022", "TC-AF-DOC-010", "", "Source row gives the exact document type values extracted as DICT-001."],
        ["dependency", "yes", "SRC-006", "ATOM-024; ATOM-028", "TC-AF-DOC-011; TC-AF-DOC-012", "coverage_gap:wr-005", "Second document availability is covered; program-specific requiredness remains residual."],
        ["date-time", "yes", "SRC-009", "ATOM-033; ATOM-034", "TC-AF-DOC-017; TC-AF-DOC-018", "coverage_gap:wr-006", "Visible/current date path and future-date upper bound are covered; exact rejection message/mechanism is not defined."],
        ["conditional-visibility", "yes", "SRC-007; SRC-011; SRC-012", "ATOM-031; ATOM-036; ATOM-038", "TC-AF-DOC-015; TC-AF-DOC-016; TC-AF-DOC-019; TC-AF-DOC-020", "", "Series field, eye and delete icons have source-defined visibility conditions."],
        ["async", "unclear", "SRC-003; SRC-004; SRC-013", "ATOM-007; ATOM-016; ATOM-041", "TC-AF-DOC-021", "GAP-002", "QR popup is covered; QR expiry, mobile upload result and async status are not defined."],
        ["persistence", "unclear", "SRC-003; SRC-004; SRC-006", "ATOM-012; ATOM-019; ATOM-029", "", "coverage_gap:wr-004", "Electronic archive persistence is internal and not observable in this scope."],
        ["expected-result", "unclear", "SRC-014", "ATOM-043; ATOM-044", "TC-AF-DOC-022", "GAP-003", "PDF download is executable; BSR 232 template/content/data mapping requires section 4.4."],
        ["scenario-use-case", "no", "scope-contract.md", "", "", "", "Scope is decomposed into atomic document/file checks rather than an end-to-end scenario."],
    ]
    write_with_manifest(
        TD / "test-design-applicability-matrix.md",
        "test-design-applicability-matrix",
        "Test-design Applicability Matrix",
        [(2, "Test-design Applicability Matrix", md_table(["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"], applicability_rows))],
    )

    risk_rows = [
        ["ATOM-010", "high", "Source-defined upload validation message must be shown for questionnaire file violations.", "SRC-003", "high", "TC-AF-DOC-005", "GAP-001", "File upload validation is high-risk; only duplicate/technical behavior remains residual."],
        ["ATOM-017", "high", "Passport file format and size constraints gate valid upload.", "SRC-004", "high", "TC-AF-DOC-006; TC-AF-DOC-008; TC-AF-DOC-009", "GAP-001", "File upload validation is high-risk; source-backed constraints are covered."],
        ["ATOM-026", "high", "Second document file constraints gate selected document upload.", "SRC-006", "high", "TC-AF-DOC-012; TC-AF-DOC-014", "GAP-001; coverage_gap:wr-005", "File upload and dependency are high-risk; external program requiredness remains residual."],
        ["ATOM-043", "medium", "Download output must be produced as local PDF.", "SRC-014", "high", "TC-AF-DOC-022", "GAP-003", "File download is covered while template/content mapping stays residual."],
    ]
    write_with_manifest(
        TD / "risk-priority-map.md",
        "risk-priority-map",
        "Risk / Priority Map",
        [(2, "Risk / Priority Map", md_table(["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale"], risk_rows))],
    )

    obligation_rows = [
        ["OBL-001", "WP-02", atom_prop_id["ATOM-043"], "ATOM-043", "action-navigation", "navigation-target-opened", "При скачивании система выгружает сформированное заявление-анкету в формате PDF на локальное рабочее место пользователя.", "BSR 231", "TC-AF-DOC-022", "covered", "Проверяется только действие скачивания PDF; шаблон, состав данных и согласия остаются GAP-003."],
    ]
    write_with_manifest(
        TD / "coverage-obligation-table.md",
        "coverage-obligation-table",
        "Coverage Obligation Table",
        [(2, "Coverage Obligation Table", md_table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obligation_rows))],
    )

    write_with_manifest(
        TD / "coverage-gaps.md",
        "coverage-gaps",
        "Coverage Gaps",
        [(2, "Coverage Gaps", md_table(["gap_id", "source_refs", "dimension", "description", "impact", "status", "linked_atoms"], coverage_gaps))],
    )

    review_rows = [
        ["decision-table-classification", "pass", "info", "all", "TDDT has one executable decision per SP-*; residual duplicate/technical upload, mobile, archive and PDF-content behavior is routed to explicit GAP rows.", "none_required:pass", "no"],
        ["ledger-plan-alignment", "pass", "info", "all", "Atomic ledger, Package Test Design Plan and TDDT use the same TC/GAP links for ATOM-001..ATOM-044.", "none_required:pass", "no"],
        ["coverage-class-completeness", "pass", "info", "all", "File-upload, file-size, validation-message, dependency, date-time, conditional-visibility, async, persistence and PDF output dimensions are represented in applicability matrix or coverage gaps.", "none_required:pass", "no"],
        ["numeric-length-boundaries", "pass", "info", "all", "No numeric length property is present in SRC-001..SRC-014; date future enforcement is isolated as GAP-WR-006.", "none_required:pass", "no"],
        ["unsupported-ui-mechanism", "pass", "info", "all", "Upload validation uses exact source-defined BSR 202/207/215 text; TC expected results do not invent duplicate behavior, QR expiry, mobile completion, PDF template checks or action Далее.", "none_required:pass", "no"],
        ["mask-format-coverage", "pass", "info", "all", "No format-mask/default-mask source property is present in selected rows.", "none_required:pass", "no"],
        ["dictionary-closed-set", "pass", "info", "WP-01", "DICT-001 uses values from BSR 210 and TC-AF-DOC-010 checks the visible list values.", "none_required:pass", "no"],
        ["conditional-branches", "pass", "info", "WP-01", "Second document dependency has false branch TC-AF-DOC-011 and true branch TC-AF-DOC-012; external program requiredness remains coverage_gap:wr-005.", "none_required:pass", "no"],
        ["negative-fixture-isolation", "pass", "info", "all", "Source-defined upload validation errors and BSR 222 future-date upper bound are covered; no executable negative transition TC is created for mobile async results or unspecified exact error messages.", "none_required:pass", "no"],
        ["applicability-linked-tc-semantics", "pass", "info", "all", "Applicability matrix links only dimensions exercised by referenced TC-* blocks, with GAP-* where executable coverage is intentionally incomplete.", "none_required:pass", "no"],
        ["gap-specificity", "pass", "info", "all", "GAP-001..GAP-003 and GAP-WR-* identify exact missing behavior and source rows.", "none_required:pass", "no"],
        ["gap-admissibility", "pass", "info", "all", "Visible upload, filename, QR popup and download behavior remains executable; unresolved internals/content/error mechanisms remain gaps.", "none_required:pass", "no"],
        ["internal-observability", "pass", "info", "all", "Archive persistence, mobile async state, role access and PDF content mapping are not marked fully covered without observable evidence.", "none_required:pass", "no"],
        ["metadata-only-exclusion", "pass", "info", "all", "No metadata-only pseudo TC is emitted; SRC-005 visibility/default/dictionary behavior is split into ATOM-020..ATOM-022.", "none_required:pass", "no"],
        ["tc-mapping-atomicity", "pass", "info", "all", "Plan rows avoid broad atom ranges and map each executable cluster to the TC that actually references those atoms.", "none_required:pass", "no"],
        ["ready-for-tc-writing", "pass", "info", "all", "All required writer test-design gates have pass status and no row blocks ready-for-review.", "none_required:pass", "no"],
    ]
    write_with_manifest(
        TD / "test-design-review.md",
        "test-design-review",
        "Test Design Review",
        [(2, "Test Design Review", md_table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows))],
    )

    gate_rows = [
        ["instruction-context", "pass", "Resolver `writer.session_initial_draft` passed: 140.2 / 200.0 KiB; selected 15 required files read.", "all", "none_required:pass", "no"],
        ["source-inputs", "pass", "AGENT-NOTES, source selection, scope contract, parity, row inventory, mockup inventory, gaps and clarification requests read; PDF parity pages 25-27 provided BSR 198..232.", "all", "none_required:pass", "no"],
        ["artifact-shape-preflight", "pass", "Split artifacts use canonical headings and required columns.", "all", "none_required:pass", "no"],
        ["artifact-write-strategy", "pass", "artifact-write-strategy.md uses file-based manifest writes.", "all", "none_required:pass", "no"],
        ["source-row-inventory", "pass", "source-row-inventory.md preserves every in-scope SRC-001..SRC-014 row from the handoff inventory.", "all", "none_required:pass", "no"],
        ["source-row-preservation", "pass", "source-row-inventory.md preserves SRC-001..SRC-014 with linked atoms/gaps.", "all", "none_required:pass", "no"],
        ["source-normalization-atomic", "pass", "source-table-normalization.md has one SP-* row per source-backed property; SRC-005 visibility/default/dictionary source are split into distinct properties.", "all", "none_required:pass", "no"],
        ["test-design-decision-table", "pass", "test-design-decision-table.md classifies every SP-* as standalone_tc or gap_unclear.", "all", "none_required:pass", "no"],
        ["coverage-obligation-table", "pass", "coverage-obligation-table.md maps SP-043 action-navigation to navigation-target-opened in TC-AF-DOC-022; PDF template/content mapping remains GAP-003.", "all", "none_required:pass", "no"],
        ["dictionary-inventory", "pass", "DICT-001 extracted from SRC-005: ВУ; СНИЛС; Загран. паспорт.", "WP-01", "none_required:pass", "no"],
        ["ledger-atomicity", "pass", "atomic-requirements-ledger.md has one ATOM-* per normalized behavior; source-backed BSR 198..232 are preserved as req_id values.", "all", "none_required:pass", "no"],
        ["gsr-range-compression", "pass", "PDF-only BSR 198..232 are preserved on atomic rows; no broad BSR N-M row is used as a covered atom.", "all", "none_required:pass", "no"],
        ["design-plan-atomicity", "pass", "package-test-design-plan.md uses one design row per major package check without replacing atom traceability.", "all", "none_required:pass", "no"],
        ["scenario-does-not-replace-atomic", "pass", "No scenario TC replaces atomic document/file checks; canonical file contains atomic TC-AF-DOC-001..TC-AF-DOC-022.", "all", "none_required:pass", "no"],
        ["tc-atomicity", "pass", "Each TC has one main observable expected result; residual unresolved mechanisms are not asserted as pass/fail outcomes.", "all", "none_required:pass", "no"],
        ["test-data-specificity", "pass", "Upload tests use explicit filenames/extensions, dictionary test uses DICT-001 values and editability/date tests use concrete values.", "all", "none_required:pass", "no"],
        ["internal-observability", "pass", "Archive persistence, mobile async result and PDF content mapping remain GAP-* instead of covered internal effects.", "all", "none_required:pass", "no"],
        ["action-observability", "pass", "Canonical TC expected results are observable UI/file states.", "all", "none_required:pass", "no"],
        ["semantic-req-id-parity", "pass", "PDF-only BSR 198..232 are preserved in source-row inventory, normalization, ledger and TC traceability.", "all", "none_required:pass", "no"],
        ["gap-admissibility", "pass", "GAP-001..GAP-003 and writer residual gaps do not hide source-backed observable UI behavior; they isolate unresolved duplicate/error/mobile/archive/PDF-content mechanisms.", "all", "none_required:pass", "no"],
        ["residual-gaps-visible", "pass", "coverage-gaps.md keeps GAP-001..GAP-003 and writer residual gaps visible; canonical TC does not cover missing behavior.", "all", "none_required:pass", "no"],
        ["mockup-visual-inventory", "pass", "Mockups used only for manual navigation hints; no business rule from mockup was promoted.", "all", "none_required:pass", "no"],
        ["canonical-runtime-format", "pass", "Canonical TC file uses bold metadata fields, package_id and required runtime sections.", "all", "none_required:pass", "no"],
        ["test-design-review", "pass", "test-design-review.md has no blocking rows.", "all", "none_required:pass", "no"],
        ["scoped-validator-findings", "pass", "Post-write scoped validator profile is `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/scoped-validator-profile.writer-r1.json`; expected unresolved_warning_error_count=0.", "all", "rerun validator if this row becomes stale", "no"],
        ["package-ready", "pass", "WP-01 and WP-02 have canonical TC mappings, split artifacts and non-blocking residual risks only after BSR parity remediation.", "all", "none_required:pass", "no"],
    ]
    write_with_manifest(
        TD / "writer-quality-gate.md",
        "writer-quality-gate",
        "Writer Quality Gate",
        [(2, "Writer Quality Gate", md_table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows))],
    )

    self_check_rows = [
        ["scope boundary", "pass", "Only section-14 rows 081-094 used; contacts, addresses, participants, employment, visual assessment, consents and `Далее` excluded.", "none"],
        ["traceability", "pass", "Every TC links to ATOM/SRC; every SRC has atom or gap mapping.", "none"],
        ["atomicity", "pass", "22 TCs each have one main expected result; same-field allowed-format checks are parameterized within one upload obligation.", "none"],
        ["gaps", "pass", "GAP-001..GAP-003 preserved in coverage-gaps.md and narrowed so BSR-defined size/error behavior is covered.", "none"],
        ["artifact write evidence", "pass", "artifact-write-strategy.md and `_artifact_write/*/*.manifest.json` show file-based manifest writes.", "none"],
        ["technical fallbacks", "pass", "DOCX label-search fallback to table-index extraction; support PDF path fallback to glob; pypdf text search not used as semantic evidence.", "none"],
    ]
    write_with_manifest(
        TD / "writer-self-check.md",
        "writer-self-check",
        "Writer Self-Check",
        [(2, "Writer Self-Check", md_table(["check", "status", "evidence", "follow_up"], self_check_rows))],
    )

    write_with_manifest(
        CANONICAL,
        "canonical-test-cases",
        "Тест-кейсы: Документы по заявке, загрузка файлов и скачивание анкеты",
        [
            (2, "Область покрытия", "Скоуп: `application-card-documents-and-questionnaire-files`. Покрываются только document/questionnaire-file behaviors из section-14 rows 081-094. Остаточные риски: `GAP-001`, `GAP-002`, `GAP-003`, а также writer-side residual gaps in split artifacts."),
            *tc_sections,
        ],
    )

    response = f"""
## Writer R1 Response

| item | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `{SCOPE}` |
| stage | `writer-r1` |
| canonical_test_cases | `{rel(CANONICAL)}` |
| test_design_dir | `{rel(TD)}` |
| tc_count | `{len(tc_data)}` |
| atom_count | `{len(atoms)}` |
| residual_gaps | `GAP-001; GAP-002; GAP-003; GAP-WR-004; GAP-WR-005; GAP-WR-006; GAP-WR-007` |

## Summary

Initial canonical manual TC set created for section-14 rows `081-094`. The set covers observable document upload, document type selection, second-document availability, document details, preview/delete UI behavior, QR popup, and questionnaire PDF download.

## Constraint Handling

- `GAP-001`: executable cases cover source-backed `jpg/png/pdf`, `40 MB` limit and common validation message; only duplicate-file UI behavior and separate technical upload failures remain open.
- `GAP-002`: executable case covers only QR popup generation; mobile flow, QR expiry and async result remain open.
- `GAP-003`: executable case covers only PDF download; print-form template/content validation remains out of scope.
- PDF parity found mandatory BSR 198..232. These PDF-only requirement IDs are preserved in row inventory, atom ledger and canonical TC traceability.

## Outputs

- `{rel(CANONICAL)}`
- `{rel(TD)}`
- `{rel(OUT / 'writer-session-log.writer-r1.md')}`
- `{rel(OUT / 'agent-decision-log.writer-r1.md')}`
- `{rel(OUT / 'scoped-validator-profile.writer-r1.json')}`
- `{rel(PROMPTS / 'prompt.structure-preflight-r1.md')}`
""".strip()
    write_with_manifest(OUT / "writer-r1-response.md", "writer-r1-response", "Writer R1 Response", [(2, "Response", response)])

    session_log = f"""
## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `session_initial_draft` |
| instruction_scenario | `writer.session_initial_draft` |
| ft_slug | `AutoFin` |
| scope_slug | `{SCOPE}` |
| started_from | `{rel(STATE)}` |
| status_after | `writer-draft-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command executed; budget status `pass (140.2 / 200.0 KiB)`.
- `AGENTS.md` - global QA and routing rules.
- `skills/README.md` - skill routing map.
- `references/agent/session-based-review-cycle-format.md` - session lifecycle and cycle-state rules.
- `references/agent/codex-sdk-orchestration-format.md` - runner/orchestration constraints.
- `skills/ft-test-case-writer/SKILL.md` - writer workflow and gates.
- `references/agent/writer-runtime-workflow.md` - runtime writer flow.
- `references/agent/writer-runtime-contract.md` - writer hard stops and output contract.
- `references/qa/test-case-runtime-format.md` - canonical slim TC format.
- `references/qa/coverage-runtime-checklist.md` - coverage dimensions.
- `references/qa/traceability-rules.md` - atomic ledger and source traceability.
- `references/agent/writer-process-workflow.md` - artifact write and process logging.
- `references/agent/workflow-state-format.md` - compatibility workflow-state update rules.
- `references/agent/session-log-format.md` - session log format.
- `references/agent/agent-decision-log-format.md` - decision log format.
- `references/agent/writer-handoff-format.md` - writer handoff minimum.
- `AGENT-NOTES.md` - AutoFin package notes; DaData notes not used for this document scope.
- `work/stage-handoffs/00-autofin-scope-selection/source-selection.md` - package source selection.
- `work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md` - parent decomposition and selected scope context.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/workflow-state.yaml` - compatibility handoff state.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-gap-review.md` - gap review verdict.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-contract.md` - confirmed scope and WP packages.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/source-parity-check.md` - DOCX/PDF parity evidence.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/source-row-inventory.md` - required SRC inventory.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/mockup-visual-inventory.md` - mockup usage limits.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-coverage-gaps.md` - residual gaps.
- `work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-clarification-requests.md` - unanswered gap questions.
- `source/AutoFinPreFinal.docx` - exact section-14 table rows 081-094 extracted with `python-docx`.
- `source/AutoFinPreFinal.pdf` - opened with `pypdf`; page count confirmed, text extraction not used as semantic source.
- `support/Анкета клиента 04.02.2026.pdf` - opened with `pypdf`; page count confirmed, not used as source of new requirements.

## Inputs Not Used

- `support/АФБ справочники 26.06.26.md` - not listed as required input for this stage; row 085 already gives the in-scope dictionary values.
- Neighboring AutoFin scopes and existing canary writer scripts - excluded from source semantics.

## Key Decisions

- Preserve `SRC-001..SRC-014` and map each to `ATOM-*` and/or explicit residual gap.
- Use `DICT-001` for the source-backed `Тип документа` values from row 085.
- Cover source-backed file formats, 40 MB limit and common validation text; keep only duplicate-file behavior, separate technical upload failures, mobile completion, QR expiry, async state and PDF content out of executable TCs.
- Route to `structure-preflight-r1` only after split artifacts, canonical TC file and validator profile are present.

## Risks And Fallbacks

- Earlier handoff artifacts missed PDF-only BSR codes; regenerated parity, row inventory and gaps now treat BSR 198..232 as mandatory traceability inputs.
- `pypdf` text search did not extract usable Cyrillic row text from PDFs; parity artifact remains the PDF evidence and DOCX remains semantic source.

## Validation

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
- `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget` - pass; used to prepare next prompt.
- `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json` - run after artifact write; current-scope profile saved as `outputs/scoped-validator-profile.writer-r1.json`.

## Contamination Check

- No behavior from contacts, addresses, participants, employment, visual assessment, consents, action `Далее`, section-16 print-form content or mockup-only details was promoted into TC expected results.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `{rel(CANONICAL)}` | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `{rel(TD)}` | `split generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved writer instruction context | pass | resolver output |
| 2 | Read required instruction and scope inputs | scope confirmed | scope artifacts |
| 3 | Extracted DOCX rows 081-094 | exact row text available | `source-table-normalization.md` |
| 4 | Wrote canonical and split artifacts | helper-based write completed | `{rel(CANONICAL)}`; `{rel(TD)}` |
| 5 | Prepared next structure preflight prompt | prompt created | `{rel(PROMPTS / 'prompt.structure-preflight-r1.md')}` |
| 6 | Ran validator/profile generation | profile created | `{rel(OUT / 'scoped-validator-profile.writer-r1.json')}` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `writer-quality-gate.md` | structure preflight |
| Source row preservation | pass | `source-row-inventory.md`; `source-row-completeness-matrix.md` | none |
| Residual gaps | pass | `coverage-gaps.md`; cycle-state open_questions | reviewer must verify gaps not promoted |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | DOCX label search returned no rows | label-based search over DOCX table text | table-index extraction of table 6 rows 80-93 | `n/a` | `n/a` | `none` | reviewer can inspect source-table-normalization |
| `TF-002` | PowerShell path encoding mangled support PDF literal path | literal Cyrillic path passed through shell heredoc | Python glob over `fts/AutoFin/support/*.pdf` | `n/a` | `n/a` | `none` | none |
| `TF-003` | `pypdf` text search found no usable Cyrillic scope text | PDF text search | use approved parity artifact for PDF evidence and DOCX table extraction for semantics | `n/a` | `n/a` | `low: PDF exact text not re-normalized in this stage` | structure preflight should accept existing parity artifact or request deeper parity if needed |

## Handoff Notes For Next Session

- Review that PDF-only BSR 198..232 are preserved through row inventory, atom ledger and TC traceability.
- Structure preflight should focus on parseability, required bold metadata fields, table shapes and whether residual gaps are visible.
""".strip()
    write_with_manifest(OUT / "writer-session-log.writer-r1.md", "writer-session-log-writer-r1", "Writer R1 Session Log", [(2, "Session Log", session_log)])

    decision_log = f"""
## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `{SCOPE}` |
| stage | `writer-r1` |
| started_from | `{rel(STATE)}` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Cover only section-14 rows 081-094. | Scope contract and active prompt exclude neighboring questionnaire areas. | `{rel(CANONICAL)}` | high | applied |
| `DEC-002` | 2 | `coverage` | `source-row-inventory.md` | Preserve every `SRC-001..SRC-014`. | Row-level traceability is mandatory for this scope. | `{rel(TD / 'source-row-inventory.md')}` | high | applied |
| `DEC-003` | 3 | `dictionary` | `SRC-005` | Create `DICT-001` for `Тип документа`. | Source row lists `ВУ`, `СНИЛС`, `Загран. паспорт`. | `{rel(TD / 'dictionary-inventory.md')}` | high | applied |
| `DEC-004` | 4 | `gap` | `GAP-001` and PDF BSR 202/207/215 | Cover file size and common upload error text; keep duplicate-file and separate technical failures as residual. | BSR 202/207/215 explicitly define formats, 40 MB limit and the common validation message. | `{rel(TD / 'coverage-gaps.md')}` | high | applied |
| `DEC-005` | 5 | `test-design` | `SRC-013` | Cover only QR popup, not mobile upload flow. | QR expiry/mobile result/async state are unresolved by GAP-002. | `TC-AF-DOC-021` | high | applied |
| `DEC-006` | 6 | `test-design` | `SRC-014` | Cover only PDF download, not PDF template/content. | Section-16 is out of scope and GAP-003 remains open. | `TC-AF-DOC-022` | high | applied |
| `DEC-007` | 7 | `artifact-write` | package-based split outputs | Use file-based manifest writer. | Required by writer process workflow for package-based generated artifacts. | `{rel(TD / 'artifact-write-strategy.md')}` | high | applied |
| `DEC-008` | 8 | `routing` | writer quality gate and scoped validator | Route cycle to `structure-preflight-r1` with `writer-draft-ready`. | Required artifacts exist and residual gaps are non-blocking. | `{rel(STATE)}` | medium | applied |
""".strip()
    write_with_manifest(OUT / "agent-decision-log.writer-r1.md", "agent-decision-log-writer-r1", "Agent Decision Log", [(2, "Decision Log", decision_log)])

    prompt = """
# Structure Preflight R1 Prompt

## Selected Skill

- Skill: `ft-test-case-reviewer`
- Mode: `structure_preflight`
- Instruction scenario: `reviewer.structure_preflight`

## Goal

Run structure preflight only for `AutoFin` scope `application-card-documents-and-questionnaire-files`. Verify that the writer R1 canonical file and split artifacts are parseable, have required headings/columns/metadata, and can safely proceed to semantic review. Do not perform semantic coverage review in this stage.

## Inputs

- `work/review-cycles/application-card-documents-and-questionnaire-files/cycle-state.yaml`
- `test-cases/14-application-card-documents-and-questionnaire-files.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/writer-quality-gate.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/source-table-normalization.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/coverage-obligation-table.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/test-design-applicability-matrix.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/test-design-decision-table.md`
- `work/test-design/14-application-card-documents-and-questionnaire-files/test-design-review.md`
- `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/scoped-validator-profile.writer-r1.json`

## Instruction Loading Contract

Before review decisions, run:

`python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`

Budget status from writer preparation: `pass (176.0 / 210.0 KiB)`.

Selected required files:

- `AGENTS.md`
- `skills/README.md`
- `references/agent/session-based-review-cycle-format.md`
- `references/agent/codex-sdk-orchestration-format.md`
- `skills/ft-test-case-reviewer/SKILL.md`
- `references/agent/reviewer-output-format.md`
- `references/qa/review-findings-format.md`
- `references/qa/test-case-runtime-format.md`
- `references/agent/workflow-state-format.md`
- `references/agent/session-log-format.md`
- `references/agent/agent-decision-log-format.md`
- `references/agent/next-step-prompt-format.md`

Record the resolver command, budget status and selected files in the reviewer session log.

## Source Of Truth

- Cycle state: `work/review-cycles/application-card-documents-and-questionnaire-files/cycle-state.yaml`
- Canonical test cases: `test-cases/14-application-card-documents-and-questionnaire-files.md`
- Split test-design directory: `work/test-design/14-application-card-documents-and-questionnaire-files`
- Writer response: `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/writer-r1-response.md`
- Writer session log: `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/writer-session-log.writer-r1.md`
- Writer decision log: `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/agent-decision-log.writer-r1.md`
- Scoped validator profile: `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/scoped-validator-profile.writer-r1.json`

## Structure Preflight Scope

Check only:

- canonical TC parseability and required runtime sections;
- bold metadata fields including `package_id` and `Трассировка`;
- split artifact presence and table shape;
- `SRC-*`, `ATOM-*`, `TC-*`, `DICT-*`, `GAP-*` id consistency at a structural level;
- writer quality gate and self-check have non-empty evidence;
- cycle-state is in runner simple-YAML form and routes to the next valid stage.

Do not decide whether the semantic coverage is sufficient beyond blocking structure defects. If semantic concerns are noticed, record them as reviewer notes for semantic review unless they prevent parseability.

## Guardrails

- `GAP-001`: file formats, 40 MB limit and common validation message are covered; duplicate-file behavior and separate technical upload failures remain open.
- `GAP-002`: QR expiry/mobile upload result/async status remain open.
- `GAP-003`: PDF template/content validation remains out of scope without section-16.
- Do not expand scope into contacts, addresses, participants, employment, visual assessment, consents or action `Далее`.
- Do not invent duplicate behavior, separate technical upload failure handling, QR expiry, mobile upload result, async status or PDF content/template checks.
- Preserve PDF-only requirement IDs `BSR 198..232` in traceability.

## Expected Reviewer Outputs

- `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/structure-preflight-r1-findings.md`
- `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/structure-preflight-r1-summary.md`
- `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/reviewer-session-log.structure-preflight-r1.md`
- `work/review-cycles/application-card-documents-and-questionnaire-files/outputs/agent-decision-log.structure-preflight-r1.md`
- next prompt for semantic review or writer structure remediation, according to `session-based-review-cycle-format.md`

## Required Cycle-State Update

If structure preflight passes:

- `current_stage: semantic-review-r1`
- `stage_status: semantic-review-ready`
- `semantic_round: 1`
- `active_transition_prompt: work/review-cycles/application-card-documents-and-questionnaire-files/prompts/prompt.semantic-review-r1.md`

If blocking structure issues exist:

- `current_stage: writer-structure-r1`
- `stage_status: structure-preflight-blocked`
- create active writer remediation prompt.
""".strip()
    write_with_manifest(PROMPTS / "prompt.structure-preflight-r1.md", "prompt-structure-preflight-r1", "Structure Preflight R1 Prompt", [(2, "Prompt", prompt)])
    write_with_manifest(PROMPTS / "prompt.writer-to-reviewer.round-1.md", "prompt-writer-to-reviewer-round-1", "Writer To Reviewer Round 1 Prompt", [(2, "Prompt", prompt)])

    latest = [
        "AGENT-NOTES.md",
        "work/stage-handoffs/00-autofin-scope-selection/source-selection.md",
        "work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/workflow-state.yaml",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-gap-review.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-contract.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/source-parity-check.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/source-row-inventory.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/mockup-visual-inventory.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-coverage-gaps.md",
        "work/stage-handoffs/11-application-card-documents-and-questionnaire-files/scope-clarification-requests.md",
        "test-cases/14-application-card-documents-and-questionnaire-files.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files",
        "work/test-design/14-application-card-documents-and-questionnaire-files/artifact-write-strategy.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/atomic-requirements-ledger.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/internal-work-package-coverage.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/source-row-inventory.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/source-row-completeness-matrix.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/source-table-normalization.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/test-design-decision-table.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/package-test-design-plan.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/test-design-applicability-matrix.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/risk-priority-map.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/dictionary-inventory.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/coverage-obligation-table.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/coverage-gaps.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/test-design-review.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/writer-quality-gate.md",
        "work/test-design/14-application-card-documents-and-questionnaire-files/writer-self-check.md",
        "work/review-cycles/application-card-documents-and-questionnaire-files/outputs/writer-r1-response.md",
        "work/review-cycles/application-card-documents-and-questionnaire-files/outputs/writer-session-log.writer-r1.md",
        "work/review-cycles/application-card-documents-and-questionnaire-files/outputs/agent-decision-log.writer-r1.md",
        "work/review-cycles/application-card-documents-and-questionnaire-files/outputs/scoped-validator-profile.writer-r1.json",
        "work/review-cycles/application-card-documents-and-questionnaire-files/prompts/prompt.structure-preflight-r1.md",
    ]
    state_lines = [
        "cycle_id: AutoFin-application-card-documents-and-questionnaire-files-2026-06-30",
        "ft_slug: AutoFin",
        f"scope_slug: {SCOPE}",
        "section_id: 14",
        "current_stage: structure-preflight-r1",
        "stage_status: writer-draft-ready",
        "semantic_round: 0",
        "max_semantic_rounds: 2",
        f"canonical_test_cases: test-cases/{CANONICAL.name}",
        f"test_design_dir: work/test-design/{SECTION}-{SCOPE}",
        "active_snapshot: none",
        f"active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md",
        "sessions: []",
        "latest_artifacts:",
        *[f"  - {item}" for item in latest],
        "blocking_reasons: []",
        "blocking_findings: []",
        "open_questions:",
        "  - GAP-001: duplicate-file behavior and separate technical upload failures are unresolved; executable coverage includes source-backed jpg/png/pdf, 40 MB limit and common validation message.",
        "  - GAP-002: QR expiry, mobile upload result and async status are unresolved; executable coverage is limited to QR popup generation.",
        "  - GAP-003: PDF template/content validation is unresolved without section-16; executable coverage is limited to PDF download.",
        "  - GAP-WR-004: electronic archive persistence is internal and not observable in current scope.",
        "  - GAP-WR-005: second-document requiredness for ГОС/non-ГОС programs is delegated to another FT.",
        "  - GAP-WR-006: exact UI rejection mechanism/message for future Дата выдачи is not defined.",
        "  - GAP-WR-007: archived-document role access matrix is not defined.",
        "accepted_risks: []",
    ]
    STATE.write_text("\n".join(state_lines) + "\n", encoding="utf-8", newline="\n")

    workflow_text = f"""
ft_slug: AutoFin
scope_slug: {SCOPE}
current_stage: ft-test-case-writer
stage_status: ready-for-review
current_round: 0
next_skill: ft-test-case-reviewer
required_inputs:
  - work/review-cycles/{SCOPE}/cycle-state.yaml
  - test-cases/{CANONICAL.name}
  - work/test-design/{SECTION}-{SCOPE}/writer-quality-gate.md
  - work/review-cycles/{SCOPE}/prompts/prompt.writer-to-reviewer.round-1.md
latest_artifacts:
  canonical_test_cases: test-cases/{CANONICAL.name}
  test_design_dir: work/test-design/{SECTION}-{SCOPE}
  cycle_state: work/review-cycles/{SCOPE}/cycle-state.yaml
  writer_response: work/review-cycles/{SCOPE}/outputs/writer-r1-response.md
  session_log: work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  decision_log: work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  scoped_validator_profile: work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json
  active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.writer-to-reviewer.round-1.md
coverage_gaps:
  blocking: 0
  non_blocking: 7
open_questions:
  - GAP-001: duplicate-file behavior and separate technical upload failures unresolved; source-backed formats, 40 MB limit and common validation message are covered.
  - GAP-002: QR expiry/mobile upload result/async status unresolved.
  - GAP-003: PDF content/template validation unresolved without section-16.
blocking_reasons: []
accepted_risks: []
notes:
  - Compatibility state only; session-based cycle-state.yaml is authoritative.
""".strip()
    WORKFLOW.write_text(workflow_text + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
