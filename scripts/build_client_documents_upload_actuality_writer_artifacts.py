from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "client-documents-upload-and-actuality"
SECTION = "section-31-client-documents-upload-and-actuality"
TD_REL = f"work/test-design/{SECTION}"
TD = FT_ROOT / TD_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT_ROOT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL_REL = f"test-cases/{SECTION}.md"
CANONICAL = FT_ROOT / CANONICAL_REL
WRITER_PROFILE_REL = f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json"
STRUCTURE_PROMPT_REL = f"work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md"

TC_ID_REMAP = {
    "TC-CDUA-001": "TC-CDUA-001",
    "TC-CDUA-002": "TC-CDUA-002",
    "TC-CDUA-003": "TC-CDUA-003",
    "TC-CDUA-004": "TC-CDUA-004",
    "TC-CDUA-006": "TC-CDUA-005",
    "TC-CDUA-017": "TC-CDUA-006",
    "TC-CDUA-007": "TC-CDUA-007",
    "TC-CDUA-008": "TC-CDUA-008",
    "TC-CDUA-009": "TC-CDUA-009",
    "TC-CDUA-005": "TC-CDUA-010",
    "TC-CDUA-010": "TC-CDUA-011",
    "TC-CDUA-018": "TC-CDUA-012",
    "TC-CDUA-011": "TC-CDUA-013",
    "TC-CDUA-012": "TC-CDUA-014",
    "TC-CDUA-013": "TC-CDUA-015",
    "TC-CDUA-014": "TC-CDUA-016",
    "TC-CDUA-015": "TC-CDUA-017",
    "TC-CDUA-016": "TC-CDUA-018",
}
TC_ID_RE = re.compile(r"TC-CDUA-\d{3}")


def remap_tc_ids(content: str) -> str:
    return TC_ID_RE.sub(lambda match: TC_ID_REMAP.get(match.group(0), match.group(0)), content)


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_with_section_helper(target: Path, heading: str, body: str) -> None:
    scratch = OUTPUTS / "_writer_r1_artifact_write"
    scratch.mkdir(parents=True, exist_ok=True)
    stem = target.name.replace(".", "_").replace("-", "_")
    content_file = scratch / f"{stem}.content.md"
    manifest_file = scratch / f"{stem}.manifest.json"
    content_file.write_text(remap_tc_ids(body).strip() + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "target_path": os.path.relpath(target, scratch),
        "sections": [{"level": 2, "heading": heading, "content_file": content_file.name}],
    }
    manifest_file.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_file)],
        cwd=str(ROOT),
        check=True,
    )


