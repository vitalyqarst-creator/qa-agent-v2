"""Build the immutable offline inputs for the AutoFin V6 transfer canary."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
HANDOFF = FT / "work" / "stage-handoffs" / "55-questionnaire-upload-transfer-v6"
DESIGN = HANDOFF / "compiler-inputs" / "questionnaire-upload-transfer-v6"
V5_CYCLE = (
    FT
    / "work"
    / "review-cycles"
    / "visual-assessment-medium-scope-benchmark-v5-20260714"
)
CYCLE_REL = "fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v6-20260714"
PACKAGE_ID = "questionnaire-upload-transfer-v6-r1"
TARGET_REL = "fts/AutoFin/test-cases/16-questionnaire-upload-transfer-v6.md"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    canonical = content.replace("ATOM-QUT-", "ATOM-")
    path.write_text(canonical.rstrip() + "\n", encoding="utf-8")


def write_source_row_inventory(path: Path, content: str) -> None:
    if path != HANDOFF / "source-row-inventory.md":
        raise ValueError(f"unexpected source-row inventory target: {path}")
    canonical = content.replace("ATOM-QUT-", "ATOM-").rstrip() + "\n"
    marker = "\n\n## Source Row Inventory\n\n"
    preamble, section_content = canonical.split(marker, 1)
    helper_root = HANDOFF / "_artifact_write" / "source-row-inventory"
    write(helper_root / "preamble.md", preamble)
    write(helper_root / "section.md", section_content)
    manifest = {
        "target_path": "../../source-row-inventory.md",
        "preamble_file": "preamble.md",
        "sections": [
            {
                "level": 2,
                "heading": "Source Row Inventory",
                "content_file": "section.md",
            }
        ],
    }
    write(
        helper_root / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "write_artifact_sections.py"),
            "--manifest",
            str(helper_root / "manifest.json"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def byte_slice(text: str, start: str, end: str | None) -> int:
    start_at = text.index(start)
    end_at = text.index(end, start_at) if end is not None else len(text)
    return len(text[start_at:end_at].encode("utf-8"))


def dadata_block_bytes(text: str) -> int:
    heading = re.search(r"(?mi)^##\s+[^\r\n]*dadata[^\r\n]*\r?$", text)
    if heading is None:
        return 0
    boundary = re.search(
        r"(?m)^(?:##\s+|- OBL-[A-Za-z0-9_.-]+:)",
        text[heading.end() :],
    )
    end = heading.end() + boundary.start() if boundary is not None else len(text)
    return len(text[heading.start() : end].encode("utf-8"))


def context_decomposition() -> dict[str, object]:
    writer = (
        V5_CYCLE / "attempts/writer-r1/attempt-001/prompt.md"
    ).read_text(encoding="utf-8")
    reviewer = (
        V5_CYCLE / "attempts/reviewer-r1/attempt-001/prompt.md"
    ).read_text(encoding="utf-8")
    performance = json.loads((V5_CYCLE / "performance.v5.json").read_text(encoding="utf-8"))
    replacement_bytes = len(
        "<!-- DaData package notes: not applicable to selected scope. -->\n\n".encode(
            "utf-8"
        )
    )
    writer_dadata = dadata_block_bytes(writer)
    reviewer_dadata = dadata_block_bytes(reviewer)
    writer_sections = {
        "outer_contract": len(
            writer[: writer.index("<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->")].encode(
                "utf-8"
            )
        ),
        "metadata_profile_rule_card": byte_slice(
            writer,
            "<!-- PREPARED-STAGE-PAYLOAD:BEGIN -->",
            "# Prepared Source Evidence",
        ),
        "source_evidence": byte_slice(
            writer, "# Prepared Source Evidence", "## Verified obligation transport"
        ),
        "obligation_transport": byte_slice(
            writer, "## Verified obligation transport", "## Draft seed template"
        ),
        "draft_seed_and_final_contract": byte_slice(
            writer, "## Draft seed template", None
        ),
    }
    reviewer_sections = {
        "outer_contract": len(
            reviewer[: reviewer.index("<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->")].encode(
                "utf-8"
            )
        ),
        "metadata_profile_rule_card": byte_slice(
            reviewer,
            "<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->",
            "## Selected source evidence",
        ),
        "shared_source_evidence": byte_slice(
            reviewer,
            "## Selected source evidence",
            "## Verified obligation review index",
        ),
        "semantic_obligation_projection": byte_slice(
            reviewer,
            "## Verified obligation review index",
            "## Deterministic gate summaries",
        ),
        "gate_and_calibration_summaries": byte_slice(
            reviewer,
            "## Deterministic gate summaries",
            "## Immutable writer draft",
        ),
        "immutable_draft": byte_slice(
            reviewer, "## Immutable writer draft", "## Required final contract"
        ),
        "final_contract": byte_slice(reviewer, "## Required final contract", None),
    }
    return {
        "schema": "prepared-context-decomposition-v6",
        "source_cycle": V5_CYCLE.relative_to(ROOT).as_posix(),
        "v5_uncached_input_tokens": performance["uncached_input_tokens_total"],
        "writer": {
            "prompt_bytes": len(writer.encode("utf-8")),
            "sections": writer_sections,
            "irrelevant_dadata_bytes": writer_dadata,
            "projected_prompt_bytes": len(writer.encode("utf-8"))
            - writer_dadata
            + replacement_bytes,
        },
        "reviewer": {
            "prompt_bytes": len(reviewer.encode("utf-8")),
            "sections": reviewer_sections,
            "irrelevant_dadata_bytes": reviewer_dadata,
            "projected_prompt_bytes": len(reviewer.encode("utf-8"))
            - reviewer_dadata
            + replacement_bytes,
        },
        "proven_removal": {
            "kind": "scope-irrelevant-package-note-section",
            "section": "DaData",
            "bytes_removed_before_replacement": writer_dadata + reviewer_dadata,
            "replacement_bytes_total": replacement_bytes * 2,
            "net_prompt_bytes_removed": writer_dadata
            + reviewer_dadata
            - replacement_bytes * 2,
            "guard": "retain-full-section-when-selected-evidence-outside-note-references-dadata",
        },
        "not_reduced": [
            "source-backed obligation semantics",
            "observable oracles",
            "portable fixture contracts",
            "immutable writer draft supplied to independent reviewer",
            "role runtime profiles required in separate exec sessions",
        ],
        "interpretation_limit": (
            "Prompt bytes are exact; backend bootstrap/system tokens are not section-attributed "
            "by the exec event stream, so the full uncached-token delta cannot be assigned to "
            "repository artifacts without inference."
        ),
    }


def main() -> int:
    HANDOFF.mkdir(parents=True, exist_ok=True)
    DESIGN.mkdir(parents=True, exist_ok=True)

    write(
        HANDOFF / "source-selection.md",
        """# Source Selection

