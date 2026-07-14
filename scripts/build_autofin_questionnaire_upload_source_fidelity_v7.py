"""Build the offline AutoFin V7 source-fidelity package inputs.

The builder intentionally creates no test-case draft and performs no live run.
Generated Markdown is assembled through the canonical section writer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
HANDOFF = FT / "work" / "stage-handoffs" / "56-questionnaire-upload-source-fidelity-v7"
DESIGN = HANDOFF / "compiler-inputs" / "questionnaire-upload-transfer-v7"
PREVIOUS = FT / "work" / "stage-handoffs" / "55-questionnaire-upload-transfer-v6"
SCOPE_SLUG = "questionnaire-upload-transfer-v7"
CYCLE_REL = "work/review-cycles/questionnaire-upload-transfer-v7-20260714"
PACKAGE_ID = "questionnaire-upload-transfer-v7-r1"
TARGET_REL = "test-cases/16-questionnaire-upload-transfer-v7.md"

SOURCE_HASHES = {
    "source/FT4AutoFinFinal.docx": "c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b",
    "source/FT4AutoFinFinal.xhtml": "cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66",
    "source/FT4AutoFinFinal.pdf": "8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58",
}
DISPLAY_LITERAL = (
    "Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку"
)
SIZE_LITERAL = "размер файла не более 40 МБ"
EXACT_ERROR = (
    "Документы не загружены. Проверьте соответствуют ли документы требованиям: "
    "формат jpg, png, pdf, размер не более 40 МБ"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def split_markdown(content: str) -> tuple[str, list[tuple[str, str]]]:
    lines = content.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("generated Markdown requires one H1 title")
    title = lines[0][2:].strip()
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_heading is None:
        sections.append(("Content", "\n".join(current_lines).strip()))
    else:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return title, sections


def write_markdown(path: Path, content: str) -> None:
    title, sections = split_markdown(content)
    helper_root = HANDOFF / "_artifact_write" / path.stem
    write_text(helper_root / "preamble.md", f"# {title}")
    manifest_sections: list[dict[str, object]] = []
    for index, (heading, body) in enumerate(sections, 1):
        content_file = helper_root / f"section-{index:02d}.md"
        write_text(content_file, body or "none_required")
        manifest_sections.append(
            {
                "level": 2,
                "heading": heading,
                "content_file": content_file.name,
            }
        )
    manifest = {
        "target_path": Path(os.path.relpath(path, helper_root)).as_posix(),
        "preamble_file": "preamble.md",
        "sections": manifest_sections,
    }
    manifest_path = helper_root / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    for dry_run in (True, False):
        command = [
            sys.executable,
            str(ROOT / "scripts" / "write_artifact_sections.py"),
            "--manifest",
            str(manifest_path),
        ]
        if dry_run:
            command.append("--dry-run")
        subprocess.run(command, cwd=ROOT, check=True)


def carry_forward(name: str, replacements: dict[str, str]) -> None:
    content = (PREVIOUS / name).read_text(encoding="utf-8")
    for old, new in replacements.items():
        content = content.replace(old, new)
    write_markdown(HANDOFF / name, content)


def verify_sources() -> None:
    for relative, expected in SOURCE_HASHES.items():
        actual = sha256(FT / relative)
        if actual != expected:
            raise RuntimeError(
                f"source drift for {relative}: expected={expected}, actual={actual}"
            )


def main() -> int:
    verify_sources()
    HANDOFF.mkdir(parents=True, exist_ok=True)
    DESIGN.mkdir(parents=True, exist_ok=True)

    carry_forward(
        "source-selection.md",
        {
            "V6 transfer-canary": "V7 source-fidelity package",
            "V6": "V7",
            "prepared transfer compilation": "source-fidelity compilation",
        },
    )
    carry_forward("source-parity-check.md", {"V6": "V7"})
    carry_forward(
        "source-row-inventory.md",
        {
            "V6": "V7",
            "Старый `work/test-design/14-application-card-documents-and-questionnaire-files` не является source evidence из-за Final/PreFinal drift.": (
                "V6 draft и production test cases не являются source evidence; inventory "
                "сохранен по текущему Final DOCX/XHTML/PDF."
            ),
        },
    )

    write_markdown(
        HANDOFF / "scope-contract.md",
        f"""# Scope Contract — Questionnaire Upload Transfer V7