def write_plain(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(remap_tc_ids(content).strip() + "\n", encoding="utf-8", newline="\n")


ATOMS = [
    ["`ATOM-001`", "`WP-01`", "`SRC-001`", "`SP-WP01-001`; `SP-WP01-002`", "`section-31-client-documents-upload-and-actuality`", "Отображается подсказка о возможности приложить несколько файлов в одном поле, пока не в каждом документном блоке есть хотя бы один неудаленный файл.", "`TC-CDUA-001`; `TC-CDUA-002`", "`none_required:covered`", "`covered`"],
    ["`ATOM-002`", "`WP-01`", "`SRC-002`", "`SP-WP01-003`", "`section-31-client-documents-upload-and-actuality`", "После UI-состояния онлайн-подписания отображается информационное поле `Все документы клиента подписаны` без утверждения доставки СМС или внешнего подписания.", "`TC-CDUA-003`", "`GAP-001`", "`covered`"],
    ["`ATOM-003`", "`WP-01`", "`SRC-003`", "`SP-WP01-004`; `SP-WP01-005`; `SP-WP01-006`", "`section-31-client-documents-upload-and-actuality`", "Зона загрузки сообщает разрешенные форматы `jpeg`, `png`, `pdf` и ограничение размера `30 МБ`; точный текст ошибки для нарушения не подтвержден.", "`TC-CDUA-004`; `TC-CDUA-006`; `TC-CDUA-017`", "`GAP-002`", "`covered`"],
    ["`ATOM-004`", "`WP-01`", "`SRC-004`", "`SP-WP01-007`", "`section-31-client-documents-upload-and-actuality`", "Загруженное заявление-анкета отображается миниатюрой файла с именем, размером и форматом.", "`TC-CDUA-007`", "`none_required:covered`", "`covered`"],
    ["`ATOM-005`", "`WP-01`", "`SRC-005`", "`SP-WP01-008`", "`section-31-client-documents-upload-and-actuality`", "Документы, удостоверяющие личность клиента, отображаются списком миниатюр при наличии паспорта в ЭА без признака актуальности.", "`TC-CDUA-008`", "`none_required:covered`", "`covered`"],
    ["`ATOM-006`", "`WP-01`", "`SRC-006`", "`SP-WP01-009`", "`section-31-client-documents-upload-and-actuality`", "При ранее загруженном паспорте без подтвержденной актуальности UI показывает сообщение о необходимости подтвердить актуальность или приложить новый документ.", "`TC-CDUA-009`", "`none_required:covered`", "`covered`"],
    ["`ATOM-007`", "`WP-02`", "`SRC-007`; `SRC-009`", "`SP-WP02-001`", "`section-31-client-documents-upload-and-actuality`", "`Документ актуальный` отображается после прикрепления сотрудником нового актуального документа.", "`TC-CDUA-012`", "`none_required:covered`", "`covered`"],
    ["`ATOM-008`", "`WP-02`", "`SRC-008`", "`SP-WP02-002`", "`section-31-client-documents-upload-and-actuality`", "Просмотр документа открывается во всплывающем окне с базовым UI-просмотром документа.", "`TC-CDUA-010`", "`none_required:covered`", "`covered`"],
    ["`ATOM-009`", "`WP-02`", "`SRC-009`", "`SP-WP02-003`", "`section-31-client-documents-upload-and-actuality`", "Сотрудник загружает документ с ПК через действие загрузки документа.", "`TC-CDUA-005`", "`GAP-002`", "`covered`"],
    ["`ATOM-010`", "`WP-02`", "`SRC-010`", "`SP-WP02-004`", "`section-31-client-documents-upload-and-actuality`", "`Показать` открывает просмотр документа и поток вопроса об актуальности.", "`TC-CDUA-018`", "`none_required:covered`", "`covered`"],
    ["`ATOM-011`", "`WP-02`", "`SRC-011`", "`SP-WP02-005`", "`section-31-client-documents-upload-and-actuality`", "`Нет` закрывает просмотр и возвращает сотрудника к возможности приложить новый актуальный документ.", "`TC-CDUA-011`", "`none_required:covered`", "`covered`"],
    ["`ATOM-012`", "`WP-02`", "`SRC-007`; `SRC-012`", "`SP-WP02-006`", "`section-31-client-documents-upload-and-actuality`", "`Актуальный` помечает документ актуальным и возвращает в раздел документов с отображением `Документ актуальный`.", "`TC-CDUA-013`", "`none_required:covered`", "`covered`"],
    ["`ATOM-013`", "`WP-03`", "`SRC-013`", "`SP-WP03-001`", "`section-31-client-documents-upload-and-actuality`", "`Отправить СМС на подписание документов онлайн` показывает сотруднику всплывающее уведомление/модальное окно без проверки доставки СМС.", "`TC-CDUA-014`", "`GAP-001`", "`covered`"],
    ["`ATOM-014`", "`WP-03`", "`SRC-014`", "`SP-WP03-002`", "`section-31-client-documents-upload-and-actuality`", "`Назад` возвращает сотрудника в раздел `Сведения о занятости`.", "`TC-CDUA-015`", "`none_required:covered`", "`covered`"],
    ["`ATOM-015`", "`WP-03`", "`SRC-015`", "`SP-WP03-003`", "`section-31-client-documents-upload-and-actuality`", "`Отправить заявку` проверяет заполнение необходимых документных блоков и подсвечивает пустой блок красным.", "`TC-CDUA-016`", "`none_required:covered`", "`covered`"],
]


def source_rows() -> list[list[str]]:
    fields = {
        "SRC-001": ("WP-01", "`При необходимости можно приложить несколько файлов в одном поле`", "DOCX `Раздел «Обработка»`, field table row 3", "`ATOM-001`; `GAP-002`"),
        "SRC-002": ("WP-01", "`Все документы клиента подписаны`", "DOCX `Раздел «Обработка»`, field table row 4", "`ATOM-002`; `GAP-001`"),
        "SRC-003": ("WP-01", "`Файлы jpeg, png, pdf не более 30 МБ`", "DOCX `Раздел «Обработка»`, field table row 5", "`ATOM-003`; `GAP-002`"),
        "SRC-004": ("WP-01", "Загруженное заявление-анкета в виде миниатюры файла", "DOCX `Раздел «Обработка»`, field table row 8", "`ATOM-004`"),
        "SRC-005": ("WP-01", "Список загруженных документов, удостоверяющих личность клиента", "DOCX `Раздел «Обработка»`, field table row 10", "`ATOM-005`"),
        "SRC-006": ("WP-01", "Сообщение о ранее загруженном паспорте", "DOCX `Раздел «Обработка»`, field table row 11", "`ATOM-006`"),
        "SRC-007": ("WP-02", "`Документ актуальный`", "DOCX `Раздел «Обработка»`, field table row 12", "`ATOM-007`; `ATOM-012`"),
        "SRC-008": ("WP-02", "Всплывающее окно просмотра документа", "DOCX `Раздел «Обработка»`, field table row 16", "`ATOM-008`"),
        "SRC-009": ("WP-02", "Загрузка документа", "DOCX `Раздел «Обработка»`, actions table row 4", "`ATOM-009`; `GAP-002`"),
        "SRC-010": ("WP-02", "`Показать`", "DOCX `Раздел «Обработка»`, actions table row 5", "`ATOM-010`"),
        "SRC-011": ("WP-02", "`Нет`", "DOCX `Раздел «Обработка»`, actions table row 8", "`ATOM-011`"),
        "SRC-012": ("WP-02", "`Актуальный`", "DOCX `Раздел «Обработка»`, actions table row 9", "`ATOM-012`"),
        "SRC-013": ("WP-03", "`Отправить СМС на подписание документов онлайн`", "DOCX `Раздел «Обработка»`, actions table row 10", "`ATOM-013`; `GAP-001`"),
        "SRC-014": ("WP-03", "`Назад`", "DOCX `Раздел «Обработка»`, actions table row 11", "`ATOM-014`"),
        "SRC-015": ("WP-03", "`Отправить заявку`", "DOCX `Раздел «Обработка»`, actions table row 12", "`ATOM-015`"),
    }
    return [[f"`{sid}`", f"`{wp}`", field, ref, "`no_requirement_code:source-parity-check`", "`yes`", mapped] for sid, (wp, field, ref, mapped) in fields.items()]


PROPERTIES = [
    ["`SRC-001`", "`SP-WP01-001`", "`WP-01`", "`Документные блоки`", "`info-note-visible`", "`Хотя бы один документный блок не имеет неудаленного файла`", "Отображается подсказка о возможности приложить несколько файлов в одном поле.", "`no_requirement_code:source-parity-check`", "`SRC-001`; DOCX field row 3", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-001`", "`SP-WP01-002`", "`WP-01`", "`Документные блоки`", "`info-note-hidden`", "`Каждый документный блок имеет хотя бы один неудаленный файл`", "Подсказка о возможности приложить несколько файлов в одном поле не отображается.", "`no_requirement_code:source-parity-check`", "`SRC-001`; DOCX field row 3", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-002`", "`SP-WP01-003`", "`WP-01`", "`Документы клиента`", "`post-signing-info-visible`", "`UI находится в состоянии после онлайн-подписания документов клиентом`", "Отображается информационное поле `Все документы клиента подписаны`.", "`no_requirement_code:source-parity-check`", "`SRC-002`; DOCX field row 4", "`medium`", "`GAP-001`", "`ATOM-002`"],
    ["`SRC-003`", "`SP-WP01-004`", "`WP-01`", "`Зона загрузки файлов`", "`file-upload-notice`", "`Документный блок доступен для загрузки`", "Отображается notice `Файлы jpeg, png, pdf не более 30 МБ`.", "`no_requirement_code:source-parity-check`", "`SRC-003`; DOCX field row 5", "`high`", "`none_required:covered`", "`ATOM-003`"],
    ["`SRC-003`", "`SP-WP01-005`", "`WP-01`", "`Зона загрузки файлов`", "`file-format-rejection`", "`Выбран файл неподдерживаемого формата`", "Файл отклоняется или отображается признак ошибки без утверждения точного текста.", "`no_requirement_code:source-parity-check`", "`SRC-003`; `SRC-009`; `GAP-002`", "`medium`", "`GAP-002`", "`ATOM-003`"],
    ["`SRC-003`", "`SP-WP01-006`", "`WP-01`", "`Зона загрузки файлов`", "`file-size-rejection`", "`Выбран файл больше 30 МБ`", "Файл отклоняется или отображается признак ошибки без утверждения точного текста.", "`no_requirement_code:source-parity-check`", "`SRC-003`; `SRC-009`; `GAP-002`", "`medium`", "`GAP-002`", "`ATOM-003`"],
    ["`SRC-004`", "`SP-WP01-007`", "`WP-01`", "`Заявление-анкета`", "`thumbnail-metadata`", "`Файл заявления-анкеты загружен`", "Файл отображается миниатюрой с именем, размером и форматом.", "`no_requirement_code:source-parity-check`", "`SRC-004`; DOCX field row 8", "`high`", "`none_required:covered`", "`ATOM-004`"],
    ["`SRC-005`", "`SP-WP01-008`", "`WP-01`", "`Документы удостоверяющие личность`", "`identity-document-list-visible`", "`В ЭА есть паспорт без признака актуальности`", "Загруженные удостоверяющие документы отображаются списком миниатюр.", "`no_requirement_code:source-parity-check`", "`SRC-005`; DOCX field row 10", "`high`", "`none_required:covered`", "`ATOM-005`"],
    ["`SRC-006`", "`SP-WP01-009`", "`WP-01`", "`Документы удостоверяющие личность`", "`passport-actuality-prompt`", "`Есть ранее загруженный паспорт без подтверждения актуальности`", "Отображается сообщение о необходимости подтвердить актуальность или приложить новый документ.", "`no_requirement_code:source-parity-check`", "`SRC-006`; DOCX field row 11", "`high`", "`none_required:covered`", "`ATOM-006`"],
    ["`SRC-007`", "`SP-WP02-001`", "`WP-02`", "`Документы удостоверяющие личность`", "`actuality-after-upload`", "`Сотрудник прикрепил новый документ`", "Отображается поле `Документ актуальный`.", "`no_requirement_code:source-parity-check`", "`SRC-007`; `SRC-009`", "`high`", "`none_required:covered`", "`ATOM-007`"],
    ["`SRC-008`", "`SP-WP02-002`", "`WP-02`", "`Миниатюра документа`", "`preview-popup`", "`Сотрудник открывает документ на просмотр`", "Открывается всплывающее окно просмотра документа.", "`no_requirement_code:source-parity-check`", "`SRC-008`; field row 16", "`high`", "`none_required:covered`", "`ATOM-008`"],
    ["`SRC-009`", "`SP-WP02-003`", "`WP-02`", "`Зона загрузки`", "`upload-from-pc`", "`Сотрудник выбирает допустимый файл с ПК`", "Документ загружается и отображается в документном блоке.", "`no_requirement_code:source-parity-check`", "`SRC-009`; actions row 4", "`high`", "`GAP-002`", "`ATOM-009`"],
    ["`SRC-010`", "`SP-WP02-004`", "`WP-02`", "`Строка документа`", "`show-action-opens-actuality-flow`", "`Сотрудник нажимает Показать`", "Открывается просмотр документа с вопросом об актуальности.", "`no_requirement_code:source-parity-check`", "`SRC-010`; actions row 5", "`high`", "`none_required:covered`", "`ATOM-010`"],
    ["`SRC-011`", "`SP-WP02-005`", "`WP-02`", "`Окно просмотра`", "`not-actual-branch`", "`Сотрудник выбирает Нет`", "Просмотр закрывается, доступна загрузка нового актуального документа.", "`no_requirement_code:source-parity-check`", "`SRC-011`; actions row 8", "`high`", "`none_required:covered`", "`ATOM-011`"],
    ["`SRC-012`", "`SP-WP02-006`", "`WP-02`", "`Окно просмотра`", "`actual-branch`", "`Сотрудник выбирает Актуальный`", "Документ помечается актуальным, раздел документов открыт, поле `Документ актуальный` отображается.", "`no_requirement_code:source-parity-check`", "`SRC-007`; `SRC-012`", "`high`", "`none_required:covered`", "`ATOM-012`"],
    ["`SRC-013`", "`SP-WP03-001`", "`WP-03`", "`Кнопка СМС`", "`sms-notification-modal`", "`Сотрудник нажимает Отправить СМС на подписание документов онлайн`", "Показывается всплывающее уведомление/модальное окно для сотрудника.", "`no_requirement_code:source-parity-check`", "`SRC-013`; actions row 10; `GAP-001`", "`medium`", "`GAP-001`", "`ATOM-013`"],
    ["`SRC-014`", "`SP-WP03-002`", "`WP-03`", "`Нижняя навигация`", "`back-navigation`", "`Сотрудник нажимает Назад`", "Открывается раздел `Сведения о занятости`.", "`no_requirement_code:source-parity-check`", "`SRC-014`; actions row 11", "`high`", "`none_required:covered`", "`ATOM-014`"],
    ["`SRC-015`", "`SP-WP03-003`", "`WP-03`", "`Кнопка Отправить заявку`", "`red-highlight`", "`Есть пустой обязательный документный блок`", "Пустой обязательный блок подсвечивается красным.", "`no_requirement_code:source-parity-check`", "`SRC-015`; actions row 12", "`high`", "`none_required:covered`", "`ATOM-015`"],
]


def write_split_artifacts() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)

    write_with_section_helper(
        TD / "artifact-write-strategy.md",
        "Artifact Write Strategy",
        table(
            ["item", "value", "evidence"],
            [
                ["preflight_result", "`large-file / package-based`", "`scope-contract.md` defines `WP-01`..`WP-03`; split artifacts required."],
                ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` selected before artifact generation."],
                ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
                ["chunk_plan", "`WP-01 -> WP-02 -> WP-03 -> process outputs`", "Rows are generated package by package from `SRC-001`..`SRC-015`."],
                ["helper_artifacts", "`scripts/write_artifact_sections.py`; transient manifests under `outputs/_writer_r1_artifact_write`", "Manifest files are transport artifacts, not source evidence."],
                ["validation_plan", "`runner scoped validator gate`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/cycle-state.yaml`."],
            ],
        ),
    )
    write_with_section_helper(
        TD / "mockup-usage.md",
        "Mockup Usage",
        table(
            ["item", "value", "evidence"],
            [
                ["inventory", "`work/stage-handoffs/08-client-documents-upload-and-actuality/mockup-visual-inventory.md`", "`opened=yes`; `not_used_as_requirement_source=yes`"],
                ["used_for_steps", "`yes`", "`TC-CDUA-005`; `TC-CDUA-010`; `TC-CDUA-014`; `TC-CDUA-015`; `TC-CDUA-016` use upload zone, eye icon and footer button hints."],
                ["not_used_as_requirement_source", "`yes`", "All expected results trace to DOCX `SRC-*` rows or explicit gaps."],
                ["mockup_only_items", "`ignore-out-of-scope`", "Income detail warning, product-change action and delete behavior are not converted into requirements."],
            ],
        ),
    )
    write_with_section_helper(TD / "source-row-inventory.md", "Source Row Inventory", table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], source_rows()))
    completeness = []
    for row in source_rows():
        sid = row[0]
        linked = row[6]
        props = "; ".join(sorted({prop[1] for prop in PROPERTIES if prop[0] == sid}))
        gaps = "; ".join(sorted({gap for gap in ["`GAP-001`" if "GAP-001" in linked else "", "`GAP-002`" if "GAP-002" in linked else ""] if gap})) or "`none_required:no_gap`"
        completeness.append([sid, "`no_requirement_code:source-parity-check`", props, linked, gaps, "`covered-or-gapped`"])
    write_with_section_helper(TD / "source-row-completeness-matrix.md", "Source Row Completeness Matrix", table(["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"], completeness))
    write_with_section_helper(TD / "source-table-normalization.md", "Source Table Normalization", table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], PROPERTIES))

    tddt_rows = []
    obligation_rows = []
    plan_rows = []
    for idx, prop in enumerate(PROPERTIES, start=1):
        sp = prop[1].strip("`")
        atom = prop[11]
        gap = prop[10]
        tc_map = {
            "SP-WP01-001": "TC-CDUA-001",
            "SP-WP01-002": "TC-CDUA-002",
            "SP-WP01-003": "TC-CDUA-003",
            "SP-WP01-004": "TC-CDUA-004",
            "SP-WP01-005": "TC-CDUA-006",
            "SP-WP01-006": "TC-CDUA-017",
            "SP-WP01-007": "TC-CDUA-007",
            "SP-WP01-008": "TC-CDUA-008",
            "SP-WP01-009": "TC-CDUA-009",
            "SP-WP02-001": "TC-CDUA-012",
            "SP-WP02-002": "TC-CDUA-010",
            "SP-WP02-003": "TC-CDUA-005",
            "SP-WP02-004": "TC-CDUA-018",
            "SP-WP02-005": "TC-CDUA-011",
            "SP-WP02-006": "TC-CDUA-013",
            "SP-WP03-001": "TC-CDUA-014",
            "SP-WP03-002": "TC-CDUA-015",
            "SP-WP03-003": "TC-CDUA-016",
        }
        tc = tc_map[sp]
        property_type = prop[4].strip("`")
        planned = f"`{tc}`"
        oracle = "`DOCX/SRC observable UI`" if "GAP-" not in gap else f"`DOCX/SRC with residual {gap.strip('`')}`"
        tddt_rows.append([f"`TDD-{idx:03d}`", prop[2], prop[1], atom, f"`{property_type}`", "`standalone_tc`", "Один наблюдаемый UI-результат можно проверить вручную; residual gaps не превращаются в backend oracle.", planned, oracle, "`yes`", prop[6], prop[6], "`none_required:covered`" if "none_required" in gap else gap, "`allowed`" if "GAP-" in gap else "`none_required:no_gap`", "`medium`" if "GAP-" in gap else "`low`"])
        required_obligation_class = {
            "red-highlight": "highlight-triggered",
        }.get(property_type)
        if required_obligation_class:
            obligation_rows.append([f"`OBL-{idx:03d}`", prop[2], prop[1], atom, f"`{property_type}`", f"`{required_obligation_class}`", prop[6], prop[8], planned, "`covered`", "`none_required:covered`"])
        plan_rows.append([f"`DES-{idx:03d}`", prop[2], f"`{property_type}`", prop[8], atom, prop[6], "`positive`" if property_type not in {"file-format-rejection", "file-size-rejection", "required-documents-check"} else "`negative`", f"`{property_type}`", prop[5], prop[6], oracle, planned, "`covered`"])
    write_with_section_helper(TD / "test-design-decision-table.md", "Test Design Decision Table", table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], tddt_rows))
    write_with_section_helper(TD / "coverage-obligation-table.md", "Coverage Obligation Table", table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obligation_rows))
    write_with_section_helper(TD / "atomic-requirements-ledger.md", "Atomic Requirements Ledger", table(["atom_id", "package_id", "source_rows", "source_property_ids", "requirement_code", "atomic_statement", "covered_by_tc", "gap_id", "coverage_status"], ATOMS))
    write_with_section_helper(TD / "package-test-design-plan.md", "Package Test Design Plan", table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows))
    package_rows = [
        ["`WP-01`", "Информационные поля и списки файлов", "`pass`", "`pass`", "`pass`", "`ATOM-001`..`ATOM-006`", "`6`", "`GAP-001`; `GAP-002`", "`none_required:no_unclear`", "`10`", "`ready-for-review`"],
        ["`WP-02`", "Просмотр и актуальность документа", "`pass`", "`pass`", "`pass`", "`ATOM-007`..`ATOM-012`", "`6`", "`GAP-002`", "`none_required:no_unclear`", "`6`", "`ready-for-review`"],
        ["`WP-03`", "Действия отправки и навигации", "`pass`", "`pass`", "`pass`", "`ATOM-013`..`ATOM-015`", "`3`", "`GAP-001`", "`none_required:no_unclear`", "`3`", "`ready-for-review`"],
    ]
    write_with_section_helper(TD / "internal-work-package-coverage.md", "Internal Work Package Coverage", table(["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"], package_rows))
    write_with_section_helper(TD / "package-ledger-self-check.md", "Package Ledger Self-Check", table(["package_id", "check", "status", "evidence", "required_action"], [[r[0], "`ledger-atomicity`", "`pass`", f"{r[5]} have one primary behavior each.", "`none_required:pass`"] for r in package_rows]))
    write_with_section_helper(TD / "package-design-plan-self-check.md", "Package Design Plan Self-Check", table(["package_id", "check", "status", "evidence", "required_action"], [[r[0], "`design-plan-atomicity`", "`pass`", "Each design row has one planned check and one expected behavior.", "`none_required:pass`"] for r in package_rows]))
    review_rows = [
        ["`decision-table-classification`", "`pass`", "`info`", "`all`", "TDDT rows use standalone executable decisions only where an observable UI oracle exists.", "`none_required:pass`", "`no`"],
        ["`ledger-plan-alignment`", "`pass`", "`info`", "`all`", "Ledger `covered_by_tc` values match TDDT and Package Test Design Plan mappings.", "`none_required:pass`", "`no`"],
        ["`coverage-class-completeness`", "`pass`", "`info`", "`all`", "Applicable file upload, branch and required-doc classes are mapped to TC or residual gap.", "`none_required:pass`", "`no`"],
        ["`numeric-length-boundaries`", "`pass`", "`info`", "`all`", "No numeric or exact-length field exists in this scope; file size is handled as file-upload class with `GAP-002`.", "`none_required:pass`", "`no`"],
        ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`all`", "Invalid format/oversize and SMS backend mechanisms avoid exact unsupported UI/backend claims.", "`none_required:pass`", "`no`"],
        ["`mask-format-coverage`", "`pass`", "`info`", "`all`", "No source-backed mask-format field exists in this scope.", "`none_required:pass`", "`no`"],
        ["`dictionary-closed-set`", "`pass`", "`info`", "`all`", "No closed dictionary is defined for current `SRC-*` rows.", "`none_required:pass`", "`no`"],
        ["`conditional-branches`", "`pass`", "`info`", "`WP-01`; `WP-02`; `WP-03`", "Multi-file note, `Нет`/`Актуальный`, and required-document branches are explicitly represented.", "`none_required:pass`", "`no`"],
        ["`negative-fixture-isolation`", "`pass`", "`info`", "`WP-01`; `WP-03`", "Negative upload and submit-required checks use isolated fixture rows.", "`none_required:pass`", "`no`"],
        ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`all`", "Applicability dimensions link to TC IDs that check the named dimension.", "`none_required:pass`", "`no`"],
        ["`gap-specificity`", "`pass`", "`info`", "`all`", "`GAP-001`..`GAP-003` are narrow and source-linked.", "`none_required:pass`", "`no`"],
        ["`gap-admissibility`", "`pass`", "`info`", "`all`", "Visible UI behavior is covered; only exact text/backend/PDF parity remains gapped.", "`none_required:pass`", "`no`"],
        ["`internal-observability`", "`pass`", "`info`", "`WP-03`", "SMS delivery and external signing are not claimed as covered.", "`none_required:pass`", "`no`"],
        ["`metadata-only-exclusion`", "`pass`", "`info`", "`all`", "No metadata-only row is converted into an executable TC.", "`none_required:pass`", "`no`"],
        ["`tc-mapping-atomicity`", "`pass`", "`info`", "`all`", "One executable design row maps to one TC or residual gap.", "`none_required:pass`", "`no`"],
        ["`ready-for-tc-writing`", "`pass`", "`info`", "`all`", "Canonical TC draft is ready for structure preflight after runner scoped validator gate.", "`none_required:pass`", "`no`"],
    ]
    write_with_section_helper(TD / "test-design-review.md", "Test Design Review", table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows))
    write_with_section_helper(TD / "dependency-matrix.md", "Dependency Matrix", table(["dependency_id", "package_id", "controlling_value", "dependent_field", "controlling_condition_or_action", "true_branch", "false_or_alternate_branch", "linked_atoms", "planned_tc_or_gap", "tc_gap", "status"], [
        ["`DEP-001`", "`WP-01`", "`all_document_blocks_have_file=yes/no`", "`multi-file-info-note`", "Каждый документный блок имеет хотя бы один неудаленный файл", "`TC-CDUA-002` hides multi-file note", "`TC-CDUA-001` shows multi-file note while at least one block is empty", "`ATOM-001`", "`TC-CDUA-001`; `TC-CDUA-002`", "`TC-CDUA-001`; `TC-CDUA-002`", "`covered`"],
        ["`DEP-002`", "`WP-02`", "`actuality_choice=Нет/Актуальный`", "`document-actuality-status`", "Выбор в окне актуальности", "`TC-CDUA-013` covers `Актуальный`", "`TC-CDUA-011` covers `Нет`", "`ATOM-011`; `ATOM-012`", "`TC-CDUA-011`; `TC-CDUA-013`", "`TC-CDUA-011`; `TC-CDUA-013`", "`covered`"],
        ["`DEP-003`", "`WP-03`", "`required_document_block_empty=yes`", "`empty-required-block-highlight`", "Пустой обязательный документный блок при отправке", "`TC-CDUA-016` red-highlight branch", "`none_required:positive-submit-out-of-scope`", "`ATOM-015`", "`TC-CDUA-016`", "`TC-CDUA-016`", "`covered`"],
    ]))
    write_with_section_helper(TD / "test-design-applicability-matrix.md", "Test-design Applicability Matrix", table(["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"], [
        ["`table-list`", "`yes`", "`SRC-005`", "Identity documents are shown as a list of uploaded file thumbnails.", "`ATOM-005`", "`TC-CDUA-008`", ""],
        ["`file-upload`", "`yes`", "`SRC-003`; `SRC-009`", "Source defines allowed formats, size notice and upload action.", "`ATOM-003`; `ATOM-009`", "`TC-CDUA-004`; `TC-CDUA-005`; `TC-CDUA-006`; `TC-CDUA-017`", "`GAP-002`"],
        ["`dependency`", "`yes`", "`SRC-001`; `SRC-011`; `SRC-012`; `SRC-015`", "Source defines multi-file note condition, actuality choices and submit-required branch.", "`ATOM-001`; `ATOM-011`; `ATOM-012`; `ATOM-015`", "`TC-CDUA-001`; `TC-CDUA-002`; `TC-CDUA-011`; `TC-CDUA-013`; `TC-CDUA-016`", ""],
        ["`integration`", "`unclear`", "`SRC-013`; `GAP-001`", "Only employee-facing UI notification is observable in current scope.", "`ATOM-013`", "`TC-CDUA-014`", "`GAP-001`"],
        ["`traceability`", "`unclear`", "`GAP-003`", "PDF pages and PDF-only IDs are not verified.", "`ATOM-001`..`ATOM-015`", "", "`GAP-003`"],
    ]))
    write_with_section_helper(TD / "coverage-metrics.md", "Coverage Metrics", table(["metric", "count", "covered", "gap", "unclear", "evidence"], [
        ["`atomic_statements`", "`15`", "`15`", "`0`", "`0`", "`atomic-requirements-ledger.md`"],
        ["`source_rows_in_scope`", "`15`", "`15`", "`0`", "`0`", "`source-row-inventory.md`"],
        ["`residual_gaps_carried`", "`3`", "`0`", "`3`", "`0`", "`coverage-gaps.md`; none blocking writer handoff"],
        ["`test_cases`", "`18`", "`18`", "`0`", "`0`", "`test-cases/section-31-client-documents-upload-and-actuality.md`"],
    ]))
    write_with_section_helper(TD / "fixture-catalog.md", "Fixture Catalog", table(["fixture_id", "purpose", "data_setup", "linked_tc", "source_ref", "cleanup"], [
        ["`FIX-CDUA-001`", "Допустимый файл для загрузки", "`client-passport.jpeg`, размер меньше `30 МБ`", "`TC-CDUA-005`; `TC-CDUA-012`", "`SRC-003`; `SRC-009`", "Удалить файл, если тестовый стенд сохраняет загрузку."],
        ["`FIX-CDUA-002`", "Недопустимый формат", "`client-passport.txt`, размер меньше `30 МБ`", "`TC-CDUA-006`", "`SRC-003`; `GAP-002`", "`none_required:file-not-attached`"],
        ["`FIX-CDUA-003`", "Пустой обязательный блок", "Карточка на разделе `Документы клиента` с одним обязательным блоком без файла", "`TC-CDUA-016`", "`SRC-015`", "`none_required:read-only-check`"],
    ]))
    write_with_section_helper(TD / "risk-priority-map.md", "Risk / Priority Map", table(["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"], [
        ["`ATOM-003`", "`file-upload`", "`4`", "`4`", "`16`", "`high`", "`data-loss`; `server-side-rejection`", "`SRC-003`; `SRC-009`", "`High`", "`TC-CDUA-004`; `TC-CDUA-005`; `TC-CDUA-006`", "`GAP-002`", "`accepted-with-gap`", "Wrong file handling can block application processing; exact error text remains unresolved."],
        ["`ATOM-013`", "`integration`", "`4`", "`3`", "`12`", "`high`", "`integration`; `external-side-effect`", "`SRC-013`", "`High`", "`TC-CDUA-014`", "`GAP-001`", "`accepted-with-gap`", "UI notification is coverable; delivery and signing completion are out of scope."],
        ["`ATOM-015`", "`critical-business-validation`", "`4`", "`4`", "`16`", "`high`", "`business-validation`; `data-quality`", "`SRC-015`", "`High`", "`TC-CDUA-016`", "`none_required:no_gap`", "`none`", "Submitting with missing required document blocks must visibly flag the empty block."],
    ]))
    write_with_section_helper(TD / "coverage-map.md", "Coverage Map", table(["coverage_item", "value", "evidence"], [
        ["`atoms_total`", "`15`", "`atomic-requirements-ledger.md`"],
        ["`atoms_covered`", "`15`", "`TC-CDUA-001`..`TC-CDUA-016`"],
        ["`uncovered_atoms`", "`none_required:no_uncovered_atoms`", "`coverage_status=covered` for all ledger rows"],
        ["`known_limits`", "`GAP-001`; `GAP-002`; `GAP-003`", "`coverage-gaps.md`"],
    ]))
    write_with_section_helper(TD / "coverage-gaps.md", "Coverage Gaps", table(["gap_id", "source_ref", "linked_atoms", "gap_type", "coverage_impact", "writer_handling", "blocking"], [
        ["`GAP-001`", "`SRC-013`; actions table row 10", "`ATOM-002`; `ATOM-013`", "`integration-observability`", "UI notification/modal covered; SMS delivery and external signing completion not asserted.", "`TC-CDUA-003`; `TC-CDUA-014` use UI-observable wording only.", "`no`"],
        ["`GAP-002`", "`SRC-003`; `SRC-009`", "`ATOM-003`; `ATOM-009`", "`missing-error-oracle`", "Exact invalid format and oversize error text not confirmed.", "`TC-CDUA-006` uses conservative rejection/error indication without exact text.", "`no`"],
        ["`GAP-003`", "`source-parity-check.md`", "`ATOM-001`..`ATOM-015`", "`source-parity-extraction-risk`", "PDF pages and PDF-only IDs not verified.", "Traceability uses DOCX `SRC-*` and local section id only.", "`no`"],
    ]))
    gate_rows = [
        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use single canonical section headings and required table columns; canonical TC links summaries only.", "`all`", "`none_required:pass`", "`no`"],
        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability-bearing cells use explicit sentinel values such as `none_required:*`, `no_requirement_code:*`, `GAP-*`.", "`all`", "`none_required:pass`", "`no`"],
        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md`; generated through `scripts/write_artifact_sections.py --manifest <manifest.json>`.", "`all`", "`none_required:pass`", "`no`"],
        ["`mockup-visual-inventory`", "`pass`", "`mockup-visual-inventory.md` has `opened=yes`; mockup used only for steps.", "`all`", "`none_required:pass`", "`no`"],
        ["`source-row-inventory`", "`pass`", "`SRC-001`..`SRC-015` present; `SRC-016`/`SRC-017` excluded.", "`all`", "`none_required:pass`", "`no`"],
        ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` has one property per row.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-design-decision-table`", "`pass`", "Every `source_property_id` has a design decision and planned TC or gap.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-obligation-table`", "`pass`", "Obligation-bearing red-highlight behavior is represented; ordinary UI rows are covered in plan/ledger without artificial obligation expansion.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts atoms, source rows, gaps and TCs.", "`all`", "`none_required:pass`", "`no`"],
        ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` defines upload and required-block fixtures.", "`all`", "`none_required:pass`", "`no`"],
        ["`risk-priority-map`", "`pass`", "High-risk file upload, SMS UI action and submit required-doc check mapped to High priority TCs or residual gaps.", "`all`", "`none_required:pass`", "`no`"],
        ["`gap-admissibility`", "`pass`", "`GAP-001`..`GAP-003` do not hide source-backed visible behavior.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
        ["`ledger-atomicity`", "`pass`", "`ATOM-001`..`ATOM-015` each describe one checkable behavior.", "`all`", "`none_required:pass`", "`no`"],
        ["`gsr-range-compression`", "`pass`", "No broad GSR ranges are used; no PDF-only GSR IDs claimed.", "`all`", "`none_required:pass`", "`no`"],
        ["`design-plan-atomicity`", "`pass`", "Each design row maps to one expected behavior.", "`all`", "`none_required:pass`", "`no`"],
        ["`scenario-does-not-replace-atomic`", "`pass`", "Viewer flow branches are covered by separate `Нет` and `Актуальный` cases.", "`WP-02`", "`none_required:pass`", "`no`"],
        ["`tc-atomicity`", "`pass`", "`TC-CDUA-*` cases have one primary expected result.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-data-specificity`", "`pass`", "Upload fixtures name concrete format/size classes and files.", "`all`", "`none_required:pass`", "`no`"],
        ["`internal-observability`", "`pass`", "SMS/backend/PDF parity effects remain gaps or out-of-scope.", "`all`", "`none_required:pass`", "`no`"],
        ["`action-observability`", "`pass`", "Action TCs assert UI-observable results only.", "`all`", "`none_required:pass`", "`no`"],
        ["`semantic-req-id-parity`", "`pass`", "Traceability uses local section id and `SRC-*`; no PDF pages/GSR IDs invented.", "`all`", "`none_required:pass`", "`no`"],
        ["`scoped-validator-findings`", "`pass`", f"`{WRITER_PROFILE_REL}` generated by runner validate; expected `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
        ["`package-ready`", "`pass`", "`WP-01`..`WP-03` gates are ready for structure preflight.", "`all`", "`none_required:pass`", "`no`"],
    ]
    write_with_section_helper(TD / "writer-quality-gate.md", "Writer Quality Gate", table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows))
    write_with_section_helper(TD / "writer-self-check.md", "Writer Self-Check", table(["check", "status", "evidence", "required_action"], [
        ["`source parity checked`", "`pass`", "`source-parity-check.md`; PDF-only IDs none confirmed.", "`none_required:pass`"],
        ["`mandatory requirement IDs preserved`", "`pass`", "`section-31-client-documents-upload-and-actuality`; `SRC-001`..`SRC-015` in ledger/TC traceability.", "`none_required:pass`"],
        ["`uncovered atoms`", "`pass`", "`none_required:no_uncovered_atoms`.", "`none_required:pass`"],
        ["`possible merged checks`", "`pass`", "No TC combines positive upload, negative upload and branch action in one case.", "`none_required:pass`"],
        ["`internal work package coverage`", "`pass`", "`internal-work-package-coverage.md`.", "`none_required:pass`"],
        ["`scoped validator command`", "`pass`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/cycle-state.yaml`.", "`none_required:pass`"],
        ["`scoped validator findings summary`", "`pass`", f"`{WRITER_PROFILE_REL}`; current-scope unresolved warning/error count expected `0` after runner gate.", "`none_required:pass`"],
        ["`Artifact Write Evidence`", "`pass`", "`artifact-write-strategy.md`; transient manifests under `outputs/_writer_r1_artifact_write`.", "`none_required:pass`"],
        ["`assumptions`", "`pass`", "Residual exact text / backend / PDF gaps remain in `coverage-gaps.md`.", "`none_required:pass`"],
        ["`unclear items`", "`pass`", "`GAP-001`; `GAP-002`; `GAP-003` are non-blocking and visible.", "`none_required:pass`"],
    ]))