## Context

- request_summary: V6 transfer-canary по загрузке анкеты клиента без изменения FT-first baseline.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-14`
- created_by: `Codex / ft-scope-analyzer`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Авторитетный source of truth для текущего Final. | `Final` | Таблица 6, строки 81-82. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Обязательный машиночитаемый источник BSR и структуры строк. | `Final XHTML` | Строки таблицы 134-135; BSR 206-212. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Визуальная и структурная сверка. | `Final PDF` | Страницы 26-27; BSR 206-212. |

## Machine-Readable XHTML Source

- main_ft_xhtml: `source/FT4AutoFinFinal.xhtml`
- xhtml_available: `yes`
- xhtml_path: `source/FT4AutoFinFinal.xhtml`
- xhtml_matches_main_ft: `yes`
- xhtml_role: `mandatory_machine_readable_extraction_source`
- xhtml_required_for_downstream: `yes`
- blocking_reason: `none`

## Structural Cross-Check PDF

- pdf_available: `yes`
- pdf_path: `source/FT4AutoFinFinal.pdf`
- pdf_matches_main_ft: `yes`
- limitation: PDF используется только для кодов/структуры/визуальной сверки; текстовая истина остаётся в DOCX.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Расшифровывает колонки `О` и `Р`; ограничивает внешний DaData context. | `yes` | Не добавляет новых требований. |

## Source Quality

- source family: только `FT4AutoFinFinal.*`.
- rejected: `AutoFinPreFinal.*` и созданные по нему старые BSR mappings.
- machine-readable status: XHTML подтверждён.
- production test cases: запрещены как requirement evidence.

## Ambiguity And Decision Log

| candidate | issue | decision |
| --- | --- | --- |
| `source/FT4AutoFinFinal.*` | Три источника имеют одинаковый Final stem и подтверждённую parity. | selected |
| `source/AutoFinPreFinal.*` | Legacy BSR mapping расходится с текущим Final. | rejected |
| production test cases | Производный результат, а не source of truth. | forbidden as requirement evidence |

## Handoff

- next_skill: `ft-scope-analyzer / prepared transfer compilation`.
- required_inputs: этот source selection, `AGENT-NOTES.md`, bounded parity и scope artifacts.
- blocked_reasons: none.
""",
    )

    write(
        HANDOFF / "scope-contract.md",
        """# Scope Contract — Questionnaire Upload Transfer V6

## Контекст

- `ft_slug`: `AutoFin`
- внешний scope: текущий Final, `section-16`, блок `Документы по заявке`.
- внутренний transfer package: информационное поле и desktop-загрузка файла `Анкета клиента`.
- цель: проверить переносимость prepared writer/reviewer на новый medium scope, не переписывая production baseline.

## In Scope

| source_property_id | source statement | requirement code | planned coverage |
| --- | --- | --- | --- |
| `SRC-QUT-001.P01` | Информационное поле отображается всегда. | `BSR 206` | отдельный TC |
| `SRC-QUT-001.P02` | Поле является информационным; `Р = Нет`. | `BSR 207`; DOCX/XHTML row property | отдельный TC |
| `SRC-QUT-002.P01` | Поле добавления файла отображается всегда. | `BSR 208` | отдельный TC |
| `SRC-QUT-002.P02` | Добавление через открытие проводника по кнопке. | `BSR 209` | отдельный TC |
| `SRC-QUT-002.P03` | После добавления отображается имя файла. | `BSR 211` | тот же observable upload result |
| `SRC-QUT-002.P04` | Добавление через Drag and Drop. | `BSR 209` | отдельный TC |
| `SRC-QUT-002.P05` | Допустимые форматы: jpg, png, pdf. | `BSR 210` | один parameterized TC |
| `SRC-QUT-002.P06` | Размер файла не более 40 МБ; точная граница 40 МБ допустима. | `BSR 210` | boundary TC |
| `SRC-QUT-002.P07` | Файл больше 40 МБ отклоняется с точным сообщением ФТ. | `BSR 210` | negative TC |
| `SRC-QUT-002.P08` | Недопустимый формат отклоняется с тем же точным сообщением ФТ. | `BSR 210` | negative TC |
| `SRC-QUT-002.P09` | В каждом типе документа остаётся не более одного файла. | `BSR 210` | count oracle без выдумывания UI-механизма |

## Out Of Scope

- QR/`Прикрепить с телефона` branch из `BSR 209` — отдельный async/integration package.
- фраза `Если файлов несколько... через запятую` из `BSR 211` — не включена: она требует cross-document-type setup, которого нет в этом внутреннем package.
- сохранение в электронном архиве Банка из `BSR 212` — отдельная persistence/observability задача.
- остальные документы, `Тип документа`, `Второй документ`, просмотр/удаление/скачивание.
- production test-case baseline и UI stand.

## Result Boundary

- expected: 11 atomic obligations, 10 unique TC titles, один writer и один independent reviewer.
- promotion: запрещён.
- final target: `fts/AutoFin/test-cases/16-questionnaire-upload-transfer-v6.md` должен оставаться отсутствующим.
""",
    )

    write(
        HANDOFF / "source-parity-check.md",
        """# Source Parity Check — Questionnaire Upload Transfer V6

## Контекст

- DOCX source of truth: `source/FT4AutoFinFinal.docx`.
- XHTML extraction source: `source/FT4AutoFinFinal.xhtml`.
- PDF structural cross-check: `source/FT4AutoFinFinal.pdf`, страницы 26-27.

## Identity

| source | SHA-256 | locator |
| --- | --- | --- |
| DOCX | `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b` | table 6, rows 81-82 |
| XHTML | `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66` | table rows 134-135 |
| PDF | `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58` | pages 26-27 |

## Parity Result

| item | DOCX | XHTML | PDF | result |
| --- | --- | --- | --- | --- |
| Информационное поле | always visible; informational; `О=Да`, `Р=Нет` | `BSR 206`; `BSR 207` | codes and row visible on p.26 | match |
| Анкета клиента upload | picker, DnD, QR; one file/type; jpg/png/pdf; max 40 МБ; exact error; filename; archive | `BSR 208-212` | `BSR 208-211` on p.26; continuation and `BSR 212` on p.27 | match |

## Code Recovery

- DOCX extraction сохраняет поведение, но не BSR labels.
- XHTML и PDF согласованно восстанавливают `BSR 206-212`; эти коды обязательны в `req_id` и traceability.
- Legacy `AutoFinPreFinal` mapping `BSR 198-203` отклонён: в текущем Final эти коды относятся к другим свойствам.

## Visual Check

- страницы 26-27 отрендерены и просмотрены: границы таблицы, колонки `О/Р`, BSR 206-212 и перенос строки между страницами читаемы;
- структурного расхождения, влияющего на выбранные statements, не обнаружено.
""",
    )

    write_source_row_inventory(
        HANDOFF / "source-row-inventory.md",
        """# Source Row Inventory — Questionnaire Upload Transfer V6

## Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-QUT-001` | `WP-QUT-01` | `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку`; `О=Да`; `Р=Нет`; text/string | `DOCX table 6 row 81; XHTML row 134; PDF p.26` | `BSR 206; BSR 207` | `yes` | `ATOM-QUT-001; ATOM-QUT-002` |
| `SRC-QUT-002` | `WP-QUT-01` | `Анкета клиента`; `О=Да`; `Р=Нет`; file upload/binary | `DOCX table 6 row 82; XHTML row 135; PDF pp.26-27` | `BSR 208; BSR 209; BSR 210; BSR 211; BSR 212` | `yes` | `ATOM-QUT-003; ATOM-QUT-004; ATOM-QUT-005; ATOM-QUT-006; ATOM-QUT-007; ATOM-QUT-008; ATOM-QUT-009; ATOM-QUT-010; ATOM-QUT-011` |