## Контекст

- `ft_slug`: `AutoFin`
- `scope_slug`: `{SCOPE_SLUG}`
- внешний scope: текущий Final, `section-16`, блок `Документы по заявке`.
- внутренний package: информационный literal и desktop-загрузка файла `Анкета клиента`.
- режим: offline source-to-package fidelity; без writer/reviewer live и без изменения baseline.

## In Scope

| source_property_id | source statement | requirement code | planned outcome |
| --- | --- | --- | --- |
| `SRC-QUT-001.P01` | `{DISPLAY_LITERAL}` отображается всегда. | `BSR 206` | `TC-QUT-001`; literal fidelity binding |
| `SRC-QUT-001.P02` | Поле является информационным; `Р = Нет`. | `BSR 207` | `TC-QUT-002` |
| `SRC-QUT-002.P01` | Поле добавления файла отображается всегда. | `BSR 208` | `TC-QUT-003` |
| `SRC-QUT-002.P02` | Добавление через открытие проводника по кнопке. | `BSR 209` | `TC-QUT-004` |
| `SRC-QUT-002.P03` | После добавления отображается имя файла. | `BSR 211` | `TC-QUT-004` |
| `SRC-QUT-002.P04` | Добавление через Drag and Drop. | `BSR 209` | `TC-QUT-005` |
| `SRC-QUT-002.P05` | Допустимые форматы: jpg, png, pdf. | `BSR 210` | `TC-QUT-006` |
| `SRC-QUT-002.P06` | `{SIZE_LITERAL}`; exact byte convention не задана. | `BSR 210` | `GAP-QUT-001`; obligation сохранен |
| `SRC-QUT-002.P07` | Файл больше 40 МБ отклоняется с точным сообщением ФТ. | `BSR 210` | `TC-QUT-007`; source-unit-only fixture |
| `SRC-QUT-002.P08` | Недопустимый формат отклоняется с тем же точным сообщением ФТ. | `BSR 210` | `TC-QUT-008` |
| `SRC-QUT-002.P09` | В каждом типе документа остаётся не более одного файла. | `BSR 210` | `TC-QUT-009` |

## Out Of Scope

- QR/`Прикрепить с телефона` branch из `BSR 209`.
- cross-document-type вывод нескольких имен из `BSR 211`.
- сохранение в электронном архиве Банка из `BSR 212`.
- остальные типы документов, просмотр/удаление/скачивание, production baseline и UI stand.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-QUT-01` | literal + desktop file upload | `SRC-QUT-001; SRC-QUT-002` | `BSR 206-211`, кроме явно исключенных branches | explicit `ATOM -> OBL -> TC/GAP` + fidelity bindings | 11 obligations, 9 planned TC, 1 gap | `no` |

## Result Boundary

- все 11 V6 source obligations сохранены: 10 testable и 1 gap obligation;
- package compile допустим только после deterministic fidelity gate;
- `{TARGET_REL}` должен оставаться отсутствующим;
- V6 package/draft остаются immutable evidence и не изменяются.
""",
    )

    write_markdown(
        HANDOFF / "scope-coverage-gaps.md",
        f"""# Scope Coverage Gaps — Questionnaire Upload Transfer V7

## Контекст

- `scope_slug`: `{SCOPE_SLUG}`
- Основной FT: `source/FT4AutoFinFinal.docx`

## Summary

- Найдено gaps: `1`
- Blocking gaps: `0`
- Активный downstream: `ft-test-case-reviewer` для gap review.

## GAP-QUT-001

**FT Reference:** `BSR 210; SRC-QUT-002.P06; DOCX table 6 row 82; XHTML row 135; {SIZE_LITERAL}`

**Problem:** ФТ не определяет, означает ли `40 МБ` decimal `MB` или binary `MiB`; точный размер boundary fixture в байтах нельзя вывести без дополнительной policy.

**Impact:** `non-blocking`

**Handling:** Сохранить `ATOM-008` / `OBL-QUT-008` как отдельный gap; не создавать точный boundary TC и не преобразовывать величину в байты. Закрыть только по source-backed policy или подтвержденной fixture convention.

## Что Можно Покрывать Несмотря На Gap

- 10 остальных obligations, включая заведомо oversized fixture `50 МБ`, остаются testable.

## Что Нельзя Домысливать

- точное число байт для `40 МБ` и just-over boundary;
- UI-механизм реакции на второй файл сверх source-backed count `не более одного`.
""",
    )

    write_markdown(
        HANDOFF / "scope-clarification-requests.md",
        f"""# Scope Clarification Requests — Questionnaire Upload Transfer V7

## CR-QUT-001

| field | value |
| --- | --- |
| gap_id | `GAP-QUT-001` |
| source_statement | `BSR 210; {SIZE_LITERAL}` |
| question | Какая convention используется для граничной фикстуры: `1 МБ = 1 000 000 байт` или `1 МБ = 1 048 576 байт`? |
| acceptable_evidence | Уточнение владельца ФТ, опубликованная product policy или подтвержденный fixture contract. |
| default_without_answer | Не создавать exact-boundary TC; сохранить gap. |
| status | `open` |
""",
    )

    write_markdown(
        HANDOFF / "negative-oracle-inventory.md",
        f"""# Negative Oracle Inventory — Questionnaire Upload Transfer V7

## Контекст

- `scope_slug`: `{SCOPE_SLUG}`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-QUT-001` | `BSR 210; SRC-QUT-002.P07` | `Анкета клиента` | `other` | `oversize-file` | Файл больше 40 МБ не загружается. | валидный PDF размером `50 МБ`; он больше лимита при decimal и binary interpretation | `yes` | `FT` | `source-backed` | `executable_tc` | `TC-QUT-007` | `none_required:covered` | `none_required` | Создать один negative TC; не выдавать fixture за exact boundary convention. | `not_applicable` |
| `SO-NEG-QUT-002` | `BSR 210; SRC-QUT-002.P08` | `Анкета клиента` | `allowed-values` | `unsupported-format` | Допустимы только jpg, png, pdf. | `questionnaire-invalid.txt`, 1 КБ | `yes` | `FT` | `source-backed` | `executable_tc` | `TC-QUT-008` | `none_required:covered` | `none_required` | Создать один negative TC с точным source-backed сообщением. | `not_applicable` |