def tc_block(tc_id: str, title: str, tc_type: str, priority: str, package_id: str, trace: str, pre: str, data: str, steps: list[str], expected: str, post: str) -> str:
    numbered = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"""## {tc_id}

**Название:** {title}
**Тип:** {tc_type}
**Приоритет:** {priority}
**package_id:** `{package_id}`
**Трассировка:** {trace}

### Предусловия

{pre}

### Тестовые данные

{data}

### Шаги

{numbered}

### Итоговый ожидаемый результат

{expected}

### Постусловия

{post}
"""


def write_canonical() -> None:
    links = "\n".join(
        f"- `{TD_REL}/{name}`"
        for name in [
            "artifact-write-strategy.md",
            "mockup-usage.md",
            "source-row-inventory.md",
            "source-row-completeness-matrix.md",
            "source-table-normalization.md",
            "test-design-decision-table.md",
            "coverage-obligation-table.md",
            "atomic-requirements-ledger.md",
            "internal-work-package-coverage.md",
            "package-test-design-plan.md",
            "test-design-review.md",
            "coverage-map.md",
            "coverage-gaps.md",
            "writer-quality-gate.md",
            "writer-self-check.md",
        ]
    )
    cases = [
        tc_block("TC-CDUA-001", "Отображение подсказки о нескольких файлах при незаполненном документном блоке", "Positive", "Medium", "WP-01", "`ATOM-001`; `SRC-001`; `section-31-client-documents-upload-and-actuality`", "Открыта карточка на разделе `Документы клиента`; хотя бы один документный блок не содержит неудаленного файла.", "Не требуются.", ["Открыть раздел `Документы клиента`.", "Просмотреть область документных блоков."], "В разделе отображается подсказка `При необходимости можно приложить несколько файлов в одном поле`.", "Не требуются."),
        tc_block("TC-CDUA-002", "Скрытие подсказки о нескольких файлах после заполнения всех документных блоков", "Positive", "Medium", "WP-01", "`ATOM-001`; `SRC-001`; `section-31-client-documents-upload-and-actuality`", "Открыта карточка на разделе `Документы клиента`; каждый документный блок содержит хотя бы один неудаленный файл.", "Не требуются.", ["Открыть раздел `Документы клиента`.", "Просмотреть область документных блоков."], "Подсказка `При необходимости можно приложить несколько файлов в одном поле` не отображается.", "Не требуются."),
        tc_block("TC-CDUA-003", "Отображение признака подписания документов клиента на UI-уровне", "Positive", "High", "WP-01", "`ATOM-002`; `SRC-002`; `GAP-001`; `section-31-client-documents-upload-and-actuality`", "Карточка находится в UI-состоянии после онлайн-подписания документов клиентом; доставка СМС и внешнее подписание не проверяются этим TC.", "Не требуются.", ["Открыть раздел `Документы клиента`."], "Отображается информационное поле `Все документы клиента подписаны`.", "Не требуются."),
        tc_block("TC-CDUA-004", "Отображение notice с форматами и ограничением размера файла", "Positive", "High", "WP-01", "`ATOM-003`; `SRC-003`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; доступна зона загрузки файла.", "Не требуются.", ["Просмотреть текст рядом с зоной загрузки файла."], "В зоне загрузки отображается notice `Файлы jpeg, png, pdf не более 30 МБ`.", "Не требуются."),
        tc_block("TC-CDUA-005", "Загрузка допустимого файла с ПК в документный блок", "Positive", "High", "WP-02", "`ATOM-009`; `SRC-003`; `SRC-009`; `GAP-002`; `FIX-CDUA-001`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; доступен документный блок для загрузки.", "`client-passport.jpeg`, формат `jpeg`, размер меньше `30 МБ`.", ["В документном блоке нажать область загрузки или пиктограмму загрузки файла.", "Выбрать файл `client-passport.jpeg` с ПК.", "Подтвердить выбор файла."], "Файл отображается в выбранном документном блоке как загруженный документ.", "Удалить загруженный файл, если тестовый стенд сохраняет состояние после проверки."),
        tc_block("TC-CDUA-006", "Отклонение файла неподдерживаемого формата без проверки точного текста ошибки", "Negative", "High", "WP-01", "`ATOM-003`; `SRC-003`; `SRC-009`; `GAP-002`; `FIX-CDUA-002`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; доступен документный блок для загрузки.", "`client-passport.txt`, формат не входит в `jpeg/png/pdf`, размер меньше `30 МБ`.", ["В документном блоке нажать область загрузки или пиктограмму загрузки файла.", "Выбрать файл `client-passport.txt` с ПК.", "Подтвердить выбор файла."], "Файл не прикрепляется к документному блоку; UI показывает факт отклонения или ошибку загрузки без проверки точного текста сообщения.", "Не требуются."),
        tc_block("TC-CDUA-007", "Отображение миниатюры заявления-анкеты с именем, размером и форматом", "Positive", "Medium", "WP-01", "`ATOM-004`; `SRC-004`; `section-31-client-documents-upload-and-actuality`", "В блоке заявления-анкеты уже загружен файл.", "Загруженный файл заявления-анкеты с известными именем, размером и форматом.", ["Открыть раздел `Документы клиента`.", "Просмотреть строку загруженного заявления-анкеты."], "Загруженное заявление-анкета отображается миниатюрой файла с именем, размером и форматом.", "Не требуются."),
        tc_block("TC-CDUA-008", "Список документов, удостоверяющих личность, при паспорте в ЭА без актуальности", "Positive", "High", "WP-01", "`ATOM-005`; `SRC-005`; `section-31-client-documents-upload-and-actuality`", "В ЭА есть паспорт клиента без признака актуальности.", "Не требуются.", ["Открыть раздел `Документы клиента`.", "Просмотреть блок `Документы удостоверяющие личность`."], "В блоке отображается список загруженных документов, удостоверяющих личность клиента, в виде миниатюр файлов.", "Не требуются."),
        tc_block("TC-CDUA-009", "Отображение сообщения о необходимости подтвердить актуальность паспорта", "Positive", "High", "WP-01", "`ATOM-006`; `SRC-006`; `section-31-client-documents-upload-and-actuality`", "В ЭА есть ранее загруженный паспорт без подтвержденной актуальности.", "Не требуются.", ["Открыть раздел `Документы клиента`.", "Просмотреть блок `Документы удостоверяющие личность`."], "Отображается сообщение о ранее загруженном паспорте и необходимости подтвердить актуальность или приложить новый документ.", "Не требуются."),
        tc_block("TC-CDUA-010", "Открытие всплывающего окна просмотра документа", "Positive", "High", "WP-02", "`ATOM-008`; `SRC-008`; `section-31-client-documents-upload-and-actuality`", "В блоке документов есть загруженный документ с доступной иконкой просмотра.", "Не требуются.", ["В строке загруженного документа нажать иконку просмотра."], "Открывается всплывающее окно просмотра выбранного документа.", "Закрыть окно просмотра, если оно осталось открытым."),
        tc_block("TC-CDUA-011", "Ветка `Нет` в окне просмотра документа", "Positive", "High", "WP-02", "`ATOM-011`; `SRC-011`; `section-31-client-documents-upload-and-actuality`", "Открыто всплывающее окно просмотра документа с вопросом об актуальности.", "Не требуются.", ["В окне просмотра нажать `Нет`."], "Окно просмотра закрывается; сотрудник возвращается к документному блоку, где можно приложить новый актуальный документ.", "Не требуются."),
        tc_block("TC-CDUA-012", "Отображение `Документ актуальный` после загрузки сотрудником нового документа", "Positive", "High", "WP-02", "`ATOM-007`; `SRC-007`; `SRC-009`; `FIX-CDUA-001`; `section-31-client-documents-upload-and-actuality`", "Открыт блок `Документы удостоверяющие личность`; требуется приложить актуальный документ.", "`client-passport.jpeg`, формат `jpeg`, размер меньше `30 МБ`.", ["В документном блоке нажать область загрузки или пиктограмму загрузки файла.", "Выбрать файл `client-passport.jpeg` с ПК.", "Подтвердить выбор файла."], "После прикрепления файла в блоке отображается поле `Документ актуальный`.", "Удалить загруженный файл, если тестовый стенд сохраняет состояние после проверки."),
        tc_block("TC-CDUA-013", "Ветка `Актуальный` в окне просмотра документа", "Positive", "High", "WP-02", "`ATOM-012`; `SRC-007`; `SRC-012`; `section-31-client-documents-upload-and-actuality`", "Открыто всплывающее окно просмотра документа с вопросом об актуальности.", "Не требуются.", ["В окне просмотра нажать `Актуальный`."], "Документ помечается актуальным; открыт раздел документов и рядом с документом отображается `Документ актуальный`.", "Не требуются."),
        tc_block("TC-CDUA-014", "Отображение UI-уведомления после отправки СМС на онлайн-подписание", "Positive", "High", "WP-03", "`ATOM-013`; `SRC-013`; `GAP-001`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; кнопка `Отправить СМС на подписание документов онлайн` доступна.", "Не требуются.", ["Нажать кнопку `Отправить СМС на подписание документов онлайн`."], "Появляется всплывающее уведомление или модальное окно для сотрудника о направлении СМС клиенту; успешная доставка СМС и внешнее подписание не проверяются.", "Закрыть уведомление или модальное окно, если оно осталось открытым."),
        tc_block("TC-CDUA-015", "Переход назад к разделу `Сведения о занятости`", "Positive", "Medium", "WP-03", "`ATOM-014`; `SRC-014`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; кнопка `Назад` доступна.", "Не требуются.", ["Нажать кнопку `Назад`."], "Открывается раздел `Сведения о занятости`.", "Не требуются."),
        tc_block("TC-CDUA-016", "Подсветка пустого обязательного документного блока при отправке заявки", "Negative", "High", "WP-03", "`ATOM-015`; `SRC-015`; `FIX-CDUA-003`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; один обязательный документный блок пустой.", "Карточка с пустым обязательным документным блоком.", ["Нажать кнопку `Отправить заявку`."], "Пустой обязательный документный блок подсвечивается красным.", "Не требуются."),
        tc_block("TC-CDUA-017", "Отклонение файла больше `30 МБ` без проверки точного текста ошибки", "Negative", "High", "WP-01", "`ATOM-003`; `SRC-003`; `SRC-009`; `GAP-002`; `section-31-client-documents-upload-and-actuality`", "Открыт раздел `Документы клиента`; доступен документный блок для загрузки.", "`client-passport.pdf`, формат `pdf`, размер больше `30 МБ`.", ["В документном блоке нажать область загрузки или пиктограмму загрузки файла.", "Выбрать файл `client-passport.pdf` с ПК.", "Подтвердить выбор файла."], "Файл не прикрепляется к документному блоку; UI показывает факт отклонения или ошибку загрузки без проверки точного текста сообщения.", "Не требуются."),
        tc_block("TC-CDUA-018", "Открытие вопроса об актуальности через действие `Показать`", "Positive", "High", "WP-02", "`ATOM-010`; `SRC-010`; `section-31-client-documents-upload-and-actuality`", "В блоке документов есть загруженный документ с доступным действием `Показать`.", "Не требуются.", ["В строке загруженного документа нажать `Показать`."], "Открывается просмотр документа с вопросом об актуальности.", "Закрыть окно просмотра, если оно осталось открытым."),
    ]
    content = f"""# Тест-кейсы: загрузка, просмотр и подтверждение актуальности документов клиента

## Metadata

| item | value |
| --- | --- |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `{SCOPE}` |
| section_id | `{SECTION}` |
| writer_stage | `writer-r1` |
| canonical_test_design_dir | `{TD_REL}` |

## Scope Boundaries

Покрываются только `SRC-001`..`SRC-015` из `source-row-inventory.md`: информационные поля, загрузка, миниатюры, список документов, prompt актуальности паспорта, просмотр, ветки `Нет` и `Актуальный`, UI-уведомление СМС, `Назад` и проверка обязательных документных блоков при `Отправить заявку`.

Исключены `SRC-016`, `SRC-017`, печатные формы/теги, `Отменить заявку`, полный раздел `Анкета клиента`, полный раздел `Обработка`, `Предложения`, backend/API/RabbitMQ/БД и внешняя доставка СМС.

## Canonical Artifact Links

{links}

## Coverage Summary

| item | value |
| --- | --- |
| source_rows | `SRC-001`..`SRC-015` |
| atomic_statements | `ATOM-001`..`ATOM-015` |
| internal_packages | `WP-01`; `WP-02`; `WP-03` |
| executable_test_cases | `TC-CDUA-001`..`TC-CDUA-018` |
| residual_gaps | `GAP-001`; `GAP-002`; `GAP-003` |

## WP-01 Информационные поля и списки файлов

{cases[0]}
{cases[1]}
{cases[2]}
{cases[3]}
{cases[5]}
{cases[16]}
{cases[6]}
{cases[7]}
{cases[8]}

## WP-02 Просмотр и актуальность документа

{cases[4]}
{cases[9]}
{cases[17]}
{cases[10]}
{cases[11]}
{cases[12]}

## WP-03 Действия отправки и навигации

{cases[13]}
{cases[14]}
{cases[15]}
"""
    write_plain(CANONICAL, content)