## Inventory Notes

- Каждый in-scope clause имеет отдельный `SRC-QUT-*.P*` в scope contract.
- `О` и `Р` интерпретируются только через обязательный `AGENT-NOTES.md`.
- Старый `work/test-design/14-application-card-documents-and-questionnaire-files` не является source evidence из-за Final/PreFinal drift.
""",
    )

    write(
        HANDOFF / "scope-coverage-gaps.md",
        """# Scope Coverage Gaps — Questionnaire Upload Transfer V6

## Контекст

- `scope_slug`: `questionnaire-upload-transfer-v6`
- Основной FT: `source/FT4AutoFinFinal.docx`

## Summary

- Найдено gaps внутри выбранных statements: `0`
- Есть blocking gaps: `no`
- Writing можно стартовать: `yes`

## Coverage Gaps

Пусто. Statements без достаточного oracle не включались скрыто: QR, cross-type multi-file display и archive persistence явно вынесены за границы внутреннего transfer package.

## Что Можно Покрывать Несмотря На Gaps

- Все 11 выбранных obligations по BSR 206-211.

## Что Нельзя Домысливать

- способ реакции на второй файл (replace/reject/message) сверх source-backed count `не более одного`;
- поведение QR, архива и нескольких типов документов.

## Требуемые Уточнения

- Нет для выбранного transfer package.
""",
    )

    write(
        DESIGN / "atomic-requirements-ledger.md",
        """# Atomic Requirements Ledger — Questionnaire Upload Transfer V6