## Summary

- total_negative_obligations: `2`
- executable_tc: `2`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`
- exact positive boundary: `GAP-QUT-001`, не относится к negative inventory.

## Writer Handoff Rules

- Сохранить `SO-NEG-QUT-001` и `SO-NEG-QUT-002` до маппинга в соответствующие `ATOM-*` / `OBL-*`.
- Использовать точный oracle `{EXACT_ERROR}`.
- Не преобразовывать `40 МБ` в байты; `50 МБ` — заведомо oversized fixture, не product boundary.
""",
    )

    write_markdown(
        HANDOFF / "scope-execution-options.md",
        """# Scope Execution Options — Questionnaire Upload Transfer V7

## Recommended

- Сначала `ft-test-case-reviewer` проверяет `GAP-QUT-001` и fidelity bindings.
- После ответа по gap новая immutable revision может перейти в `ft-test-case-iteration`.

## Allowed Offline Now

- deterministic compile/validate-only;
- architecture and artifact audits;
- review source/design artifacts без создания draft.

## Forbidden Now

- writer/reviewer live invocation;
- ручное исправление V6 draft;
- promotion или запись production test cases;
- exact byte fixture без source-backed policy.
""",
    )

    ledger_rows = [
        (1, "SRC-QUT-001.P01", "BSR 206", f"Буквальный текст `{DISPLAY_LITERAL}` отображается всегда.", "visibility", "covered", "TC-QUT-001"),
        (2, "SRC-QUT-001.P02", "BSR 207", "Информационное поле не допускает ручного редактирования своего текста.", "field-property", "covered", "TC-QUT-002"),
        (3, "SRC-QUT-002.P01", "BSR 208", "Поле добавления файла `Анкета клиента` отображается всегда.", "visibility", "covered", "TC-QUT-003"),
        (4, "SRC-QUT-002.P02", "BSR 209", "Документ можно добавить через открытие проводника по кнопке.", "file-upload", "covered", "TC-QUT-004"),
        (5, "SRC-QUT-002.P03", "BSR 211", "После добавления документа отображается имя прикреплённого файла.", "file-upload-result", "covered", "TC-QUT-004"),
        (6, "SRC-QUT-002.P04", "BSR 209", "Документ можно добавить через Drag and Drop.", "file-upload", "covered", "TC-QUT-005"),
        (7, "SRC-QUT-002.P05", "BSR 210", "Поле принимает файлы форматов jpg, png и pdf.", "equivalence", "covered", "TC-QUT-006"),
        (8, "SRC-QUT-002.P06", "BSR 210; GAP-QUT-001", f"Точное граничное значение для `{SIZE_LITERAL}` нельзя задать без byte convention.", "boundary", "gap", "GAP-QUT-001"),
        (9, "SRC-QUT-002.P07", "BSR 210", f"Ограничение `{SIZE_LITERAL}`: файл размером 50 МБ не загружается и отображается точный текст ошибки.", "negative-oracle", "covered", "TC-QUT-007"),
        (10, "SRC-QUT-002.P08", "BSR 210", "Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ.", "negative-oracle", "covered", "TC-QUT-008"),
        (11, "SRC-QUT-002.P09", "BSR 210", "После попытки добавить второй файл в типе документа остаётся не более одного файла.", "file-cardinality", "covered", "TC-QUT-009"),
    ]
    ledger = [
        "# Atomic Requirements Ledger — Questionnaire Upload Transfer V7",
        "",
        "## Ledger",
        "",
        "| atom_id | package_id | source_property_id | source_ref | atomic_statement | property_type | coverage_status | covered_by_tc | planned_tc_or_gap | gap_id |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for number, property_id, source_ref, statement, prop_type, status, planned in ledger_rows:
        gap_id = "GAP-QUT-001" if status == "gap" else "none_required:covered"
        ledger.append(
            f"| `ATOM-{number:03d}` | `WP-QUT-01` | `{property_id}` | `{source_ref}` | {statement} | `{prop_type}` | `{status}` | `{planned}` | `{planned}` | `{gap_id}` |"
        )
    write_markdown(DESIGN / "atomic-requirements-ledger.md", "\n".join(ledger))

    obligation_rows = [
        (1, "SRC-QUT-001.P01", 1, "field-property", "field-visible", f"Буквальный текст `{DISPLAY_LITERAL}` отображается всегда.", "SRC-QUT-001; BSR 206", "TC-QUT-001", "covered", "Literal обязан дойти до oracle без generic compression."),
        (2, "SRC-QUT-001.P02", 2, "field-property", "informational-read-only", "Текст информационного поля нельзя изменить ручным вводом.", "SRC-QUT-001; BSR 207", "TC-QUT-002", "covered", "BSR 207 и Р=Нет."),
        (3, "SRC-QUT-002.P01", 3, "field-property", "field-visible", "Поле добавления файла `Анкета клиента` отображается всегда.", "SRC-QUT-002; BSR 208", "TC-QUT-003", "covered", "Прямая visibility obligation."),
        (4, "SRC-QUT-002.P02", 4, "file-upload", "picker-upload", "После выбора portable jpg через проводник файл добавлен.", "SRC-QUT-002; BSR 209", "TC-QUT-004", "covered", "Сгруппировано с OBL-QUT-005 одним result."),
        (5, "SRC-QUT-002.P03", 5, "file-upload", "filename-visible", "После добавления отображается точное имя выбранного файла.", "SRC-QUT-002; BSR 211", "TC-QUT-004", "covered", "Один observable upload result."),
        (6, "SRC-QUT-002.P04", 6, "file-upload", "drag-drop-upload", "После Drag and Drop portable pdf файл добавлен и его имя отображается.", "SRC-QUT-002; BSR 209; BSR 211", "TC-QUT-005", "covered", "Отдельный способ действия."),
        (7, "SRC-QUT-002.P05", 7, "equivalence", "allowed-file-formats", "В отдельных чистых итерациях jpg, png и pdf добавляются успешно.", "SRC-QUT-002; BSR 210", "TC-QUT-006", "covered", "Полный фиксированный перечень."),
        (8, "SRC-QUT-002.P06", 8, "input-boundaries", "max-file-size", f"Точное граничное значение для `{SIZE_LITERAL}` нельзя задать без byte convention.", "SRC-QUT-002; BSR 210; GAP-QUT-001", "GAP-QUT-001", "gap", "Обязательство сохранено, exact boundary не выдуман."),
        (9, "SRC-QUT-002.P07", 9, "negative-oracle", "oversize-file", f"Ограничение `{SIZE_LITERAL}`: файл размером 50 МБ не добавляется; отображается `{EXACT_ERROR}`.", "SRC-QUT-002; BSR 210", "TC-QUT-007", "covered", "50 МБ заведомо больше обеих 40 МБ conventions."),
        (10, "SRC-QUT-002.P08", 10, "negative-oracle", "unsupported-format", f"Файл txt не добавляется; отображается `{EXACT_ERROR}`.", "SRC-QUT-002; BSR 210", "TC-QUT-008", "covered", "Точный source-backed oracle."),
        (11, "SRC-QUT-002.P09", 11, "file-upload", "one-file-per-type", "После попытки добавить второй файл отображается не более одного имени файла этого типа.", "SRC-QUT-002; BSR 210", "TC-QUT-009", "covered", "Не утверждается replace/reject/message."),
    ]
    obligations = [
        "# Coverage Obligation Table — Questionnaire Upload Transfer V7",
        "",
        "## Obligations",
        "",
        "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in obligation_rows:
        number, property_id, atom, prop_type, obligation_class, behavior, source_ref, planned, status, notes = row
        obligations.append(
            f"| `OBL-QUT-{number:03d}` | `WP-QUT-01` | `{property_id}` | `ATOM-{atom:03d}` | `{prop_type}` | `{obligation_class}` | {behavior} | `{source_ref}` | `{planned}` | `{status}` | {notes} |"
        )
    write_markdown(DESIGN / "coverage-obligation-table.md", "\n".join(obligations))

    write_markdown(
        DESIGN / "package-test-design-plan.md",
        f"""# Package Test Design Plan — Questionnaire Upload Transfer V7

## Portable Fixture Contracts

- `FIXTURE-QUT-JPG`: валидный JPEG `questionnaire-valid.jpg`, 1 КБ.
- `FIXTURE-QUT-PNG`: валидный PNG `questionnaire-valid.png`, 1 КБ.
- `FIXTURE-QUT-PDF`: валидный PDF `questionnaire-valid.pdf`, 1 КБ.
- `FIXTURE-QUT-PDF-OVER40`: валидный PDF `questionnaire-over40mb.pdf`, размер 50 МБ; fixture заведомо больше лимита при decimal и binary interpretation.
- `FIXTURE-QUT-TXT`: текстовый `questionnaire-invalid.txt`, 1 КБ.
- `FIXTURE-QUT-PDF-A`: валидный PDF `questionnaire-first.pdf`, 1 КБ.
- `FIXTURE-QUT-PDF-B`: валидный PDF `questionnaire-second.pdf`, 1 КБ, другое имя и содержимое.

## Plan

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | test_data | single_expected_behavior | oracle_source | planned_tc_or_gap | status | grouping_justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-QUT-001` | `WP-QUT-01` | `visibility` | `SRC-QUT-001; BSR 206` | `ATOM-001` | Открыть блок `Документы по заявке`. | `positive` | `visibility` | `field-state` | `none_required` | Буквальный текст `{DISPLAY_LITERAL}` отображается всегда. | `DOCX/XHTML/PDF exact literal` | `TC-QUT-001` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-002` | `WP-QUT-01` | `field-property` | `SRC-QUT-001; BSR 207` | `ATOM-002` | Установить фокус на информационном поле и попытаться ввести `Тест`. | `positive` | `read-only` | `text:Тест` | `Тест` | Текст информационного поля не изменяется. | `DOCX/XHTML/PDF; Р=Нет` | `TC-QUT-002` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-003` | `WP-QUT-01` | `visibility` | `SRC-QUT-002; BSR 208` | `ATOM-003` | Открыть блок `Документы по заявке`. | `positive` | `visibility` | `field-state` | `none_required` | Поле добавления файла `Анкета клиента` отображается. | `DOCX/XHTML/PDF` | `TC-QUT-003` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-004` | `WP-QUT-01` | `file-upload` | `SRC-QUT-002; BSR 209; BSR 211` | `ATOM-004; ATOM-005` | По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`. | `positive` | `picker-upload` | `file:FIXTURE-QUT-JPG` | `FIXTURE-QUT-JPG` | Файл добавлен, отображается имя `questionnaire-valid.jpg`. | `DOCX/XHTML/PDF` | `TC-QUT-004` | `covered` | `grouping-justification:` способ и имя образуют один upload result. |
| `PLAN-QUT-005` | `WP-QUT-01` | `file-upload` | `SRC-QUT-002; BSR 209; BSR 211` | `ATOM-006` | Перетащить `FIXTURE-QUT-PDF` в поле `Анкета клиента`. | `positive` | `drag-drop-upload` | `file:FIXTURE-QUT-PDF` | `FIXTURE-QUT-PDF` | Файл добавлен, отображается имя `questionnaire-valid.pdf`. | `DOCX/XHTML/PDF` | `TC-QUT-005` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-006` | `WP-QUT-01` | `equivalence` | `SRC-QUT-002; BSR 210` | `ATOM-007` | В трёх чистых итерациях добавить `FIXTURE-QUT-JPG`, `FIXTURE-QUT-PNG`, `FIXTURE-QUT-PDF`. | `positive` | `allowed-formats` | `files:three-formats` | `FIXTURE-QUT-JPG; FIXTURE-QUT-PNG; FIXTURE-QUT-PDF` | В каждой итерации выбранный файл добавляется. | `DOCX/XHTML/PDF` | `TC-QUT-006` | `covered` | `none_required:one-fixed-value-set` |
| `PLAN-QUT-007` | `WP-QUT-01` | `boundary` | `SRC-QUT-002; BSR 210; GAP-QUT-001` | `ATOM-008` | Не создавать exact-boundary TC до уточнения byte convention. | `gap` | `max-file-size` | `none_required` | `none_required` | Точное граничное значение для `{SIZE_LITERAL}` нельзя задать без byte convention. | `GAP-QUT-001` | `GAP-QUT-001` | `gap` | `none_required:single-atom-gap` |
| `PLAN-QUT-008` | `WP-QUT-01` | `negative-oracle` | `SRC-QUT-002; BSR 210` | `ATOM-009` | Добавить `FIXTURE-QUT-PDF-OVER40`. | `negative-boundary` | `oversize-file` | `file:over-max` | `FIXTURE-QUT-PDF-OVER40` | Ограничение `{SIZE_LITERAL}`: файл размером 50 МБ не добавляется; отображается `{EXACT_ERROR}`. | `DOCX/XHTML/PDF exact text` | `TC-QUT-007` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-009` | `WP-QUT-01` | `negative-oracle` | `SRC-QUT-002; BSR 210` | `ATOM-010` | Добавить `FIXTURE-QUT-TXT`. | `negative-equivalence` | `unsupported-format` | `file:txt` | `FIXTURE-QUT-TXT` | Файл не добавляется; отображается `{EXACT_ERROR}`. | `DOCX/XHTML/PDF exact text` | `TC-QUT-008` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-010` | `WP-QUT-01` | `file-cardinality` | `SRC-QUT-002; BSR 210` | `ATOM-011` | Добавить `FIXTURE-QUT-PDF-A`, затем попытаться добавить `FIXTURE-QUT-PDF-B`. | `boundary` | `one-file-per-type` | `files:two-distinct` | `FIXTURE-QUT-PDF-A; FIXTURE-QUT-PDF-B` | После второго действия отображается не более одного имени файла; replace/reject/message не утверждаются. | `DOCX/XHTML/PDF count rule` | `TC-QUT-009` | `covered` | `none_required:single-atom` |
""",
    )

    write_markdown(
        DESIGN / "test-design-applicability-matrix.md",
        """# Test-Design Applicability Matrix — Questionnaire Upload Transfer V7

## Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| file-upload | `yes` | `BSR 209-211` | Picker, Drag and Drop, file name and cardinality. | `ATOM-004..ATOM-011` | `TC-QUT-004..TC-QUT-009` | `GAP-QUT-001` |
| input-boundaries | `yes` | `BSR 210` | Max 40 МБ; exact byte convention unresolved. | `ATOM-008; ATOM-009` | `TC-QUT-007` | `GAP-QUT-001` |
| negative-oracle | `yes` | `BSR 210` | Exact shared error text is source-backed. | `ATOM-009; ATOM-010` | `TC-QUT-007; TC-QUT-008` | `none_required:covered` |
| equivalence | `yes` | `BSR 210` | Полный список jpg/png/pdf плюс txt invalid class. | `ATOM-007; ATOM-010` | `TC-QUT-006; TC-QUT-008` | `none_required:covered` |
| visibility | `yes` | `BSR 206; BSR 208` | Два independent always-visible properties. | `ATOM-001; ATOM-003` | `TC-QUT-001; TC-QUT-003` | `none_required:covered` |
| persistence | `no` | `BSR 212` | Вне внутреннего package. | `none_required` | `none_required` | `none_required:out-of-scope` |
| integration | `no` | `BSR 209 QR branch` | Вне внутреннего package. | `none_required` | `none_required` | `none_required:out-of-scope` |
""",
    )

    fidelity = {
        "version": 1,
        "scope_slug": SCOPE_SLUG,
        "bindings": [
            {
                "binding_id": "FID-QUT-001",
                "binding_kind": "literal",
                "source_ref": "BSR 206; DOCX table 6 row 81; XHTML row 134",
                "source_text": DISPLAY_LITERAL,
                "atom_id": "ATOM-001",
                "obligation_id": "OBL-QUT-001",
                "handling": "preserve",
                "required_targets": [
                    "atomic_statement",
                    "required_behavior",
                    "single_expected_behavior",
                ],
            },
            {
                "binding_id": "FID-QUT-002",
                "binding_kind": "unit",
                "source_ref": "BSR 210; DOCX table 6 row 82; XHTML row 135",
                "source_text": SIZE_LITERAL,
                "atom_id": "ATOM-008",
                "obligation_id": "OBL-QUT-008",
                "handling": "coverage-gap",
                "required_targets": [
                    "atomic_statement",
                    "required_behavior",
                    "single_expected_behavior",
                ],
                "unit_value": 40,
                "unit_symbol": "МБ",
                "gap_id": "GAP-QUT-001",
                "decision_reason": "Final FT does not define decimal or binary byte convention.",
            },
            {
                "binding_id": "FID-QUT-003",
                "binding_kind": "unit",
                "source_ref": "BSR 210; DOCX table 6 row 82; XHTML row 135",
                "source_text": SIZE_LITERAL,
                "atom_id": "ATOM-009",
                "obligation_id": "OBL-QUT-009",
                "handling": "source-unit-only",
                "required_targets": [
                    "atomic_statement",
                    "required_behavior",
                    "single_expected_behavior",
                ],
                "unit_value": 40,
                "unit_symbol": "МБ",
                "decision_reason": "50 МБ fixture is unambiguously over the limit under both conventions.",
            },
        ],
    }
    write_text(
        DESIGN / "source-to-package-fidelity.json",
        json.dumps(fidelity, ensure_ascii=False, indent=2),
    )

    write_text(
        HANDOFF / "prompt.scope-gaps-to-reviewer.md",
        f"""# Prompt: Questionnaire Upload Source-Fidelity Gap Review V7

## Цель этапа

В режиме `scope_gap_review` проверить `GAP-QUT-001` и три fidelity bindings до любого writer/live этапа.

## Входные артефакты

- `../../../AGENT-NOTES.md`
- `workflow-state.yaml`
- `source-selection.md`
- `scope-contract.md`
- `source-parity-check.md`
- `source-row-inventory.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `negative-oracle-inventory.md`
- `compiler-inputs/{SCOPE_SLUG}/source-to-package-fidelity.json`