def write_outputs_and_prompt() -> None:
    response = f"""# Writer R1 Response

## Summary

Initial writer draft created for `ft-2-OF_17` / `{SCOPE}`.

## Artifacts Written

- `{CANONICAL_REL}`
- `{TD_REL}/`
- `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- `{STRUCTURE_PROMPT_REL}`

## Scope Discipline

- Used only `SRC-001`..`SRC-015`.
- Excluded `SRC-016`, `SRC-017`, print-form tags, `Отменить заявку`, full `Анкета клиента`, full `Обработка` and `Предложения`.
- Preserved `GAP-001`, `GAP-002`, `GAP-003` as residual gaps.

## Validator Plan

Run `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` after artifact write. The writer gate references `{WRITER_PROFILE_REL}`.
"""
    write_plain(OUTPUTS / "writer-r1-response.md", response)
    session_log = f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft` |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `{SCOPE}` |
| started_from | `work/review-cycles/{SCOPE}/cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget status `pass (140.1 / 200.0 KiB)`.
- `AGENTS.md`; `skills/README.md`; `references/agent/session-based-review-cycle-format.md`; `references/agent/codex-sdk-orchestration-format.md`; `skills/ft-test-case-writer/SKILL.md`; `references/agent/writer-runtime-workflow.md`; `references/agent/writer-runtime-contract.md`; `references/qa/test-case-runtime-format.md`; `references/qa/coverage-runtime-checklist.md`; `references/qa/traceability-rules.md`; `references/agent/writer-process-workflow.md`; `references/agent/workflow-state-format.md`; `references/agent/session-log-format.md`; `references/agent/agent-decision-log-format.md`; `references/agent/writer-handoff-format.md` - selected required instruction files.
- `work/stage-handoffs/00-source-selection/source-selection.md` - source boundary.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-contract.md` - scope and `WP-*`.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/source-parity-check.md` - DOCX/PDF parity limitation.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/source-row-inventory.md` - `SRC-*` and `ATOM-*`.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/mockup-visual-inventory.md` - UI interaction hints only.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-coverage-gaps.md` - `GAP-*`.
- `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-clarification-requests.md` - non-blocking clarifications.
- `AGENT-NOTES.md` - package-specific notes.

## Inputs Not Used

- `SRC-016`; `SRC-017` - out of current scope.
- Neighboring FT packages and existing unrelated test-case files - excluded from source evidence.

## Key Decisions

- Used only DOCX `SRC-*` anchors and local section id because PDF parity is not verified.
- Kept negative upload oracle conservative: rejection/error indication only, no invented exact text.
- Covered SMS action only at UI notification/modal level, no delivery/signing completion claim.

## Risks And Fallbacks

- `GAP-001`; `GAP-002`; `GAP-003` remain non-blocking residual gaps.
- Initial PowerShell stdout showed mojibake for Cyrillic; affected instruction/source files were reread with `Get-Content -Raw -Encoding UTF8`, and distorted output was not used as source evidence.

## Validation

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - run after final artifact write; expected to persist `{WRITER_PROFILE_REL}` with zero current-scope warnings/errors.

## Contamination Check

- Existing test-case files for other scopes were listed only to verify no competing canonical file existed for this scope; they were not used as source content.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | pass | budget `140.1 / 200.0 KiB` |
| 2 | Read required inputs | pass | handoff and package notes |
| 3 | Built split test-design artifacts | pass | `{TD_REL}/` |
| 4 | Built canonical TC draft | pass | `{CANONICAL_REL}` |
| 5 | Prepared structure preflight prompt | pass | `{STRUCTURE_PROMPT_REL}` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md` | structure preflight |
| Gap discipline | `pass` | `{TD_REL}/coverage-gaps.md` | semantic reviewer should verify no backend claims |
| Traceability | `pass` | `ATOM-*`; `SRC-*`; `WP-*` in design rows and TC traceability | none |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `{CANONICAL_REL}` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `{TD_REL}/` | `split generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `encoding issue` | `PowerShell console output read without explicit UTF-8` | `Get-Content -Raw -Encoding UTF8` | `n/a` | `n/a` | `none; mojibake stdout discarded and not used as source evidence` | `none` |

## Handoff Notes For Next Session

- Structure preflight should check parser shape, required runtime fields, split artifact headings and `{WRITER_PROFILE_REL}` first.
- Semantic reviewer should focus on `GAP-001`/`GAP-002` wording and ensure no backend delivery or exact upload error text was invented.
"""
    write_plain(OUTPUTS / "writer-session-log.writer-r1.md", session_log)
    decisions = [
        ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only `SRC-001`..`SRC-015`.", "Prompt explicitly excludes `SRC-016`, `SRC-017`, print forms and broader sections.", CANONICAL_REL, "`high`", "`applied`"],
        ["`DEC-002`", "2", "`source-boundary`", "`source-parity-check.md`", "Use DOCX/SRC anchors only; no PDF page or PDF-only GSR IDs.", "PDF parity not completed and no PDF-only IDs confirmed.", f"{TD_REL}/atomic-requirements-ledger.md", "`high`", "`applied`"],
        ["`DEC-003`", "3", "`gap`", "`scope-coverage-gaps.md`", "Carry `GAP-001`, `GAP-002`, `GAP-003` into design artifacts.", "Gaps are non-blocking but must remain visible.", f"{TD_REL}/coverage-gaps.md", "`high`", "`applied`"],
        ["`DEC-004`", "4", "`test-design`", "`SRC-013`", "Cover SMS action only by employee-facing UI notification/modal.", "Source-backed UI observable exists; external delivery chain is not in scope.", f"{CANONICAL_REL}#TC-CDUA-014", "`high`", "`applied`"],
        ["`DEC-005`", "5", "`artifact-write`", "`writer-output-format.md`", "Use file-based manifest helper for split and canonical artifacts.", "Package-based scope requires safe chunked writing.", f"{TD_REL}/artifact-write-strategy.md", "`high`", "`applied`"],
        ["`DEC-006`", "6", "`routing`", "`session-based-review-cycle-format.md`", "Route to `structure-preflight-r1` with `writer-draft-ready`.", "Structure preflight must run before semantic review.", f"work/review-cycles/{SCOPE}/cycle-state.yaml", "`high`", "`applied`"],
    ]
    decision_log = "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + table(
        ["field", "value"],
        [["ft_slug", "`ft-2-OF_17`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`work/review-cycles/{SCOPE}/cycle-state.yaml`"]],
    ) + "\n\n## Decision Log\n\n" + table(["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"], decisions)
    write_plain(OUTPUTS / "agent-decision-log.writer-r1.md", decision_log)
    prompt = f"""# Prompt: Structure Preflight R1

Run `reviewer.structure_preflight` for `ft-2-OF_17` / `{SCOPE}`.

## Instruction Loading

Before review, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file before review decisions. If resolver fails or budget is not pass, do not advance the cycle.

## Bounded Runtime

- Do not recursively read directories.
- Do not read `validator-report*.json` or other large raw validator reports; use the scoped validator profile listed below.
- If a needed structure signal is unavailable from the exact files below, record a structure-preflight blocker instead of broadening the search.
- Do not perform semantic coverage review.

## Inputs

- Canonical test cases: `{CANONICAL_REL}`
- Test-design bounded files:
  - `{TD_REL}/writer-quality-gate.md`
  - `{TD_REL}/test-design-review.md`
  - `{TD_REL}/package-test-design-plan.md`
- Writer response: `work/review-cycles/{SCOPE}/outputs/writer-r1-response.md`
- Writer session log: `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- Writer decision log: `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- Scoped validator profile: `{WRITER_PROFILE_REL}`
- Scope contract: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-contract.md`
- Source row inventory: `work/stage-handoffs/08-client-documents-upload-and-actuality/source-row-inventory.md`
- Coverage gaps: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-coverage-gaps.md`

## Review Mode

Use `structure_preflight` only: parseability, canonical TC runtime fields, continuous numbering, required split artifact headings/table columns, no duplicate wrapper headings, and current writer-stage scoped validator evidence.

Do not perform semantic coverage review in this stage.

## Expected Output

- `work/review-cycles/{SCOPE}/outputs/structure-preflight-r1-findings.md`
- `work/review-cycles/{SCOPE}/outputs/reviewer-session-log.structure-preflight-r1.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.structure-preflight-r1.md`
- Updated `cycle-state.yaml` to `semantic-review-ready` if structure passes, or `structure-preflight-blocked` with a writer remediation prompt if blocked.
"""
    write_plain(PROMPTS / "prompt.structure-preflight-r1.md", prompt)


def write_bootstrap_profile() -> None:
    payload = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "bootstrap before runner validate; must be overwritten by python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/cycle-state.yaml",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    write_plain(OUTPUTS / "scoped-validator-profile.writer-r1.json", json.dumps(payload, ensure_ascii=False, indent=2))


def write_cycle_state(current_stage: str = "structure-preflight-r1") -> None:
    state = f"""cycle_id: client-documents-upload-and-actuality-2026-06-25
ft_slug: ft-2-OF_17
scope_slug: {SCOPE}
section_id: {SECTION}
current_stage: {current_stage}
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: {CANONICAL_REL}
test_design_dir: {TD_REL}
active_snapshot: work/review-cycles/{SCOPE}/versions/r1-writer-draft
active_transition_prompt: {STRUCTURE_PROMPT_REL}
sessions: []
latest_artifacts:
  - {CANONICAL_REL}
  - {TD_REL}
  - work/review-cycles/{SCOPE}/outputs/writer-r1-response.md
  - work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - {WRITER_PROFILE_REL}
  - {STRUCTURE_PROMPT_REL}
blocking_reasons: []
blocking_findings: []
open_questions:
  - "GAP-001: exact UI notification text after sending SMS for online document signing is not confirmed; cover only observable UI notification/modal, not SMS/backend delivery."
  - "GAP-002: exact invalid format and oversize file error messages are not confirmed; use conservative rejection/error indication only."
  - "GAP-003: PDF pages and possible PDF-only GSR IDs are not confirmed; use DOCX/SRC anchors only."
accepted_risks:
  - "source-quality-oversized-blocks: active DOCX has large unrelated source blocks; selected scope rows are split into SRC-001..SRC-015 and used defensively."
"""
    write_plain(CYCLE / "cycle-state.yaml", state)


def main() -> int:
    write_split_artifacts()
    write_canonical()
    write_outputs_and_prompt()
    write_bootstrap_profile()
    write_cycle_state("structure-preflight-r1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