| atom_id | package_id | source_property_id | req_id | source_row_id | atomic_statement | property_type | coverage_status | covered_by_tc | planned_tc_or_gap | gap_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-QUT-001` | `WP-QUT-01` | `SRC-QUT-001.P01` | `BSR 206` | `SRC-QUT-001` | Информационное поле отображается всегда. | `visibility` | `covered` | `TC-QUT-001` | `TC-QUT-001` | `none_required:covered` |
| `ATOM-QUT-002` | `WP-QUT-01` | `SRC-QUT-001.P02` | `BSR 207` | `SRC-QUT-001` | Информационное поле не допускает ручного редактирования своего текста. | `field-property` | `covered` | `TC-QUT-002` | `TC-QUT-002` | `none_required:covered` |
| `ATOM-QUT-003` | `WP-QUT-01` | `SRC-QUT-002.P01` | `BSR 208` | `SRC-QUT-002` | Поле добавления файла `Анкета клиента` отображается всегда. | `visibility` | `covered` | `TC-QUT-003` | `TC-QUT-003` | `none_required:covered` |
| `ATOM-QUT-004` | `WP-QUT-01` | `SRC-QUT-002.P02` | `BSR 209` | `SRC-QUT-002` | Документ можно добавить через открытие проводника по кнопке. | `file-upload` | `covered` | `TC-QUT-004` | `TC-QUT-004` | `none_required:covered` |
| `ATOM-QUT-005` | `WP-QUT-01` | `SRC-QUT-002.P03` | `BSR 211` | `SRC-QUT-002` | После добавления документа отображается имя прикреплённого файла. | `file-upload-result` | `covered` | `TC-QUT-004` | `TC-QUT-004` | `none_required:covered` |
| `ATOM-QUT-006` | `WP-QUT-01` | `SRC-QUT-002.P04` | `BSR 209` | `SRC-QUT-002` | Документ можно добавить через Drag and Drop. | `file-upload` | `covered` | `TC-QUT-005` | `TC-QUT-005` | `none_required:covered` |
| `ATOM-QUT-007` | `WP-QUT-01` | `SRC-QUT-002.P05` | `BSR 210` | `SRC-QUT-002` | Поле принимает файлы форматов jpg, png и pdf. | `equivalence` | `covered` | `TC-QUT-006` | `TC-QUT-006` | `none_required:covered` |
| `ATOM-QUT-008` | `WP-QUT-01` | `SRC-QUT-002.P06` | `BSR 210` | `SRC-QUT-002` | Файл размером ровно 40 МБ соответствует ограничению `не более 40 МБ`. | `boundary` | `covered` | `TC-QUT-007` | `TC-QUT-007` | `none_required:covered` |
| `ATOM-QUT-009` | `WP-QUT-01` | `SRC-QUT-002.P07` | `BSR 210` | `SRC-QUT-002` | Файл больше 40 МБ не загружается, отображается точный текст ошибки из ФТ. | `negative-oracle` | `covered` | `TC-QUT-008` | `TC-QUT-008` | `none_required:covered` |
| `ATOM-QUT-010` | `WP-QUT-01` | `SRC-QUT-002.P08` | `BSR 210` | `SRC-QUT-002` | Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ. | `negative-oracle` | `covered` | `TC-QUT-009` | `TC-QUT-009` | `none_required:covered` |
| `ATOM-QUT-011` | `WP-QUT-01` | `SRC-QUT-002.P09` | `BSR 210` | `SRC-QUT-002` | После попытки добавить второй файл в типе документа остаётся не более одного файла. | `file-cardinality` | `covered` | `TC-QUT-010` | `TC-QUT-010` | `none_required:covered` |
""",
    )

    exact_error = (
        "Документы не загружены. Проверьте соответствуют ли документы требованиям: "
        "формат jpg, png, pdf, размер не более 40 МБ"
    )
    obligations = [
        (1, "SRC-QUT-001.P01", 1, "field-property", "field-visible", "Информационное поле отображается всегда.", "SRC-QUT-001; BSR 206", 1, "Прямая visibility obligation."),
        (2, "SRC-QUT-001.P02", 2, "field-property", "informational-read-only", "Текст информационного поля нельзя изменить ручным вводом.", "SRC-QUT-001; BSR 207", 2, "BSR 207 и Р=Нет дают observable non-editability."),
        (3, "SRC-QUT-002.P01", 3, "field-property", "field-visible", "Поле добавления файла Анкета клиента отображается всегда.", "SRC-QUT-002; BSR 208", 3, "Прямая visibility obligation."),
        (4, "SRC-QUT-002.P02", 4, "file-upload", "picker-upload", "После выбора portable jpg через проводник файл добавлен.", "SRC-QUT-002; BSR 209", 4, "Сгруппировано с OBL-QUT-005 одним upload result."),
        (5, "SRC-QUT-002.P03", 5, "file-upload", "filename-visible", "После добавления отображается точное имя выбранного файла.", "SRC-QUT-002; BSR 211", 4, "Один observable result с picker upload."),
        (6, "SRC-QUT-002.P04", 6, "file-upload", "drag-drop-upload", "После Drag and Drop portable pdf файл добавлен и его имя отображается.", "SRC-QUT-002; BSR 209; BSR 211", 5, "Отдельный способ действия."),
        (7, "SRC-QUT-002.P05", 7, "equivalence", "allowed-file-formats", "В отдельных чистых итерациях jpg, png и pdf добавляются успешно.", "SRC-QUT-002; BSR 210", 6, "Один элемент и одно действие для полного фиксированного перечня."),
        (8, "SRC-QUT-002.P06", 8, "input-boundaries", "max-file-size", "Файл ровно 41 943 040 байт добавляется успешно.", "SRC-QUT-002; BSR 210", 7, "Точная положительная граница."),
        (9, "SRC-QUT-002.P07", 9, "negative-oracle", "oversize-file", f"Файл 41 943 041 байт не добавляется; отображается `{exact_error}`.", "SRC-QUT-002; BSR 210", 8, "Точный source-backed oracle."),
        (10, "SRC-QUT-002.P08", 10, "negative-oracle", "unsupported-format", f"Файл txt не добавляется; отображается `{exact_error}`.", "SRC-QUT-002; BSR 210", 9, "Точный source-backed oracle."),
        (11, "SRC-QUT-002.P09", 11, "file-upload", "one-file-per-type", "После попытки добавить второй файл отображается не более одного имени файла этого типа.", "SRC-QUT-002; BSR 210", 10, "Не утверждается replace/reject/message mechanism."),
    ]
    rows = [
        "# Coverage Obligation Table — Questionnaire Upload Transfer V6",
        "",
        "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for number, property_id, atom, prop_type, obligation_class, behavior, source_ref, tc, notes in obligations:
        rows.append(
            f"| `OBL-QUT-{number:03d}` | `WP-QUT-01` | `{property_id}` | `ATOM-QUT-{atom:03d}` | `{prop_type}` | `{obligation_class}` | {behavior} | `{source_ref.replace('; ', '`; `')}` | `TC-QUT-{tc:03d}` | `covered` | {notes} |"
        )
    write(DESIGN / "coverage-obligation-table.md", "\n".join(rows))

    write(
        DESIGN / "package-test-design-plan.md",
        f"""# Package Test Design Plan — Questionnaire Upload Transfer V6

## Portable Fixture Contracts

- `FIXTURE-QUT-JPG`: локально создать валидный JPEG `questionnaire-valid.jpg` размером 1 024 байта.
- `FIXTURE-QUT-PNG`: локально создать валидный PNG `questionnaire-valid.png` размером 1 024 байта.
- `FIXTURE-QUT-PDF`: локально создать валидный PDF `questionnaire-valid.pdf` размером 1 024 байта.
- `FIXTURE-QUT-PDF-40MB`: локально создать валидный PDF `questionnaire-40mb.pdf` размером ровно 41 943 040 байт.
- `FIXTURE-QUT-PDF-OVER40`: локально создать валидный PDF `questionnaire-over40mb.pdf` размером ровно 41 943 041 байт.
- `FIXTURE-QUT-TXT`: локально создать текстовый файл `questionnaire-invalid.txt` размером 1 024 байта.
- `FIXTURE-QUT-PDF-A`: локально создать валидный PDF `questionnaire-first.pdf` размером 1 024 байта.
- `FIXTURE-QUT-PDF-B`: локально создать валидный PDF `questionnaire-second.pdf` размером 1 024 байта, отличный по имени и содержимому от `FIXTURE-QUT-PDF-A`.

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | test_data | single_expected_behavior | oracle_source | planned_tc_or_gap | status | grouping_justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PLAN-QUT-001` | `WP-QUT-01` | `visibility` | `SRC-QUT-001; BSR 206` | `ATOM-QUT-001` | Открыть блок `Документы по заявке`. | `positive` | `visibility` | `field-state` | `none_required` | Информационное поле отображается. | `DOCX/XHTML/PDF` | `TC-QUT-001` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-002` | `WP-QUT-01` | `field-property` | `SRC-QUT-001; BSR 207` | `ATOM-QUT-002` | Установить фокус на информационном поле и попытаться ввести `Тест`. | `positive` | `read-only` | `text:Тест` | `Тест` | Текст информационного поля не изменяется. | `DOCX/XHTML/PDF; Р=Нет` | `TC-QUT-002` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-003` | `WP-QUT-01` | `visibility` | `SRC-QUT-002; BSR 208` | `ATOM-QUT-003` | Открыть блок `Документы по заявке`. | `positive` | `visibility` | `field-state` | `none_required` | Поле добавления файла `Анкета клиента` отображается. | `DOCX/XHTML/PDF` | `TC-QUT-003` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-004` | `WP-QUT-01` | `file-upload` | `SRC-QUT-002; BSR 209; BSR 211` | `ATOM-QUT-004; ATOM-QUT-005` | По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`. | `positive` | `picker-upload` | `file:FIXTURE-QUT-JPG` | `FIXTURE-QUT-JPG` | Файл добавлен, отображается имя `questionnaire-valid.jpg`. | `DOCX/XHTML/PDF` | `TC-QUT-004` | `covered` | `grouping-justification:` способ добавления и имя файла образуют один observable upload result. |
| `PLAN-QUT-005` | `WP-QUT-01` | `file-upload` | `SRC-QUT-002; BSR 209; BSR 211` | `ATOM-QUT-006` | Перетащить `FIXTURE-QUT-PDF` в поле `Анкета клиента`. | `positive` | `drag-drop-upload` | `file:FIXTURE-QUT-PDF` | `FIXTURE-QUT-PDF` | Файл добавлен, отображается имя `questionnaire-valid.pdf`. | `DOCX/XHTML/PDF` | `TC-QUT-005` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-006` | `WP-QUT-01` | `equivalence` | `SRC-QUT-002; BSR 210` | `ATOM-QUT-007` | В трёх независимых чистых итерациях добавить через проводник `FIXTURE-QUT-JPG`, `FIXTURE-QUT-PNG`, `FIXTURE-QUT-PDF`. | `positive` | `allowed-formats` | `files:three-formats` | `FIXTURE-QUT-JPG; FIXTURE-QUT-PNG; FIXTURE-QUT-PDF` | В каждой итерации выбранный файл добавляется. | `DOCX/XHTML/PDF` | `TC-QUT-006` | `covered` | `none_required:one-fixed-value-set` |
| `PLAN-QUT-007` | `WP-QUT-01` | `boundary` | `SRC-QUT-002; BSR 210` | `ATOM-QUT-008` | Добавить через проводник `FIXTURE-QUT-PDF-40MB`. | `positive-boundary` | `max-file-size` | `file:exact-max` | `FIXTURE-QUT-PDF-40MB` | Файл размером ровно 41 943 040 байт добавляется. | `DOCX/XHTML/PDF` | `TC-QUT-007` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-008` | `WP-QUT-01` | `negative-oracle` | `SRC-QUT-002; BSR 210` | `ATOM-QUT-009` | Добавить через проводник `FIXTURE-QUT-PDF-OVER40`. | `negative-boundary` | `oversize-file` | `file:over-max` | `FIXTURE-QUT-PDF-OVER40` | Файл не добавляется; отображается `{exact_error}`. | `DOCX/XHTML/PDF exact text` | `TC-QUT-008` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-009` | `WP-QUT-01` | `negative-oracle` | `SRC-QUT-002; BSR 210` | `ATOM-QUT-010` | Добавить через проводник `FIXTURE-QUT-TXT`. | `negative-equivalence` | `unsupported-format` | `file:txt` | `FIXTURE-QUT-TXT` | Файл не добавляется; отображается `{exact_error}`. | `DOCX/XHTML/PDF exact text` | `TC-QUT-009` | `covered` | `none_required:single-atom` |
| `PLAN-QUT-010` | `WP-QUT-01` | `file-cardinality` | `SRC-QUT-002; BSR 210` | `ATOM-QUT-011` | Добавить `FIXTURE-QUT-PDF-A`, затем через тот же picker попытаться добавить `FIXTURE-QUT-PDF-B`. | `boundary` | `one-file-per-type` | `files:two-distinct` | `FIXTURE-QUT-PDF-A; FIXTURE-QUT-PDF-B` | После второго действия в поле отображается не более одного имени файла; способ replace/reject и сообщение не утверждаются. | `DOCX/XHTML/PDF count rule` | `TC-QUT-010` | `covered` | `none_required:single-atom` |
""",
    )

    write(
        DESIGN / "test-design-applicability-matrix.md",
        """# Test-Design Applicability Matrix — Questionnaire Upload Transfer V6

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| file-upload | `yes` | `BSR 209-211` | Picker, Drag and Drop, file name and cardinality. | `ATOM-QUT-004..ATOM-QUT-011` | `TC-QUT-004..TC-QUT-010` | `none_required:covered` |
| input-boundaries | `yes` | `BSR 210` | Exact max 40 МБ and just-over boundary. | `ATOM-QUT-008; ATOM-QUT-009` | `TC-QUT-007; TC-QUT-008` | `none_required:covered` |
| negative-oracle | `yes` | `BSR 210` | Exact shared error text is source-backed. | `ATOM-QUT-009; ATOM-QUT-010` | `TC-QUT-008; TC-QUT-009` | `none_required:covered` |
| equivalence | `yes` | `BSR 210` | Complete fixed format list jpg/png/pdf plus txt invalid class. | `ATOM-QUT-007; ATOM-QUT-010` | `TC-QUT-006; TC-QUT-009` | `none_required:covered` |
| visibility | `yes` | `BSR 206; BSR 208` | Two independent always-visible properties. | `ATOM-QUT-001; ATOM-QUT-003` | `TC-QUT-001; TC-QUT-003` | `none_required:covered` |
| persistence | `no` | `BSR 212` | Explicitly outside this internal package. | `none_required` | `none_required` | `none_required:out-of-scope` |
| integration | `no` | `BSR 209 QR branch` | Explicitly outside this internal package. | `none_required` | `none_required` | `none_required:out-of-scope` |
""",
    )

    decomposition = context_decomposition()
    write(
        HANDOFF / "context-decomposition.v6.json",
        json.dumps(decomposition, ensure_ascii=False, indent=2),
    )
    writer = decomposition["writer"]
    reviewer = decomposition["reviewer"]
    removal = decomposition["proven_removal"]
    write(
        HANDOFF / "context-decomposition.v6.md",
        f"""# Context Decomposition V6

## Итог

V5 prompt разложен по фактическим секциям. Единственное доказанное нерелевантное содержимое — полный package-note раздел DaData в обеих независимых сессиях. Source-backed obligations, oracles, fixtures, writer draft и role profiles не сокращаются.

## Exact Prompt Bytes

| role | V5 prompt | irrelevant DaData block | projected prompt after guarded projection |
| --- | ---: | ---: | ---: |
| writer | {writer['prompt_bytes']} | {writer['irrelevant_dadata_bytes']} | {writer['projected_prompt_bytes']} |
| reviewer | {reviewer['prompt_bytes']} | {reviewer['irrelevant_dadata_bytes']} | {reviewer['projected_prompt_bytes']} |

- net exact prompt bytes removed: `{removal['net_prompt_bytes_removed']}`.
- guard: DaData section remains intact when selected evidence outside the note references DaData.
- V5 uncached input tokens: `{decomposition['v5_uncached_input_tokens']}`; backend bootstrap/system tokens не имеют section attribution, поэтому их нельзя честно приписать repo prompt sections.

## Writer Sections

{json.dumps(writer['sections'], ensure_ascii=False, indent=2)}

## Reviewer Sections

{json.dumps(reviewer['sections'], ensure_ascii=False, indent=2)}

## Не сокращать

- semantic obligation projection и exact observable oracle;
- portable fixture contracts;
- immutable draft для независимого reviewer;
- runtime profile каждой отдельной exec session.
""",
    )

    write(
        HANDOFF / "architecture-decision.md",
        """# Architecture Decision V6

## Decision

Добавить guarded package-context projection перед writer/reviewer prompts: удалять только H2 DaData из mandatory package notes, если выбранное evidence вне этого блока не содержит DaData behavior.

## Why

- V5 передал один и тот же большой нерелевантный DaData раздел двум отдельным sessions.
- `AGENT-NOTES.md` остаётся обязательным: релевантная расшифровка `О/Р` сохраняется.
- Для DaData scope полный раздел сохраняется; тест покрывает обе ветки.

## Rejected Alternatives

- сокращать atomic statements/oracles: ухудшает независимый semantic review;
- убирать reviewer draft: нарушает независимую проверку результата writer-а;
- объединять writer/reviewer session: противоречит целевой архитектуре отдельных этапов;
- приписывать все uncached tokens repo prompt: event stream не даёт такого attribution.
""",
    )

    write(
        HANDOFF / "benchmark-protocol.v6.md",
        f"""# V6 Transfer Canary Protocol

## Цель

Проверить переносимость prepared package v8 и context projection на новом current-source file-upload scope, не использовавшемся для настройки V3-V5.

## Один запуск

- fresh cycle `questionnaire-upload-transfer-v6-20260714`;
- backend `exec`; 11 obligations; 10 planned TC;
- один writer и один independent reviewer в разных sessions;
- один dispatcher invocation; retry/resume/repair/rebind/sharding/SDK fallback запрещены.

## Quality Gates

- package compiled from current `FT4AutoFinFinal.*`, BSR 206-211;
- reviewer: 11/11 covered, incorrect=0, error findings=0;
- unique IDs/titles; exact negative message retained;
- package context projection removes DaData only as not applicable;
- no production mutation; `{TARGET_REL}` remains absent.

## Performance

- publish duration, uncached tokens/OBL and exact context projection bytes;
- quality dominates speed; no retry may be selected by performance;
- one canary proves transfer behavior, not a stable median.
""",
    )

    dispatcher = {
        "version": 1,
        "cycle_dir": CYCLE_REL,
        "exec_runner_args": [
            "--ft-root",
            "fts/AutoFin",
            "--cycle-dir",
            CYCLE_REL,
            "--final-artifact",
            TARGET_REL,
            "--prepared-package",
            f"{CYCLE_REL}/prepared-input/{PACKAGE_ID}/stage-package.json",
            "--prepared-standard-writer-mode",
            "structured",
            "--sandbox-flag",
            "--sandbox",
            "--writer-sandbox",
            "workspace-write",
            "--reviewer-sandbox",
            "read-only",
            "--working-directory-flag",
            "--cd",
            "--json-flag",
            "--json",
            "--output-last-message-flag",
            "--output-last-message",
            "--output-schema-flag",
            "--output-schema",
            "--writer-timeout-seconds",
            "600",
            "--reviewer-timeout-seconds",
            "450",
            "--writer-command-budget",
            "1",
            "--reviewer-command-budget",
            "1",
            "--prepared-reviewer-command-budget",
            "1",
            "--prepared-standard-writer-context-max-bytes",
            "131072",
            "--prepared-standard-reviewer-context-max-bytes",
            "131072",
            "--prepared-structured-writer-single-session-tc-limit",
            "10",
            "--prepared-structured-writer-shard-size",
            "10",
            "--prepared-structured-writer-max-shards",
            "1",
            "--prepared-structured-reviewer-obligation-limit",
            "100",
        ],
        "sdk_runner_args": [],
    }
    write(
        HANDOFF / "dispatcher-config.v6.json",
        json.dumps(dispatcher, ensure_ascii=False, indent=2),
    )

    write(
        HANDOFF / "pre-live-stop-gate.md",
        """# Pre-Live Stop Gate V6

## Status

`open-offline-validation`

## До Live Обязательно

- focused/full agent tests and artifact validator pass;
- architecture audit has 0 findings;
- current-source package compile, validate-only and exec dry-run pass;
- generic reference-only regression proves no invented fixture values;
- protected baselines and absent V6 target confirmed;
- offline checkpoint committed and pushed; local/origin SHA match;
- separate hash-bound authorization binds package/config/checkpoint and one invocation.

## Запрещено

- live до checkpoint и authorization;
- retry, SDK fallback, repair, rebind, sharding or promotion;
- manual benchmark draft edits;
- any production test-case write.
""",
    )

    write(
        HANDOFF / "agent-decision-log.md",
        """# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v6` |