## Обязательные действия

1. Подтвердить, что literal BSR 206 сохранен в atom/obligation/plan.
2. Подтвердить, что exact boundary BSR 210 не превращен в байты и остается `GAP-QUT-001`.
3. Проверить, что oversized `50 МБ` testable при обеих conventions и не выдается за product boundary.
4. Проверить сохранение 11 obligations и отсутствие draft/baseline изменений.
5. При успешном gap review подготовить `prompt.scope-to-writer.md`; при ошибке вернуть scope analyzer или установить `blocked-input`.

## Не делать

- Не писать, не переписывать и не review-ить test cases в режиме `scope_gap_review`.
- Не запускать writer/reviewer live.
- Не менять V6 package/draft и production baseline.
- Не закрывать gap догадкой.

## Ожидаемые выходы

- `scope-gap-review.md` с verdict по anchors, classification, clarification requests и routing readiness.
- Решение: оставить gap open либо закрыть только полученным source-backed ответом.

## Gate завершения

При отсутствии policy оставить workflow `ready-for-gap-review`; failed review возвращается в `ft-scope-analyzer` или `blocked-input`; live остается запрещен.
""",
    )

    write_text(
        HANDOFF / "prompt.v7-to-next.md",
        """# Prompt: Continue Questionnaire Upload V7