| stage | `agent-architecture-auditor` |
| started_from | `work/stage-handoffs/54-reference-fixture-contract-v5/prompt.reference-fixture-v5-to-next.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | Current Final parity extraction | Использовать только `FT4AutoFinFinal.*` и BSR 206-212. | Legacy PreFinal BSR mapping конфликтует с текущим Final. | `source-selection.md`; `source-parity-check.md` | high | applied |
| `DEC-002` | 2 | `scope-boundary` | V6 transfer requirement | Выбрать desktop questionnaire upload clauses BSR 206-211; QR/archive/multi-type display отложить. | Новый bounded medium scope проверяет transfer без UI/async/persistence шума. | `scope-contract.md` | high | applied |
| `DEC-003` | 3 | `test-design` | BSR 210 count rule | Проверять только `не более одного`, не утверждать replace/reject/message mechanism. | FT задаёт count oracle, но не UI mechanism. | compiler design plan | high | applied |
| `DEC-004` | 4 | `architecture` | V5 context decomposition | Guarded-удаление только нерелевантного DaData note section. | Дублирование доказано exact prompt bytes; semantic evidence не сокращается. | code/tests; `context-decomposition.v6.*` | high | applied |
| `DEC-005` | 5 | `validation` | V5 active prompt | Добавить generic reference-only no-invention regression. | Package v8 не должен выводить fixture из всего dictionary без explicit plan labels. | compiler test | high | applied |
| `DEC-006` | 6 | `authorization` | User instruction `Выполняй v6` | Live возможен только после pushed checkpoint и separate immutable binding. | Сохраняет terminal one-shot discipline. | `pre-live-stop-gate.md` | high | proposed |
""",
    )

    write(
        HANDOFF / "architecture-session-log.md",
        """# Architecture Session Log V6

## Session Metadata

| field | value |
| --- | --- |
| skill | `agent-architecture-auditor` |
| mode | `transfer-and-context-efficiency-v6` |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v6` |
| started_from | `work/stage-handoffs/54-reference-fixture-contract-v5/prompt.reference-fixture-v5-to-next.md` |
| status_after | `ready-for-next-stage` |