## Intent

Продолжить только после независимого review source-fidelity gate.

## Required Inputs

- активный `workflow-state.yaml` H56;
- `scope-coverage-gaps.md` и `scope-clarification-requests.md`;
- immutable prepared package V7 и offline validation report.

## Required Actions

Если `GAP-QUT-001` остается open, выполнить только gap review. Если получена source-backed convention, создать новую immutable revision, обновить binding policy и заново скомпилировать package.

## Forbidden Actions

Не запускать live и не менять baseline без отдельного нового authorization.

## Expected Output

Проверяемое reviewer decision и следующий numbered handoff.

## Stop Conditions

Любая попытка вывести byte convention из `МБ` без source-backed policy блокирует продолжение.
""",
    )

    required = [
        "AGENT-NOTES.md",
        "work/stage-handoffs/55-questionnaire-upload-transfer-v6/post-canary-source-package-audit.v6.md",
        "work/stage-handoffs/55-questionnaire-upload-transfer-v6/prompt.v6-to-next.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-selection.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-contract.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-parity-check.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-row-inventory.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-coverage-gaps.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-clarification-requests.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/negative-oracle-inventory.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-execution-options.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/agent-decision-log.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-analyzer-session-log.md",
        "work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/prompt.scope-gaps-to-reviewer.md",
        f"work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/atomic-requirements-ledger.md",
        f"work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/coverage-obligation-table.md",
        f"work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/package-test-design-plan.md",
        f"work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/test-design-applicability-matrix.md",
        f"work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/source-to-package-fidelity.json",
    ]
    prepared_package = FT / CYCLE_REL / "prepared-input" / PACKAGE_ID / "stage-package.json"
    prepared_latest_yaml = ""
    if prepared_package.is_file():
        prepared_relative = prepared_package.relative_to(FT).as_posix()
        required.append(prepared_relative)
        prepared_latest_yaml = f"  prepared_package: {prepared_relative}\n"
    required_yaml = "\n".join(f"  - {item}" for item in required)
    write_text(
        HANDOFF / "workflow-state.yaml",
        f"""ft_slug: AutoFin