## Inputs Read

- H54 V5 terminal artifacts and accepted performance evidence.
- Current Final DOCX/XHTML/PDF bounded rows for BSR 206-212.
- Package notes, prepared compiler/runner, canonical handoff references.

## Inputs Not Used

- Production test cases as requirement evidence.
- UI stand and previous benchmark drafts as requirement evidence.
- User-owned untracked diagnostics and section 4.3 test-case file.

## Key Decisions

- Current Final BSR 206-212 заменяют несовместимый legacy PreFinal mapping.
- Transfer package ограничен desktop upload clauses; QR/archive/cross-type display не смешиваются с canary.
- Сокращён только доказанно нерелевантный DaData note block; semantic transport сохранён.

## Risks And Fallbacks

- Один canary не даёт latency median; performance остаётся observation.
- Backend bootstrap tokens не имеют section attribution; exact repo prompt bytes не выдаются за полную token attribution.

## Validation

- Bounded DOCX/XHTML/PDF extraction and visual page review: parity pass.
- Prepared compiler: 11 obligations, 0 gaps, standard-required.
- Focused runner/compiler tests and scoped artifact validator are required before live.

## Contamination Check

- Production test cases не читались как requirement evidence и не изменялись.
- Untracked `evals/sdk-turn-diagnostics/**` и пользовательский section 4.3 файл не читались, не изменялись и не включаются в commit.

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Initial section filter used bare `16`. | resolver expected generated id | reran with `section-16`; discarded failed output | `n/a` | `n/a` | no residual fidelity risk | use generated section ids |
| `TF-002` | XHTML passed to DOCX/PDF section loader. | unsupported `.xhtml` API path | used XHTML row extraction and DOCX section resolver separately | `scripts/extract_autofin_bsr_evidence.py` | yes | no residual fidelity risk | keep source roles separate |
| `TF-003` | PDF renderer emitted Poppler Unicode-map path warnings. | optional map lookup | rendered pages remained readable; text parity separately checked with pypdf | `tmp/pdfs/v6-questionnaire-upload/` | no | no residual fidelity risk | source hashes and parity retained |
| `TF-004` | broad XHTML search entered embedded base64. | unbounded text search | discarded output; used bounded XML table rows/extractor | `n/a` | `n/a` | no residual fidelity risk | never use base64 output as evidence |
| `TF-005` | Console/inline PowerShell discovery output was unsafe as Cyrillic evidence. | unbounded console search and invalid pipeline shape | source files were re-read with explicit `Get-Content -Encoding UTF8`; distorted stdout was discarded and not used as evidence | `n/a` | `n/a` | no residual fidelity risk after UTF-8 reread | keep bounded UTF-8 file reads |
| `TF-006` | Builder expected a nonexistent nested performance key. | first builder execution | corrected to canonical `uncached_input_tokens_total` and reran deterministically | `scripts/build_autofin_questionnaire_upload_transfer_v6.py` | yes | no residual fidelity risk | builder output revalidated |
| `TF-007` | Guessed dispatcher filename did not exist. | `run_review_cycle_dispatcher.py` | discovered canonical `review_cycle_backend_dispatcher.py` with `rg --files` | `n/a` | `n/a` | no residual fidelity risk | use canonical dispatcher path |
| `TF-008` | First direct validate-only lacked verified CLI flag. | runner validate-only | reran after successful exec capability probe with `--cli-contract-verified` | `backend-selection.dry-run.json` | yes | no residual fidelity risk | immutable config semantics unchanged |
| `TF-009` | Initial source-row inventory was emitted by the general builder. | ad-hoc generated table writer | regenerated the final inventory through canonical `write_artifact_sections.py` manifest | `_artifact_write/source-row-inventory/manifest.json` | yes | no residual fidelity risk | retain manifest for replay |