prepared_compiler_contract_version: 2
scope_slug: {SCOPE_SLUG}
current_stage: ft-scope-analyzer
stage_status: ready-for-gap-review
current_round: 1
next_skill: ft-test-case-reviewer
canonical_test_cases: {TARGET_REL}
required_inputs:
{required_yaml}
latest_artifacts:
  source_selection: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-selection.md
  scope_contract: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-contract.md
  source_parity_check: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-parity-check.md
  source_row_inventory: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/source-row-inventory.md
  scope_coverage_gaps: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-coverage-gaps.md
  coverage_gaps: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-coverage-gaps.md
  scope_clarification_requests: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-clarification-requests.md
  negative_oracle_inventory: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/negative-oracle-inventory.md
  scope_execution_options: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-execution-options.md
  atomic_requirements_ledger: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/atomic-requirements-ledger.md
  coverage_obligation_table: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/coverage-obligation-table.md
  package_test_design_plan: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/package-test-design-plan.md
  test_design_applicability_matrix: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/test-design-applicability-matrix.md
  source_to_package_fidelity: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/compiler-inputs/{SCOPE_SLUG}/source-to-package-fidelity.json
{prepared_latest_yaml.rstrip()}
  active_transition_prompt: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/prompt.scope-gaps-to-reviewer.md
  alternative_transition_prompt: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/prompt.v7-to-next.md
  decision_log: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/agent-decision-log.md
  scope_analyzer_session_log: work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-analyzer-session-log.md
coverage_gaps:
  blocking: 0
  non_blocking: 1
open_questions:
  - BSR 210 не определяет decimal или binary byte convention для 40 МБ.
blocking_reasons: []
accepted_risks:
  - V7 gate covers named literal and unit risks, not general semantic equivalence.
  - Exact 40 МБ boundary remains uncovered until GAP-QUT-001 is resolved.
  - No live run, draft generation or production promotion is authorized.
""",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