## Artifact Write Strategy

Generated handoff/compiler inputs are emitted by `scripts/build_autofin_questionnaire_upload_transfer_v6.py`; code and tests are changed by targeted patch. Production test cases are excluded.

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-row-inventory.md` | `small table-heavy` | `file-based section manifest` | `yes` | `scripts/write_artifact_sections.py --manifest _artifact_write/source-row-inventory/manifest.json` | `yes` |
| `work/stage-handoffs/55-questionnaire-upload-transfer-v6/**` | `small files` | `file-based deterministic builder` | `yes` | `scripts/build_autofin_questionnaire_upload_transfer_v6.py` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Runtime/source routing confirmed | Windows PowerShell UTF-8 file reads; current Final selected | source selection |
| 2 | DOCX/XHTML/PDF bounded parity | BSR 206-212 aligned; legacy mapping rejected | source parity |
| 3 | V5 context decomposed | 10 530 net prompt bytes proven irrelevant across two sessions | context decomposition |
| 4 | Guarded projection and regressions added | irrelevant DaData omitted; relevant branch retained | code/tests |
| 5 | Transfer package compiled | 11 obligations, 10 TC, 0 gaps | prepared package |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Current-source parity | pass | DOCX/XHTML/PDF hashes and BSR mapping | none |
| Generic reference-only no-invention | pending at initial write | focused regression | require pass before live |
| Production boundary | pass at initial write | target absent; protected hashes captured | recheck after live |

## Handoff Notes For Next Session

- Live разрешён только после full offline gates, pushed checkpoint и separate hash binding.
- Любой terminal result consumes the single V6 budget; no retry or promotion.
""",
    )

    write(
        HANDOFF / "workflow-state.yaml",
        """ft_slug: AutoFin
prepared_compiler_contract_version: 2
scope_slug: questionnaire-upload-transfer-v6
current_stage: agent-architecture-auditor
stage_status: ready-for-next-stage
current_round: 1
next_skill: agent-architecture-auditor
required_inputs:
  - AGENT-NOTES.md
  - work/stage-handoffs/54-reference-fixture-contract-v5/workflow-state.yaml
  - work/stage-handoffs/54-reference-fixture-contract-v5/prompt.reference-fixture-v5-to-next.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-selection.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/scope-contract.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-parity-check.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-row-inventory.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/scope-coverage-gaps.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/atomic-requirements-ledger.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/coverage-obligation-table.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/package-test-design-plan.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/test-design-applicability-matrix.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/context-decomposition.v6.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/architecture-decision.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/benchmark-protocol.v6.md
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/dispatcher-config.v6.json
  - work/stage-handoffs/55-questionnaire-upload-transfer-v6/pre-live-stop-gate.md
latest_artifacts:
  source_selection: work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-selection.md
  scope_contract: work/stage-handoffs/55-questionnaire-upload-transfer-v6/scope-contract.md
  source_parity_check: work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-parity-check.md
  source_row_inventory: work/stage-handoffs/55-questionnaire-upload-transfer-v6/source-row-inventory.md
  scope_coverage_gaps: work/stage-handoffs/55-questionnaire-upload-transfer-v6/scope-coverage-gaps.md
  coverage_gaps: work/stage-handoffs/55-questionnaire-upload-transfer-v6/scope-coverage-gaps.md
  atomic_requirements_ledger: work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/atomic-requirements-ledger.md
  coverage_obligation_table: work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/coverage-obligation-table.md
  package_test_design_plan: work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/package-test-design-plan.md
  test_design_applicability_matrix: work/stage-handoffs/55-questionnaire-upload-transfer-v6/compiler-inputs/questionnaire-upload-transfer-v6/test-design-applicability-matrix.md
  context_decomposition_v6: work/stage-handoffs/55-questionnaire-upload-transfer-v6/context-decomposition.v6.md
  architecture_decision: work/stage-handoffs/55-questionnaire-upload-transfer-v6/architecture-decision.md
  benchmark_protocol: work/stage-handoffs/55-questionnaire-upload-transfer-v6/benchmark-protocol.v6.md
  dispatcher_config: work/stage-handoffs/55-questionnaire-upload-transfer-v6/dispatcher-config.v6.json
  pre_live_stop_gate: work/stage-handoffs/55-questionnaire-upload-transfer-v6/pre-live-stop-gate.md
  decision_log: work/stage-handoffs/55-questionnaire-upload-transfer-v6/agent-decision-log.md
  session_log: work/stage-handoffs/55-questionnaire-upload-transfer-v6/architecture-session-log.md
coverage_gaps:
  blocking: 0
  non_blocking: 0
open_questions: []
blocking_reasons: []
accepted_risks:
  - V6 is an internal transfer package, not full coverage of the document-upload row.
  - One live canary can verify transfer correctness but not stable latency median.
  - Generated draft is benchmark evidence and must not be promoted.
""",
    )
    print(
        json.dumps(
            {
                "handoff": HANDOFF.relative_to(ROOT).as_posix(),
                "design": DESIGN.relative_to(ROOT).as_posix(),
                "files": len(list(HANDOFF.rglob("*"))),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
