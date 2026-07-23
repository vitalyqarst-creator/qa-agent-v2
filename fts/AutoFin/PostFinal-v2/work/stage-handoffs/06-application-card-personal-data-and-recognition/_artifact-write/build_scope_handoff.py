from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[7]
HANDOFF = REPO / "fts/AutoFin/PostFinal-v2/work/stage-handoffs/06-application-card-personal-data-and-recognition"
FT_ROOT = REPO / "fts/AutoFin/PostFinal-v2"
CONTEXT_PATH = HANDOFF / "prepared-bounded-context.json"
CONTEXT = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
ROWS = CONTEXT["source_rows"]
ROW_BY_ID = {row["source_row_id"]: row for row in ROWS}
NOW = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%dT%H:%M:%S+07:00")


def rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        return p.as_posix()
    return p.relative_to(REPO).as_posix()


def ft_rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = REPO / p
    return p.relative_to(FT_ROOT).as_posix()


def sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def esc(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", "<br>")
    text = text.replace("|", "\\|")
    return text


def codes(row: dict) -> list[str]:
    return list(row.get("requirement_codes_hint") or row.get("requirement_codes") or [])


def row_text(row_id: str) -> str:
    return str(ROW_BY_ID[row_id]["bounded_source_text"])


def row_ref(row_id: str) -> str:
    row = ROW_BY_ID[row_id]
    return f"{row['source_path']} {row['source_locator']}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_md(name: str, title: str, sections: list[tuple[int, str, str]]) -> None:
    base = HANDOFF / "_artifact-write"
    stale_root = base / "sections"
    if stale_root.exists():
        for stale in stale_root.rglob("*.md"):
            stale.unlink()
    section_dir = base / "sections" / name.replace(".md", "")
    manifest_dir = base / "manifests"
    section_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    preamble = section_dir / "00-preamble.txt"
    write_text(preamble, f"# {title}")
    manifest_sections: list[dict[str, object]] = []
    for idx, (level, heading, content) in enumerate(sections, start=1):
        path = section_dir / f"{idx:02d}-{re.sub(r'[^A-Za-z0-9_-]+', '-', heading).strip('-') or 'section'}.txt"
        write_text(path, content)
        manifest_sections.append(
            {
                "level": level,
                "heading": heading,
                "content_file": Path(os.path.relpath(path, manifest_dir)).as_posix(),
            }
        )

    manifest = {
        "target_path": Path(os.path.relpath(HANDOFF / name, manifest_dir)).as_posix(),
        "preamble_file": Path(os.path.relpath(preamble, manifest_dir)).as_posix(),
        "sections": manifest_sections,
    }
    manifest_path = manifest_dir / f"{name}.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def make_source_selection() -> None:
    docx = FT_ROOT / "source/PostFinal-v2.docx"
    xhtml = FT_ROOT / "source/PostFinal-v2.xhtml"
    pdf = FT_ROOT / "source/PostFinal-v2.pdf"
    clarification = FT_ROOT / "support/application-card-personal-data-and-recognition-approved-clarifications.md"
    dictionaries = FT_ROOT / "support/АФБ справочники 26.06.26.md"
    mockup2 = FT_ROOT / "mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg"
    mockup4 = FT_ROOT / "mockups/Рисунок 4 Макет всплывающего окна Распознание документов.jpg"
    mockup5 = FT_ROOT / "mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg"

    sections = [
        (
            2,
            "Context",
            "\n".join(
                [
                    "- `request_summary`: Подтвержденный manual scope после выбора `SCOPE-OPTION-002`.",
                    "- `selected_ft_slug`: `AutoFin/PostFinal-v2`",
                    "- `selection_status`: `selected`",
                    f"- `created_at`: `{NOW}`",
                    "- `created_by`: `Codex / ft-scope-analyzer`",
                    "- `scope_slug`: `application-card-personal-data-and-recognition`",
                ]
            ),
        ),
        (
            2,
            "Main FT Documents",
            "\n".join(
                [
                    "| path | role | selection_reason | version_or_date | source_quality_notes |",
                    "| --- | --- | --- | --- | --- |",
                    f"| `{rel(docx)}` | `main-ft-docx` | Authoritative source of truth for FT semantics. | `PostFinal-v2`; sha256 `{sha256(docx)}` | DOCX content text matches selected rows; plain XML extraction loses visible BSR markers, so XHTML/PDF preserve code anchors. |",
                    f"| `{rel(xhtml)}` | `main-ft-xhtml` | Mandatory machine-readable source for table rows and exact BSR anchors. | `PostFinal-v2`; sha256 `{sha256(xhtml)}` | XML parsed; selected bounded baseline has 41 candidates. |",
                    f"| `{rel(pdf)}` | `main-ft-pdf` | Structural/visual parity for table 4 and BSR 43-83. | `PostFinal-v2`; sha256 `{sha256(pdf)}` | PDF pages 16-18 contain all BSR 43-83 anchors; PDF is not source of truth. |",
                ]
            ),
        ),
        (
            2,
            "Machine-Readable XHTML Source",
            "\n".join(
                [
                    f"- `main_ft_xhtml`: `{rel(xhtml)}`",
                    "- `xhtml_available`: `yes`",
                    f"- `xhtml_path`: `{rel(xhtml)}`",
                    "- `xhtml_matches_main_ft`: `yes`",
                    "- `xhtml_role`: `mandatory_machine_readable_extraction_source`",
                    "- `xhtml_required_for_downstream`: `yes`",
                    "- `blocking_reason`: `none`",
                    "- `bounded_source_rows`: `41`",
                    "- `scope_local_rows`: `SRC-027`-`SRC-040`; next boundary row `SRC-041` excluded.",
                ]
            ),
        ),
        (
            2,
            "Structural Cross-Check PDF",
            "\n".join(
                [
                    "- `pdf_available`: `yes`",
                    f"- `pdf_path`: `{rel(pdf)}`",
                    "- `pdf_matches_main_ft`: `yes`",
                    "- `pdf_scope_pages`: `16-18`",
                    "- `limitation`: PDF confirms structure/codes only; DOCX/XHTML remain semantic/extraction sources.",
                ]
            ),
        ),
        (
            2,
            "Support Files And Mockups",
            "\n".join(
                [
                    "| path | role | why_relevant | must_use_downstream | limitations |",
                    "| --- | --- | --- | --- | --- |",
                    f"| `{rel(clarification)}` | `approved-clarification` | Approved answers for columns `О`/`Р`, DaData suggestions, UI calibration routing, spaces, dictionary default. sha256 `{sha256(clarification)}` | `yes` | Only exact answered `CLR-003`, `CLR-005`-`CLR-008`; does not expand scope. |",
                    f"| `{rel(dictionaries)}` | `support-dictionary-file` | Values for FT-referenced dictionaries `Пол клиента` and `Тип документа`. sha256 `{sha256(dictionaries)}` | `yes` | Values only; no default/closed-set behavior unless supported by FT/clarification. |",
                    f"| `{rel(mockup2)}` | `mockup` | Application card minimum-state visual context and personal-data placement. sha256 `{sha256(mockup2)}` | `yes` | Visual hints only; mockup-selected gender is not a default because `CLR-008` says no default. |",
                    f"| `{rel(mockup4)}` | `mockup` | Document recognition popup controls. sha256 `{sha256(mockup4)}` | `yes` | Visual hints only; close/trash/add-document controls are mockup-only unless backed by FT. |",
                    f"| `{rel(mockup5)}` | `mockup` | Application card maximum-state visual context and conditional previous-FIO placement. sha256 `{sha256(mockup5)}` | `yes` | Visual hints only; not a business-rule source. |",
                    f"| `{rel(FT_ROOT / 'AGENT-NOTES.md')}` | `package-notes` | Package-specific notes check. | `no` | File absent. |",
                ]
            ),
        ),
        (
            2,
            "Source Quality",
            "\n".join(
                [
                    "- `active source documents`: `source/PostFinal-v2.docx`; `source/PostFinal-v2.xhtml`; `source/PostFinal-v2.pdf`",
                    "- `parseability`: DOCX container readable; XHTML XML parsed; PDF text extracted for pages 16-18.",
                    "- `section-id confidence`: DOCX resolver uses generated section ids; this scope uses XHTML/PDF anchors `4.3`, `Таблица 4`, rows 2-15 and BSR 43-83.",
                    "- `oversized blocks`: selected source is from bounded context; avoid one-shot console extraction for large XHTML.",
                    "- `strict warnings`: DOCX plain XML extraction loses BSR marker text; parity preserves BSR ids from XHTML and PDF.",
                ]
            ),
        ),
        (
            2,
            "Ambiguity And Decision Log",
            "\n".join(
                [
                    "| candidate | issue | required_decision |",
                    "| --- | --- | --- |",
                    "| `SCOPE-OPTION-002` | User selected the candidate scope. | Confirmed as `application-card-personal-data-and-recognition`. |",
                    "| `work/stage-handoffs/03-application-card-personal-data-and-recognition/` | Prior artifacts exist for same logical scope. | Not used as requirement evidence; new handoff `06-*` is current independent run. |",
                    "| `support/application-card-personal-data-and-recognition-approved-clarifications.md` | Approved clarification source came from prior normalized BA answers. | Use only exact answered rows with authority `analyst`; keep unresolved branches as gaps. |",
                    "| `prepared-bounded-context.json` | Reused hash-bound cache, but template does not register approved clarification as compiler-v3 evidence. | Do not create `source-assertions.json` from this context; route to gap review / future rematerialization. |",
                ]
            ),
        ),
        (
            2,
            "Handoff",
            "\n".join(
                [
                    "- `next_skill`: `ft-test-case-reviewer`",
                    "- `reviewer_mode`: `scope_gap_review`",
                    "- `required_inputs`: see `workflow-state.yaml`.",
                    "- `latest_artifacts`: see `workflow-state.yaml`.",
                    "- `blocked_reasons`: no blocker for gap-review handoff; writer/production is blocked by open recognition/file gaps until clarified, accepted as residual risk, or explicitly scoped out.",
                ]
            ),
        ),
    ]
    write_md("source-selection.md", "Source Selection", sections)


def make_scope_contract() -> None:
    sections = [
        (
            2,
            "Контекст",
            "\n".join(
                [
                    "- FT-пакет: `fts/AutoFin/PostFinal-v2`",
                    "- Основной FT DOCX: `source/PostFinal-v2.docx`",
                    "- Main FT XHTML: `source/PostFinal-v2.xhtml`",
                    "- XHTML extraction notes: `primary source for Table 4 rows/lists/BSR anchors; bounded context has 41 rows including context and explicit out-of-scope boundary`",
                    "- PDF для structural cross-check: `есть`, страницы `16-18`",
                    "- `AGENT-NOTES.md`: `нет`",
                    "- Scope выбран пользователем: `application-card-personal-data-and-recognition (SCOPE-OPTION-002)`",
                    "- Lean eligibility: `no`; source rows `41` > limit `12`, heterogeneous integrations present, standard/legacy handoff required.",
                ]
            ),
        ),
        (
            2,
            "Scope Identity",
            "\n".join(
                [
                    "- `scope_slug`: `application-card-personal-data-and-recognition`",
                    "- Рабочее название: Карточка `Заявка`: краткая информация, персональные данные и распознавание документа",
                    "- `source_path`: `4.3`, `Таблица 4`, rows `2-15`, `BSR 43-83`",
                    "- Режим получения: `agent-proposed-scope -> confirmed manual-scope`",
                    "- Handoff dir: `work/stage-handoffs/06-application-card-personal-data-and-recognition/`",
                ]
            ),
        ),
        (
            2,
            "Что Входит В Scope",
            "\n".join(
                [
                    "- `SRC-027`-`SRC-028`: виджет краткой информации с калькулятора и кнопка/переход к кредитному калькулятору только в пределах `BSR 43-46`.",
                    "- `SRC-029`-`SRC-039`: блок `Персональные данные`, ФИО, ID клиента, `Пол`, `Дата рождения`, признак `Клиент менял ФИО`, предыдущие ФИО и условная обязательность хотя бы одного предыдущего ФИО.",
                    "- `SRC-040`: действие `Распознать документ`, popup, поле `Тип документа`, контейнер вложений, кнопки `Отменить`/`Распознать`, no-file warning and source-stated recognition request.",
                    "- Применимые context rows: priority of FT text over mockup, text/date/list/default constraints, dictionary values only for referenced dictionaries.",
                    "- Mockup visual inventory: `work/stage-handoffs/06-application-card-personal-data-and-recognition/mockup-visual-inventory.md`.",
                ]
            ),
        ),
        (
            2,
            "Что Не Входит В Scope",
            "\n".join(
                [
                    "- `SRC-041` and all passport block rows beginning after selected range.",
                    "- Full requirements of external FT `Калькулятор`; only local open/navigate actions are retained.",
                    "- Generic widget behavior from `Описание базовых возможностей интерфейсных виджетов FIS Platform` unless repeated in local BSR.",
                    "- Passport/current/previous passport, addresses, contacts, documents-by-application, participants, employment, visual assessment, consents/checks and general actions `Далее` / `Вернуть в общий список`.",
                    "- Unstated DaData/ABS/recognition retries, timeouts, errors, backend state, persistence and field mapping.",
                    "- Mockup-only controls and default-looking selected values when they conflict with FT/support.",
                ]
            ),
        ),
        (
            2,
            "Разрешенные Источники",
            "\n".join(
                [
                    "| source | type | usage_rule |",
                    "| --- | --- | --- |",
                    "| `source/PostFinal-v2.docx` | `main-ft-docx` | Authoritative source of truth for semantics. |",
                    "| `source/PostFinal-v2.xhtml` | `main-ft-xhtml` | Mandatory row/list/table extraction and source-row inventory. |",
                    "| `source/PostFinal-v2.pdf` | `pdf` | Structural/visual parity only, especially BSR ids and pages 16-18. |",
                    "| `support/application-card-personal-data-and-recognition-approved-clarifications.md` | `approved-clarification` | Exact answered `CLR-003`, `CLR-005`-`CLR-008`; unresolved branches stay gaps. |",
                    "| `support/АФБ справочники 26.06.26.md` | `support` | Values for `Пол клиента` and `Тип документа` only. |",
                    "| `mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg` | `mockup` | Visual placement and interaction hints only. |",
                    "| `mockups/Рисунок 4 Макет всплывающего окна Распознание документов.jpg` | `mockup` | Visual popup controls and interaction hints only. |",
                    "| `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | `mockup` | Visual placement and conditional previous-FIO hints only. |",
                ]
            ),
        ),
        (
            2,
            "Scope Complexity Assessment",
            "\n".join(
                [
                    "| factor | value | risk | note |",
                    "| --- | --- | --- | --- |",
                    "| fields_or_blocks | `14 scope-local rows plus 27 context/boundary rows` | `medium` | Small UI block but source-first registry is 41 rows. |",
                    "| conditional_dependencies | `previous-FIO visible/required when client changed FIO = yes; DaData suggestion/update; recognition if files exist` | `high` | Several conditions affect expected result. |",
                    "| validation_domains | `text symbols; length; date-time; requiredness; dictionary values; file attachment presence` | `high` | Exact UI rejection mechanism mostly not source-backed. |",
                    "| action_flows | `calculator widget/button; recognize document popup; cancel; recognize no-file/with-file` | `medium` | Recognition positive branch has unresolved observation/mapping. |",
                    "| integrations_api_async | `DaData; ABS; recognition service; external calculator FT` | `high` | Only local, observable requirements are in scope. |",
                    "| status_lifecycle | `none` | `low` | No status transitions in selected rows. |",
                    "| expected_gaps_or_unclear | `8 gaps; 3 blocking for recognition/file-positive branch` | `high` | Requires pre-writer gap review. |",
                    "",
                    "Complexity decision:",
                    "",
                    "- `single_scope_with_internal_packages`",
                    "- Обоснование: пользователь подтвердил contiguous bounded fragment Table 4 rows 2-15; external split не нужен, но writer должен идти package-by-package.",
                ]
            ),
        ),
        (
            2,
            "Внутренние Рабочие Пакеты",
            "\n".join(
                [
                    "| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    "| `WP-01` | calculator summary and entrypoints | `SRC-027`-`SRC-028` | `BSR 43-46` | `field-property coverage; scenario-use-case; cross-ft dependency gate` | visible summary/action obligations and explicit calculator external gap | `no` |",
                    "| `WP-02` | personal data fields and conditional previous-FIO branch | `SRC-029`-`SRC-039`; applicable context `SRC-001`-`SRC-015`, `SRC-017` | `BSR 47-77`; `CLR-003`, `CLR-005`-`CLR-008`; `DICT-001` | `field-property coverage; equivalence-boundary; dependency matrix; requiredness/negative oracle inventory` | field/display/editability/requiredness/validation candidate obligations | `no` |",
                    "| `WP-03` | document recognition popup and file-presence flow | `SRC-040`; applicable context `SRC-011`-`SRC-012`; `DICT-002`; mockup Figure 4 | `BSR 78-83`; `DICT-002` | `scenario-use-case; decision table; integration artifact gate; file-upload boundary` | popup/action/no-file warning coverage and blocking recognition integration gaps | `no` |",
                ]
            ),
        ),
        (
            2,
            "Целевые Артефакты",
            "\n".join(
                [
                    "- Канонический файл тест-кейсов: `test-cases/4.3-application-card-personal-data-and-recognition.md`",
                    "- Handoff-папка: `work/stage-handoffs/06-application-card-personal-data-and-recognition/`",
                    "- Review-cycle папка: `work/review-cycles/application-card-personal-data-and-recognition/`",
                ]
            ),
        ),
        (
            2,
            "Условия Старта Следующего Этапа",
            "\n".join(
                [
                    "- Активный следующий этап: `ft-test-case-reviewer` в режиме `scope_gap_review`, потому что есть `GAP-*`.",
                    "- Writer/iteration не должны стартовать до проверки `scope-coverage-gaps.md` и явного решения по blocking gaps `GAP-001`-`GAP-003`.",
                    "- Если gap review passed и blocking gaps остаются open без accepted risk, workflow должен остаться `blocked-input` для writer.",
                    "- Для production/promotion-capable source-first run нужно rematerialize compiler-v3 source assertions with approved clarification binding; текущий handoff не содержит `source-assertions.json`.",
                    "- Downstream must use `source-row-inventory.md`, `source-parity-check.md`, `dictionary-inventory.md`, `negative-oracle-inventory.md`, `requiredness-oracle-inventory.md` and `mockup-visual-inventory.md` before any writer package plan.",
                ]
            ),
        ),
        (
            2,
            "Ограничения И Правила Интерпретации",
            "\n".join(
                [
                    "- Не расширять scope за `BSR 43-83` и selected context rows.",
                    "- Приоритет: DOCX text semantics > XHTML extraction > PDF structural parity > support clarification > mockup visual hints.",
                    "- Макеты не задают business rules, mandatory/default values, validation, allowed values or expected results.",
                    "- `О` means requiredness and `Р` means editability only because `CLR-003` confirms it.",
                    "- Candidate UI-calibration obligations must preserve source-backed checks without inventing exact messages, colors, filtering, save blocking or backend behavior.",
                ]
            ),
        ),
    ]
    write_md("scope-contract.md", "Scope Contract", sections)


def make_source_parity() -> None:
    parity_rows = CONTEXT["parity"]
    req_lines = ["| req_id | docx_ref | pdf_ref | status | source_decision | note |", "| --- | --- | --- | --- | --- | --- |"]
    for item in parity_rows:
        req_lines.append(
            f"| `{item['requirement_code']}` | `{esc(item['docx_locator'])}` | `{esc(item['pdf_locator'])}` | `{item['status']}` | `mandatory-req-id` | Preserve exact BSR id in downstream traceability. |"
        )

    table_lines = ["| row_anchor | docx_ref | pdf_ref | docx_text | pdf_text | status | action |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for row_id in [f"SRC-{i:03d}" for i in range(27, 41)]:
        row = ROW_BY_ID[row_id]
        row_codes = codes(row)
        pdf_pages = sorted({next((p["pdf_locator"] for p in parity_rows if p["requirement_code"] == code), "-") for code in row_codes}) if row_codes else ["-"]
        table_lines.append(
            f"| `{row_id}` / `{esc(row['field_or_action'])}` | `{esc('Table 4/Table extractor row for ' + row['field_or_action'])}` | `{esc('; '.join(pdf_pages))}` | `{esc(row['bounded_source_text'][:260])}` | `{esc('; '.join(row_codes) or 'no BSR code')}` | `match` | `use` |"
        )

    sections = [
        (
            2,
            "Source Parity Check",
            "\n".join(
                [
                    "- FT package: `fts/AutoFin/PostFinal-v2`",
                    "- Scope: `application-card-personal-data-and-recognition`",
                    "- DOCX source: `source/PostFinal-v2.docx`",
                    "- XHTML source: `source/PostFinal-v2.xhtml`",
                    "- PDF source: `source/PostFinal-v2.pdf`",
                    "- DOCX extraction: `DOCX XML text scan + bounded context evidence`",
                    "- XHTML extraction: `source-row-extraction-spec.json` / `source-row-baseline.json`",
                    "- PDF extraction: `pypdf page text search in one-pass fallback`",
                    "- DOCX scope refs: `4.3`, `Таблица 4`, rows `2-15`; DOCX plain XML contains selected source text but not visible BSR markers.",
                    "- PDF scope refs: pages `16-18`.",
                ]
            ),
        ),
        (
            2,
            "Boundary Parity",
            "\n".join(
                [
                    "| item | docx_ref | pdf_ref | status | note |",
                    "| --- | --- | --- | --- | --- |",
                    "| `4.3 / Карточка Заявка / Table 4 start` | DOCX contains title and selected rows | PDF page 16 | `match` | Table title and selected block start confirmed. |",
                    "| `scope start: Краткая информация с калькулятора` | DOCX selected text found | PDF page 16 / BSR 43 | `match` | Start row confirmed. |",
                    "| `scope end: Распознать документ / BSR 83` | DOCX selected text found | PDF page 18 / BSR 83 | `match` | End row confirmed. |",
                    "| `next boundary: Блок Паспортные данные` | DOCX selected text after BSR83 | PDF page 18 / BSR 84 | `match` | Boundary excluded from current scope. |",
                    "| `requirement-code extraction in DOCX plain XML` | direct `BSR 43` string search returns 0/41 | XHTML/PDF contain all BSR 43-83 | `extraction-risk` | Use XHTML/PDF for ids; DOCX remains semantic source. |",
                ]
            ),
        ),
        (2, "Requirement Id Inventory", "\n".join(req_lines)),
        (2, "Table / Row Parity", "\n".join(table_lines)),
        (
            2,
            "Mandatory Traceability Inputs",
            "\n".join(
                [
                    "- Requirement IDs to preserve: `BSR 43`-`BSR 83`.",
                    "- PDF-only IDs to preserve: `none`.",
                    "- DOCX-only IDs to preserve: `none`.",
                    "- Semantic mismatches requiring gaps: `none` between DOCX/XHTML/PDF; behavioral gaps are due to missing integration/file/UI oracle details, not parity mismatch.",
                ]
            ),
        ),
        (
            2,
            "Decision",
            "\n".join(
                [
                    "- Scope parity status: `pass-with-extraction-risk`",
                    "- Writer/reviewer rule: preserve all BSR ids from XHTML/PDF parity; do not use DOCX plain XML absence of BSR markers to drop requirement ids.",
                    "- Open gaps/questions: `GAP-001`-`GAP-008`.",
                ]
            ),
        ),
    ]
    write_md("source-parity-check.md", "Source Parity Check", sections)


def row_package(row_id: str) -> str:
    n = int(row_id.split("-")[1])
    if n in (27, 28):
        return "WP-01"
    if n == 40 or n in (11, 12):
        return "WP-03"
    return "WP-02"


def row_mapping(row_id: str, in_scope: str) -> str:
    if in_scope == "no":
        return "out-of-scope:explicit context/boundary row retained for attestation"
    atom_num = int(row_id.split("-")[1])
    mapping = [f"planned:ATOM-{atom_num:03d}"]
    extra = {
        "SRC-016": ["GAP-008"],
        "SRC-027": ["GAP-007"],
        "SRC-028": ["GAP-007"],
        "SRC-030": ["GAP-004", "GAP-005"],
        "SRC-031": ["GAP-004", "GAP-005"],
        "SRC-032": ["GAP-004", "GAP-005"],
        "SRC-034": ["GAP-004", "GAP-006"],
        "SRC-035": ["GAP-005"],
        "SRC-037": ["GAP-004", "GAP-005"],
        "SRC-038": ["GAP-004", "GAP-005"],
        "SRC-039": ["GAP-004", "GAP-005"],
        "SRC-040": ["GAP-001", "GAP-002", "GAP-003", "GAP-006"],
    }.get(row_id, [])
    mapping.extend(extra)
    return "; ".join(mapping)


def make_source_row_inventory() -> None:
    lines = [
        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap | source_path | source_locator | bounded_source_text | source_context_class | candidate_id |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in ROWS:
        row_id = row["source_row_id"]
        hint = str(row.get("in_scope_hint", "")).lower()
        in_scope = "yes" if hint.startswith("yes") else "no" if hint.startswith("no") else "unclear"
        code_text = "; ".join(codes(row)) or "none_required"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row_id}`",
                    f"`{row_package(row_id)}`",
                    esc(row.get("field_or_action", "")),
                    f"`{esc(row.get('source_ref', ''))}`",
                    esc(code_text),
                    f"`{in_scope}`",
                    esc(row_mapping(row_id, in_scope)),
                    f"`{esc(row.get('source_path', ''))}`",
                    f"`{esc(row.get('source_locator', ''))}`",
                    esc(row.get("bounded_source_text", "")),
                    f"`{esc(row.get('source_context_class', ''))}`",
                    f"`{esc(row.get('candidate_id', '') or 'null')}`",
                ]
            )
            + " |"
        )

    sections = [
        (
            2,
            "Контекст",
            "\n".join(
                [
                    "- Scope: `application-card-personal-data-and-recognition`.",
                    "- Prepared context: `prepared-bounded-context.json`.",
                    "- Extraction spec: `source-row-extraction-spec.json`.",
                    "- Baseline: `source-row-baseline.json`.",
                    "- `source_rows_total`: `41`.",
                    "- `scope_local_rows`: `SRC-027`-`SRC-040`.",
                ]
            ),
        ),
        (2, "Source Row Inventory", "\n".join(lines)),
        (
            2,
            "Normalization Handoff Notes",
            "\n".join(
                [
                    "- Writer must create writer-side `Source Table Normalization` before ledger.",
                    "- Rows with multiple BSR codes must be decomposed through `Source Row Completeness Matrix`.",
                    "- `mapped_atom_or_gap` values with `planned:ATOM-*` are scope-stage placeholders; writer owns final atomic IDs.",
                    "- `GAP-001`-`GAP-003` block complete recognition positive branch until clarified or accepted as residual risk.",
                ]
            ),
        ),
    ]
    write_md("source-row-inventory.md", "Source Row Inventory Handoff", sections)


def make_dictionary_inventory() -> None:
    sections = [
        (
            2,
            "Контекст",
            "\n".join(
                [
                    "- Scope: `application-card-personal-data-and-recognition`.",
                    "- Source: `support/АФБ справочники 26.06.26.md`.",
                    "- Extracted dictionaries: `Пол`; `Тип документа`.",
                    "- Active means `Архивный = нет` in support table.",
                ]
            ),
        ),
        (
            2,
            "Dictionary Inventory",
            "\n".join(
                [
                    "| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| `DICT-001` | `Пол` / FT name `Пол клиента` | `support/АФБ справочники 26.06.26.md` | heading `## Пол`; columns `Значение`, `Внутренний код`, `Архивный` | `extracted` | `Мужчина`; `Женщина` | `-` | `SRC-034` | `GAP-006` | Active values extracted; `CLR-008` says no default; closed-set/no-extra-values not confirmed. |",
                    "| `DICT-002` | `Тип документа` / FT name `типы документов` | `support/АФБ справочники 26.06.26.md` | heading `## Тип документа`; columns `Значение`, `Внутренний код`, `Архивный` | `extracted` | `ВУ`; `СНИЛС`; `Загран. паспорт`; `Паспорт`; `Анкета` | `-` | `SRC-040` | `GAP-006` | Active values extracted; `CLR-008` says no default; closed-set/no-extra-values not confirmed. |",
                ]
            ),
        ),
        (
            2,
            "Writer Handoff Rules",
            "\n".join(
                [
                    "- Writer must reference `DICT-001` and `DICT-002` when using dictionary values.",
                    "- Do not assert absence of any value outside the extracted list unless `GAP-006` is resolved.",
                    "- Do not use mockup-selected `Мужской` or `Паспорт` as default values; `CLR-008` says no default.",
                ]
            ),
        ),
    ]
    write_md("dictionary-inventory.md", "Dictionary Inventory", sections)


def make_requiredness_inventory() -> None:
    rows = [
        ("SO-REQ-001", "`SRC-030`; BSR 47; column `О=Да`", "Фамилия", "requiredness", "`О=Да` confirmed by `CLR-003`", "empty-required-field", "always"),
        ("SO-REQ-002", "`SRC-031`; BSR 50; column `О=Да`", "Имя", "requiredness", "`О=Да` confirmed by `CLR-003`", "empty-required-field", "always"),
        ("SO-REQ-003", "`SRC-034`; BSR 58; column `О=Да`; `CLR-008` no default", "Пол", "requiredness", "`О=Да` confirmed by `CLR-003`", "empty-required-field", "always"),
        ("SO-REQ-004", "`SRC-035`; BSR 60; column `О=Да`", "Дата рождения", "requiredness", "`О=Да` confirmed by `CLR-003`", "empty-required-field", "always"),
        ("SO-REQ-005", "`SRC-037`-`SRC-039`; BSR 68; BSR 72; BSR 76", "Предыдущие ФИО", "conditional-requiredness", "At least one previous-FIO field is required when `Клиент менял ФИО = Да`", "condition-true-empty", "`Клиент менял ФИО = Да`"),
    ]
    table = [
        "| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        oid, source_ref, field, rtype, source, klass, when = row
        table.append(
            f"| `{oid}` | {source_ref} | `{field}` | `{rtype}` | {source} | `{klass}` | `{when}` | `no` | `no` | `not_found` | `ui-calibration-required` | `candidate_tc_required` | `candidate:{oid}` | `GAP-005` | `Как UI проверяет пустое обязательное значение for {field}?` | Create candidate TC; do not cover requiredness through positive filled value only. | Record marker/message/highlight/transition/save effect during UI calibration. |"
        )
    sections = [
        (2, "Контекст", "- `scope_slug`: `application-card-personal-data-and-recognition`\n- `scope_contract`: `scope-contract.md`\n- `scope_coverage_gaps`: `scope-coverage-gaps.md`"),
        (2, "Requiredness Oracle Inventory", "\n".join(table)),
        (2, "Summary", "- total_requiredness_obligations: `5`\n- executable_tc: `0`\n- candidate_tc_required: `5`\n- gap_required: `0`\n- clarification_required: `0`"),
        (
            2,
            "Writer Handoff Rules",
            "\n".join(
                [
                    "- Writer must carry every `SO-REQ-*` into Source Table Normalization / Coverage Obligation Table.",
                    "- Writer must create candidate TC for `candidate_tc_required` rows and mark `Статус oracle: ui-calibration-required`.",
                    "- Writer must not invent exact marker, message, highlight or transition/save block.",
                ]
            ),
        ),
    ]
    write_md("requiredness-oracle-inventory.md", "Requiredness Oracle Inventory", sections)


def make_negative_inventory() -> None:
    text_fields = [
        ("Фамилия", "SRC-030", "BSR 48"),
        ("Имя", "SRC-031", "BSR 51"),
        ("Отчество", "SRC-032", "BSR 54"),
        ("Предыдущая фамилия", "SRC-037", "BSR 67"),
        ("Предыдущее имя", "SRC-038", "BSR 71"),
        ("Предыдущее отчество", "SRC-039", "BSR 75"),
    ]
    obligations = []
    idx = 1
    for field, src, bsr in text_fields:
        for klass, value, statement in [
            ("digits", "Иван1", "Only text symbols and `-` are allowed."),
            ("special-chars", "Иван@", "Only text symbols and `-` are allowed."),
            ("spaces", "Иван Иванов", "`CLR-007` confirms space is forbidden."),
            ("too-long", "<2001 text chars>", "Global text type allows 2000 symbols."),
        ]:
            obligations.append((f"SO-NEG-{idx:03d}", f"`{src}`; {bsr}; `SRC-005`; `CLR-007` where applicable", field, "text-symbols" if klass != "too-long" else "length", klass, statement, value, "GAP-005", "candidate_tc_required", "ui-calibration-required", "not_found"))
            idx += 1
    for klass, value, statement, bsr in [
        ("younger-than-18", "2008-07-24 when current date is 2026-07-23", "Дата не может быть позже чем <текущая дата>–18 лет.", "BSR 61"),
        ("future-date", "2026-07-24 when current date is 2026-07-23", "Дата не может быть больше чем текущая дата.", "BSR 62"),
        ("older-than-100", "1926-07-22 when current date is 2026-07-23", "Дата не может быть меньше, чем <текущая дата>–100 лет.", "BSR 63"),
    ]:
        obligations.append((f"SO-NEG-{idx:03d}", f"`SRC-035`; {bsr}", "Дата рождения", "date-validity-window", klass, statement, value, "GAP-005", "candidate_tc_required", "ui-calibration-required", "not_found"))
        idx += 1
    obligations.append((f"SO-NEG-{idx:03d}", "`SRC-040`; BSR 82", "Распознать документ", "other", "no-attachment", "If files are absent, warning must be shown.", "no attached file", "none_required:covered", "executable_tc", "source-backed", "FT"))

    table = [
        "| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for oid, source_ref, field, rtype, klass, statement, value, gap, decision, status, oracle_source in obligations:
        planned = f"candidate:{oid}" if decision == "candidate_tc_required" else "planned:TC-source-backed"
        question = "none_required" if gap.startswith("none_required") else f"Как UI отклоняет invalid class `{klass}` для `{field}`?"
        handoff = "Create candidate TC; do not invent exact UI reaction." if decision == "candidate_tc_required" else "Create executable TC with exact warning from BSR 82."
        calibration = "Record validation trigger, UI reaction, message if any, transition/save effect." if decision == "candidate_tc_required" else "Expected warning text is source-backed: `Отсутствуют файлы для распознавания`."
        table.append(
            f"| `{oid}` | {source_ref} | `{field}` | `{rtype}` | `{klass}` | {esc(statement)} | `{esc(value)}` | `{'yes' if decision == 'executable_tc' else 'no'}` | `{oracle_source}` | `{status}` | `{decision}` | `{planned}` | `{gap}` | {esc(question)} | {handoff} | {calibration} |"
        )

    sections = [
        (2, "Контекст", "- `scope_slug`: `application-card-personal-data-and-recognition`\n- `scope_contract`: `scope-contract.md`\n- `scope_coverage_gaps`: `scope-coverage-gaps.md`"),
        (2, "Negative Oracle Inventory", "\n".join(table)),
        (2, "Summary", f"- total_negative_obligations: `{len(obligations)}`\n- executable_tc: `1`\n- candidate_tc_required: `{len(obligations) - 1}`\n- gap_required: `0`\n- clarification_required: `0`"),
        (
            2,
            "Writer Handoff Rules",
            "\n".join(
                [
                    "- Writer must carry every `SO-NEG-*` into Source Table Normalization / Coverage Obligation Table.",
                    "- Candidate rows remain executable-intent obligations with `oracle_status = ui-calibration-required`.",
                    "- Do not invent exact UI filtering, message, color, clearing, save block or backend effect.",
                    "- `SO-NEG-028` for no attachment has source-backed warning text from `BSR 82`.",
                ]
            ),
        ),
    ]
    write_md("negative-oracle-inventory.md", "Negative Oracle Inventory", sections)


def make_mockup_inventory() -> None:
    mockups = [
        ("Рисунок 2", FT_ROOT / "mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg", "Анкета Клиента. Минимальное состояние", "1950x2567"),
        ("Рисунок 4", FT_ROOT / "mockups/Рисунок 4 Макет всплывающего окна Распознание документов.jpg", "Распознание документов", "1120x784"),
        ("Рисунок 5", FT_ROOT / "mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg", "Анкета Клиента. Максимальное состояние", "3840x12356"),
    ]
    meta = ["| item | value | evidence |", "| --- | --- | --- |"]
    for label, path, screen, size in mockups:
        meta.append(f"| mockup_path | `{rel(path)}` | `{label}`; sha256 `{sha256(path)}`; size `{size}` |")
        meta.append(f"| opened | `yes` | `view_image`; visual-inspection; `{NOW}` |")
        meta.append(f"| method | `visual-inspection` | Codex desktop image viewer |")
        meta.append(f"| screen_name | `{screen}` | mockup caption/source |")
        meta.append("| source_priority | `FT-over-mockup` | `AGENTS.md / scope-contract.md` |")

    sections = [
        (2, "Metadata", "\n".join(meta)),
        (
            2,
            "Visual Inventory",
            "\n".join(
                [
                    "| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |",
                    "| --- | --- | --- | --- | --- |",
                    "| `visible_blocks` | `Персональные данные` | `Блок «Персональные данные»` | `visible` | Seen in Figures 2 and 5. |",
                    "| `visible_fields` | `Фамилия`, `Имя`, `Отчество` | Current FIO fields | `visible/editable/unclear` | Mockup shows text inputs; FT defines editability. |",
                    "| `visible_fields` | `ID клиента` | `ID клиента` | `visible/readonly-looking` | FT says auto-filled after save; mockup not used for behavior. |",
                    "| `visible_fields` | `Клиент менял ФИО` | `Клиент менял ФИО` | `visible/toggle` | In mockups toggle appears on; FT default is `Нет`. |",
                    "| `visible_fields` | `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество` | Previous-FIO fields | `visible when toggle shown on` | FT condition wins. |",
                    "| `visible_fields` | `Дата рождения` | `Дата рождения` | `visible/input with calendar icon` | Calendar icon is interaction hint only. |",
                    "| `visible_fields` | `Пол`, `Мужской`, `Женский` | `Пол` | `visible/radio-like switch` | Mockup-selected `Мужской` is not a default due `CLR-008`. |",
                    "| `visible_actions` | `РАСПОЗНАТЬ ДОКУМЕНТ` | `Распознать документ` | `visible/enabled-looking` | Opens popup per BSR 79. |",
                    "| `visible_actions` | `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` | `Кредитный калькулятор` | `visible/enabled-looking` | Local open action only; external calculator details excluded. |",
                    "| `visible_blocks` | `Распознание документов` popup | Recognition popup | `visible` | Seen in Figure 4. |",
                    "| `visible_fields` | `Тип документа` | Popup `Тип документа` | `visible/dropdown` | Mockup value `Паспорт` not used as default. |",
                    "| `visible_fields` | paperclip/document row | file attachment container | `visible` | UI hint for attaching file; file constraints not defined. |",
                    "| `visible_actions` | `ОТМЕНИТЬ`, `РАСПОЗНАТЬ` | Popup buttons | `visible` | Both are FT-backed by BSR 80-82. |",
                ]
            ),
        ),
        (
            2,
            "Interaction Hints",
            "\n".join(
                [
                    "| element | interaction_hint | source | used_for_steps | limitation |",
                    "| --- | --- | --- | --- | --- |",
                    "| `Краткая информация с калькулятора` | click widget | mockup + BSR 45 | `yes` | Does not define calculator FT behavior. |",
                    "| `Кредитный калькулятор` | click button | mockup + BSR 46 | `yes` | Does not define opened window internals. |",
                    "| text fields | type into underline-style input | mockup | `yes` | FT/support define validation. |",
                    "| `Клиент менял ФИО` | toggle switch | mockup | `yes` | FT defines visibility/default. |",
                    "| `Пол` | select radio/switch value | mockup | `yes` | Dictionary/default from support, not mockup. |",
                    "| `Дата рождения` | type date or use calendar icon | mockup | `yes` | Date bounds from FT. |",
                    "| `РАСПОЗНАТЬ ДОКУМЕНТ` | click button to open modal | mockup + BSR 79 | `yes` | Modal expected behavior from FT. |",
                    "| `Тип документа` | open dropdown | mockup + BSR 79 | `yes` | Values from `DICT-002`; no default asserted. |",
                    "| attachment row/paperclip | attach file via upload/drop zone | mockup + BSR 79 | `yes` | File type/count/size unresolved. |",
                    "| `ОТМЕНИТЬ` | click cancel | mockup + BSR 81 | `yes` | Close X not FT-backed. |",
                    "| `РАСПОЗНАТЬ` | click recognize | mockup + BSR 82/83 | `yes` | Positive recognition branch blocked by gaps. |",
                ]
            ),
        ),
        (
            2,
            "Mockup-Only Items",
            "\n".join(
                [
                    "| item | mockup_observation | ft_reference | handling |",
                    "| --- | --- | --- | --- |",
                    "| close `X` on popup | visible in Figure 4 | not listed in BSR 80 | `ignore-out-of-scope` unless separately confirmed. |",
                    "| trash icon in popup document card | visible in Figure 4 | not listed in BSR 79-83 | `ignore-out-of-scope` for current scope. |",
                    "| `ДОБАВИТЬ ДОКУМЕНТ` in popup | visible in Figure 4 | not listed in BSR 79-83 | `ignore-out-of-scope`; file container is FT-backed, add action label is not. |",
                    "| selected `Мужской` | visible in Figures 2/5 | `CLR-008` says no default | `alias-only`; do not assert default. |",
                    "| selected `Паспорт` | visible in Figure 4 | `CLR-008` says no default | `alias-only`; do not assert default. |",
                ]
            ),
        ),
        (
            2,
            "FT Conflicts",
            "\n".join(
                [
                    "| item | ft_statement | mockup_observation | decision |",
                    "| --- | --- | --- | --- |",
                    "| `Пол` default | `CLR-008`: default absent | mockup visually shows `Мужской` selected | `FT/support wins`; no default TC from mockup. |",
                    "| `Тип документа` default | `CLR-008`: default absent | popup visually shows `Паспорт` selected | `FT/support wins`; no default TC from mockup. |",
                    "| popup close/delete/add controls | BSR 80 lists only `Отменить` and `Распознать`; BSR 79 says container for files | mockup shows extra controls | `ignore-out-of-scope`; may be separate future clarification if needed. |",
                ]
            ),
        ),
        (
            2,
            "Usage Decision",
            "\n".join(
                [
                    "| item | value | evidence |",
                    "| --- | --- | --- |",
                    "| schema_terms | `interaction_hints`; `mockup_only_items`; `ft_conflicts` | Literal validator terms for canonical sections above. |",
                    "| used_for_steps | `yes` | Interaction hints above. |",
                    "| not_used_as_requirement_source | `yes` | Mockup refines interaction only; FT/support define behavior. |",
                    "| open_questions | `GAP-003`; `GAP-006` | File constraints and closed-set semantics remain source gaps. |",
                ]
            ),
        ),
    ]
    write_md("mockup-visual-inventory.md", "Mockup Visual Inventory", sections)


def gap_block(gap_id: str, ref: str, source_path: str, source_statement: str, gap_type: str, description: str, impact: str, coverage_impact: str, dimension: str, risk: str, question: str, temporary: str, writer_rule: str, reviewer_rule: str, needs_input: str, obligations: str = "not_applicable", blocked_classes: str = "not_applicable", missing_oracle: str = "not_applicable", why_not_exec: str = "not_applicable", downstream_do_not_test: str = "not_applicable") -> str:
    blocks = "yes" if impact == "blocking" else "no"
    return "\n".join(
        [
            f"### {gap_id}",
            f"**FT Reference:** `{ref}`",
            f"**Source Path:** `{source_path}`",
            "**Related Atomic Statement(s):** `not-yet-assigned`",
            f"**Source Statement:** {source_statement}",
            f"**Gap Type:** `{gap_type}`",
            f"**Description:** {description}",
            f"**Impact:** `{impact}`",
            f"**Coverage Impact:** `{coverage_impact}`",
            "**Affected Atom ID:** `not-yet-assigned`",
            f"**Missing Behavior:** {description}",
            "**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.",
            f"**Affected Test-design Dimension:** `{dimension}`",
            f"**Scope Obligation ID(s):** `{obligations}`",
            f"**Blocked Negative Classes:** `{blocked_classes}`",
            f"**Missing Observable Oracle:** `{missing_oracle}`",
            f"**Why Not Executable:** {why_not_exec}",
            f"**Downstream Do Not Test:** {downstream_do_not_test}",
            f"**Risk:** `{risk}`",
            f"**Blocks Ready For Review:** `{blocks}`",
            f"**Question To Analyst:** {question}",
            f"**Temporary Handling:** {temporary}",
            f"**Writer Rule:** {writer_rule}",
            f"**Reviewer Rule:** {reviewer_rule}",
            f"**Needs User Input:** `{needs_input}`",
            "**Status:** `open`",
        ]
    )


def make_gaps() -> None:
    gaps = [
        gap_block(
            "GAP-001",
            "4.3 / Таблица 4 / row 15 / BSR 83 / recognition request and wait",
            row_ref("SRC-040"),
            "`BSR 83`: if files exist, the system sends a request to recognition, waits and fills application fields.",
            "missing-observation-interface",
            "No authorized observable interface is defined for proving the recognition request, wait completion and service result.",
            "blocking",
            "partial",
            "integration",
            "high",
            "Каким разрешённым способом тестировщик должен подтвердить запрос в систему распознавания, ожидание и завершение результата?",
            "Cover popup opening/cancel/no-file warning; keep positive recognition integration branch blocked.",
            "Do not create executable TC for request/wait/fill unless an observable artifact is provided.",
            "Verify that BSR 83 remains blocking or is explicitly accepted/deferred; do not allow backend assumptions.",
            "yes",
            missing_oracle="request log / visible status / callback artifact / filled-field evidence",
            why_not_exec="The source names an integration effect but does not define a tester-observable artifact.",
            downstream_do_not_test="Do not assert that request was sent or wait completed without observable evidence.",
        ),
        gap_block(
            "GAP-002",
            "4.3 / Таблица 4 / row 15 / BSR 83 / `соответствующие поля Заявки`",
            row_ref("SRC-040"),
            "`BSR 83`: recognition result fills corresponding application fields.",
            "missing-rule",
            "Exact mapping from recognition result attributes to application fields is not defined.",
            "blocking",
            "uncovered",
            "integration",
            "high",
            "Какие поля заявки должны заполняться после успешного распознавания и по каким видимым признакам тестировщик должен понять, что распознавание прошло успешно?",
            "Do not verify field-filling after recognition; only retain it as open coverage.",
            "Do not invent field mapping from document type or mockup labels.",
            "Check that no downstream TC claims recognition-filled fields without source mapping.",
            "yes",
            missing_oracle="field mapping and success state",
            why_not_exec="There is no source-backed target field list or expected values.",
            downstream_do_not_test="Do not test auto-fill of unspecified application fields.",
        ),
        gap_block(
            "GAP-003",
            "4.3 / Таблица 4 / row 15 / BSR 79; BSR 82; BSR 83 / file attachment container",
            row_ref("SRC-040"),
            "`BSR 79`: container for files with drag & drop; `BSR 82`: no-file warning; `BSR 83`: if files exist, recognition starts.",
            "missing-constraint",
            "Allowed file types, count, size and stable positive fixture for recognition are not defined.",
            "blocking",
            "partial",
            "file-upload",
            "medium",
            "Какие файлы можно использовать для успешного распознавания, включая формат, количество, максимальный размер и пример тестового файла?",
            "Cover source-backed no-file warning; do not test invalid file type/size/count or positive recognition with arbitrary file.",
            "Use exact no-file warning only; block positive recognition file branch until fixture constraints are source-backed.",
            "Ensure writer does not choose arbitrary files or invent upload validation.",
            "yes",
            missing_oracle="allowed file classes and valid fixture",
            why_not_exec="A stable positive file fixture cannot be derived from BSR 79-83.",
            downstream_do_not_test="Do not test unsupported file classes or arbitrary successful recognition upload.",
        ),
        gap_block(
            "GAP-004",
            "4.3 / Таблица 4 / BSR 49; 52; 55; 59; 69; 73; 77 / DaData",
            "`SRC-030`; `SRC-031`; `SRC-032`; `SRC-034`; `SRC-037`; `SRC-038`; `SRC-039`",
            "`CLR-005` confirms suggestion list appears on partial input when matching values exist in DaData.",
            "missing-rule",
            "Selection effect, no-match behavior and DaData service error behavior are not defined.",
            "non-blocking",
            "design-constraint-on-covered-atom",
            "integration",
            "medium",
            "Что происходит после выбора подсказки, при отсутствии совпадений и при ошибке DaData?",
            "Cover only display of suitable suggestions when values exist; exclude no-match/error/selection branches.",
            "Do not invent DaData fallback, error message, selection side effects or retry behavior.",
            "Check DaData branches are limited to approved `CLR-005` trigger/display behavior.",
            "yes",
        ),
        gap_block(
            "GAP-005",
            "4.3 / Таблица 4 / validation and requiredness rows; `CLR-006`; `CLR-007`",
            "`SRC-030`-`SRC-039`; requiredness/negative oracle inventories",
            "`CLR-006`: exact UI reaction must be clarified during UI research; `CLR-007`: spaces are forbidden.",
            "missing-rule",
            "Exact UI rejection/requiredness mechanism is not source-backed for invalid or empty required values.",
            "non-blocking",
            "design-constraint-on-covered-atom",
            "expected-result",
            "medium",
            "`none_required`: вопрос БА сейчас не требуется; `CLR-006` уже переносит точную реакцию UI на UI-калибровку.",
            "Preserve all `SO-NEG-*` and `SO-REQ-*` rows as `candidate_tc_required` with `ui-calibration-required`.",
            "Create candidate UI-calibration TC; do not invent exact message/filtering/highlight/save block.",
            "Verify child obligations are not hidden inside this parent gap.",
            "no",
            obligations="SO-NEG-001..SO-NEG-027; SO-REQ-001..SO-REQ-005",
            blocked_classes="digits; special-chars; spaces; too-long; younger-than-18; future-date; older-than-100; empty-required-field; condition-true-empty",
            missing_oracle="exact message / red highlight / blocked transition / input filtering / visible marker",
            why_not_exec="Candidate TC can be formed, but exact UI reaction is pending UI calibration.",
            downstream_do_not_test="Do not create fully executable negative/requiredness TC without calibration evidence.",
        ),
        gap_block(
            "GAP-006",
            "4.3 / Таблица 4 / BSR 58; BSR 79 / dictionaries `Пол клиента`, `типы документов`",
            "`SRC-034`; `SRC-040`; `support/АФБ справочники 26.06.26.md`; `CLR-008`",
            "`CLR-008` confirms no default; dictionary values are extracted from support.",
            "missing-rule",
            "Closed-set/no-extra-values semantics are not confirmed for extracted dictionaries.",
            "non-blocking",
            "design-constraint-on-covered-atom",
            "table-list",
            "low",
            "Можно ли в полях `Пол` и `Тип документа` выбрать только значения из справочников, или допускаются другие значения?",
            "Use extracted active values and no-default semantics; do not assert absence of extra values.",
            "Reference `DICT-001`/`DICT-002`; do not write closed-set rejection checks.",
            "Verify dictionary inventory is used and closed-set claim is not invented.",
            "yes",
        ),
        gap_block(
            "GAP-007",
            "4.3 / Таблица 4 / rows 2-3 / BSR 43-46 / external FT `Калькулятор`",
            "`SRC-027`; `SRC-028`",
            "Selected rows refer to requirements for `Кредитный калькулятор` in a separate FT.",
            "cross-ft-dependency",
            "Calculator calculation/content behavior is outside the current source package.",
            "non-blocking",
            "design-constraint-on-covered-atom",
            "scope",
            "low",
            "`none_required`: вопрос БА не требуется, если требования к калькулятору не добавляются как источник текущего scope.",
            "Cover only visible summary content listed in BSR 44 and local click/open actions BSR 45-46.",
            "Do not test calculator calculations, validations or internal window behavior.",
            "Check current scope does not import external calculator rules.",
            "no",
        ),
        gap_block(
            "GAP-008",
            "Section 3 / external widget document `Описание базовых возможностей интерфейсных виджетов FIS Platform`",
            "`SRC-016`",
            "Main FT says base widget behavior is described in external FIS Platform documentation.",
            "cross-ft-dependency",
            "Generic widget capabilities are not available as a source in this run.",
            "non-blocking",
            "design-constraint-on-covered-atom",
            "scope",
            "low",
            "`none_required`: вопрос БА не требуется, если спецификация виджетов не добавляется как источник текущего scope.",
            "Use only local BSR behavior and mockup interaction hints.",
            "Do not test generic widget behavior not restated in BSR 43-83.",
            "Check writer does not import external widget rules by assumption.",
            "no",
        ),
    ]
    sections = [
        (2, "Контекст", "- `scope_slug`: `application-card-personal-data-and-recognition`\n- Основной FT: `source/PostFinal-v2.docx`\n- Handoff: `work/stage-handoffs/06-application-card-personal-data-and-recognition/`"),
        (2, "Summary", "- Найдено gaps: `8`\n- Есть blocking gaps: `yes` (`GAP-001`-`GAP-003`)\n- Writing можно стартовать: `no`, пока blocking gaps не закрыты, не приняты как residual risk или не исключены явным scope decision.\n- Pre-writer gap review можно стартовать: `yes`"),
        (2, "Coverage Gaps", "\n\n".join(gaps)),
        (
            2,
            "Что Можно Покрывать Несмотря На Gaps",
            "\n".join(
                [
                    "- Field visibility/editability/default/requiredness source-backed obligations for BSR 43-82, with candidate UI calibration where exact UI reaction is absent.",
                    "- No-file warning for `BSR 82` with exact text `Отсутствуют файлы для распознавания`.",
                    "- Dictionary active values from `DICT-001`/`DICT-002` and absence of default per `CLR-008`.",
                    "- DaData suggestion display only under `CLR-005` condition: matching values exist and partial input is entered.",
                ]
            ),
        ),
        (
            2,
            "Что Нельзя Домысливать",
            "\n".join(
                [
                    "- Recognition request logs, waiting state, field mapping, successful filling and backend effects.",
                    "- Allowed file types/count/size and invalid upload behavior.",
                    "- DaData no-match/error/selection side effects.",
                    "- Exact validation/requiredness message, color, filtering, clearing, blocked transition or save/no-save effect.",
                    "- Closed-set/no-extra-values semantics for dictionaries.",
                    "- External calculator or generic widget behavior.",
                ]
            ),
        ),
        (
            2,
            "Требуемые Уточнения",
            "- See `scope-clarification-requests.md` for open questions linked to `GAP-001`-`GAP-004` and `GAP-006`.",
        ),
    ]
    write_md("scope-coverage-gaps.md", "Scope Coverage Gaps", sections)


def make_clarifications() -> None:
    def card(
        clarification_id: str,
        gap_id: str,
        requirement_codes: str,
        related_ft_reference: str,
        source_quote: str,
        question: str,
        needed_for: str,
        blocking: str,
    ) -> str:
        metadata = {
            "clarification_id": clarification_id,
            "gap_id": gap_id,
            "scope_slug": "application-card-personal-data-and-recognition",
            "requirement_codes": requirement_codes,
            "related_ft_reference": related_ft_reference,
            "source_quote": source_quote,
            "question": question,
            "needed_for": needed_for,
            "blocking": blocking,
            "requested_from": "analyst",
            "authority": "analyst",
            "response_status": "unanswered",
            "response_type": "not-provided",
            "updated_at": "-",
        }
        metadata_block = "\n".join(
            f"{key}: {value}" for key, value in metadata.items()
        )
        return (
            f"### {clarification_id} — {gap_id}\n\n"
            "```yaml\n"
            f"{metadata_block}\n"
            "```\n\n"
            f"**Текст из ФТ:** {source_quote}\n\n"
            f"**Вопрос:** {question}\n\n"
            f"**Что станет возможно после ответа:** {needed_for}\n\n"
            "#### Ответ БА (`user_response`)\n\n"
            "```text\n"
            "-\n"
            "```"
        )

    requests = [
        card(
            "CLR-011",
            "GAP-001",
            "BSR 83",
            "4.3, table 4 row 15, recognition request/wait",
            "BSR 83. Если имеются файлы для распознавания, то выполняется запрос в систему распознавания (интеграция со сторонней системой), ожидание распознавания и заполнения соответствующих полей Заявки.",
            "Каким разрешённым способом тестировщик должен подтвердить запрос в систему распознавания, ожидание и завершение результата?",
            "Понять, как проверять выполнение требования BSR 83 в тесте.",
            "yes",
        ),
        card(
            "CLR-012",
            "GAP-002",
            "BSR 83",
            "4.3, table 4 row 15, corresponding application fields",
            "BSR 83. Если имеются файлы для распознавания, то выполняется запрос в систему распознавания (интеграция со сторонней системой), ожидание распознавания и заполнения соответствующих полей Заявки.",
            "Какие поля заявки должны заполняться после успешного распознавания и по каким видимым признакам тестировщик должен понять, что распознавание прошло успешно?",
            "Понять, какие поля и ожидаемый результат проверять в тестах распознавания.",
            "yes",
        ),
        card(
            "CLR-013",
            "GAP-003",
            "BSR 79; BSR 82; BSR 83",
            "4.3, table 4 row 15, file container",
            "BSR 79. Открывает всплывающее окно, в котором имеется поле (раскрывающийся список) «Тип документа» (значения по справочнику типов документов) и контейнер для прикрепления файлов с drag & drop, предназначенных для распознавания. BSR 82. При нажатии кнопки «Распознать» выполняется проверка наличия вложения в контейнере для файлов. Если файлы отсутствуют, выдается предупреждение: «Отсутствуют файлы для распознавания». BSR 83. Если имеются файлы для распознавания, то выполняется запрос в систему распознавания.",
            "Какие файлы можно использовать для успешного распознавания, включая формат, количество, максимальный размер и пример тестового файла?",
            "Подобрать корректные тестовые файлы и границы загрузки для сценария с распознаванием.",
            "yes",
        ),
        card(
            "CLR-014",
            "GAP-004",
            "BSR 49; BSR 52; BSR 55; BSR 59; BSR 69; BSR 73; BSR 77",
            "DaData suggestions",
            "BSR 49/52/55/69/73/77. При интеграции DaData допускаются подсказки. BSR 59. Поле должно обновляться данными из DaData после того как пользователь заполнит ФИО через подсказку DaData.",
            "Что происходит после выбора подсказки, при отсутствии совпадений и при ошибке DaData?",
            "Понять, какие дополнительные сценарии DaData можно проверять.",
            "no",
        ),
        card(
            "CLR-015",
            "GAP-006",
            "BSR 58; BSR 79",
            "Dictionaries `Пол`, `Тип документа`",
            "Пол: Значение из справочника «Пол клиента». BSR 79. Во всплывающем окне имеется поле «Тип документа» (значения по справочнику типов документов).",
            "Можно ли в полях `Пол` и `Тип документа` выбрать только значения из справочников, или допускаются другие значения?",
            "Понять, нужно ли проверять отсутствие дополнительных значений в справочниках.",
            "no",
        ),
    ]
    sections = [
        (2, "Контекст", "- `scope_slug`: `application-card-personal-data-and-recognition`\n- Coverage gaps: `scope-coverage-gaps.md`\n- Existing approved clarification source: `support/application-card-personal-data-and-recognition-approved-clarifications.md`"),
        (
            2,
            "Как Заполнять",
            "- БА заполняет только блок `Ответ БА`.\n- `response_status`, `response_type` и `updated_at` заполняет агент после получения ответа.\n- Не удаляйте `clarification_id`, `gap_id`, scope, ссылки, вопрос и служебные поля.\n- Ответы не заменяют основной FT; служебные поля нужны для подтвержденного источника ответа.",
        ),
        (
            2,
            "Clarification Requests",
            "\n\n".join(requests),
        ),
        (
            2,
            "Gaps Without Requests",
            "\n".join(
                [
                    "| gap_id | related_ft_reference | reason |",
                    "| --- | --- | --- |",
                    "| `GAP-005` | Validation/requiredness oracle; `CLR-006` | Вопрос БА сейчас не нужен: существующее уточнение переносит проверку точной реакции UI на UI-калибровку. |",
                    "| `GAP-007` | BSR 43-46 external calculator FT | Вопрос БА не нужен, пока требования к калькулятору не добавлены в источники текущего scope. |",
                    "| `GAP-008` | External FIS Platform widget documentation | Вопрос БА не нужен, пока спецификация виджетов не добавлена в источники текущего scope. |",
                ]
            ),
        ),
        (
            2,
            "Правила Использования Ответов",
            "\n".join(
                [
                    "- Ответы в этом файле не заменяют основной FT.",
                    "- Черновые предположения, пустые ответы, отклонённые и устаревшие ответы не являются подтверждённым источником для тестов.",
                    "- Если ответ закрывает gap, агент регистрирует его как approved clarification в support/source-selection перед production source-first materialization.",
                ]
            ),
        ),
    ]
    write_md("scope-clarification-requests.md", "Scope Clarification Requests", sections)


def make_prompts() -> None:
    common_inputs = [
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/source-selection.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-contract.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/source-parity-check.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/source-row-inventory.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/dictionary-inventory.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/negative-oracle-inventory.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/requiredness-oracle-inventory.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/mockup-visual-inventory.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-coverage-gaps.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-clarification-requests.md`",
        "`work/stage-handoffs/06-application-card-personal-data-and-recognition/workflow-state.yaml`",
        "`support/application-card-personal-data-and-recognition-approved-clarifications.md`",
    ]
    gap_sections = [
        (2, "Цель этапа", "Провести независимый pre-writer review найденных scope gaps в режиме `scope_gap_review` для `application-card-personal-data-and-recognition`."),
        (2, "Входные артефакты", "\n".join(f"- {item}" for item in common_inputs)),
        (
            2,
            "Обязательные действия",
            "\n".join(
                [
                    "- Проверить anchors каждого `GAP-*`: BSR, source row, source path, statement.",
                    "- Проверить blocking classification: especially `GAP-001`-`GAP-003`.",
                    "- Проверить, что `candidate_tc_required` obligations from negative/requiredness inventories are not lost inside parent `GAP-005`.",
                    "- Проверить clarification requests and gaps without requests.",
                    "- Проверить, что XHTML availability remains `yes` and row inventory covers `SRC-001`-`SRC-041`.",
                ]
            ),
        ),
        (2, "Не делать", "- не писать тест-кейсы\n- не проводить writer/reviewer iteration\n- не расширять scope\n- не выдумывать behavior outside FT/support"),
        (
            2,
            "Ожидаемые выходы",
            "- `scope-gap-review.md` with verdict `passed | changes-required` and findings only about scope/gap readiness.\n- If passed, explicit route decision: writer can start only after blocking gaps are resolved/accepted, otherwise state remains blocked for writer.",
        ),
        (2, "Gate завершения", "Этап завершен, когда reviewer подтвердил или отклонил anchors/classification/routing for every `GAP-*`; no test-case review is performed."),
    ]
    write_md("prompt.scope-gaps-to-reviewer.md", "Prompt Scope Gaps To Reviewer", gap_sections)

    writer_sections = [
        (2, "Цель этапа", "Неактивный handoff для будущего writer-pass после passed gap review and resolution/accepted-risk decision for blocking gaps."),
        (2, "Входные артефакты", "\n".join(f"- {item}" for item in common_inputs + ["`work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-gap-review.md` (must exist before use)"])),
        (
            2,
            "Обязательные действия",
            "\n".join(
                [
                    "- Mode: `fresh-eval-run`, unless workflow-state is explicitly updated.",
                    "- Work package-by-package: `WP-01`, then `WP-02`, then `WP-03`.",
                    "- Every `ATOM-*` and `TC-*` must include `package_id`.",
                    "- Before ledger, reconcile writer-side source-row inventory with handoff `source-row-inventory.md` and create `Source Table Normalization`.",
                    "- Carry `SO-NEG-*` / `SO-REQ-*` candidate UI calibration obligations.",
                    "- Use mockup only for interaction hints; FT/support define expected results.",
                    "- Preserve all BSR 43-83 ids from `source-parity-check.md`.",
                    "- Use `scripts/write_artifact_sections.py --manifest` if generated artifacts exceed canonical thresholds.",
                ]
            ),
        ),
        (2, "Не делать", "- не стартовать while `GAP-001`-`GAP-003` are open and unaccepted\n- не создавать source-first production claims without `source-assertions.json` and accepted source assertion review\n- не объединять valid/invalid checks into one TC\n- не использовать mockup as business-rule source"),
        (2, "Ожидаемые выходы", "- canonical test-case file `test-cases/4.3-application-card-personal-data-and-recognition.md`\n- split test-design artifacts under `work/test-design/4.3-application-card-personal-data-and-recognition/`\n- `writer-session-log.md`, writer self-check, and `prompt.writer-to-reviewer.round-1.md`"),
        (2, "Gate завершения", "Writer may set only `stage_status: ready-for-review`; never `signed-off`."),
    ]
    write_md("prompt.scope-to-writer.md", "Prompt Scope To Writer", writer_sections)

    iteration_sections = [
        (2, "Цель этапа", "Неактивный handoff для будущего full writer-reviewer iteration после passed gap review and valid writer entry conditions."),
        (2, "Входные артефакты", "\n".join(f"- {item}" for item in common_inputs + ["`work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-gap-review.md` (must exist before use)"])),
        (
            2,
            "Обязательные действия",
            "- Run writer then independent reviewer loop by project workflow.\n- Preserve package-by-package gates and all scope-stage source/oracle/mockup constraints.\n- Stop on blocking gaps unless accepted-risk is explicit in `workflow-state.yaml`.",
        ),
        (2, "Не делать", "- не начинать reviewer iteration from this prompt until gap review and writer entry conditions are satisfied\n- не skip source parity or source-row inventory\n- не promote legacy output as production without source-first gates"),
        (2, "Ожидаемые выходы", "- review-cycle artifacts under `work/review-cycles/application-card-personal-data-and-recognition/`\n- terminal status `signed-off | round-cap-reached | blocked-input`"),
        (2, "Gate завершения", "Iteration завершена только по canonical session-based review-cycle state; writer alone does not sign off."),
    ]
    write_md("prompt.scope-to-iteration.md", "Prompt Scope To Iteration", iteration_sections)


def make_logs_and_state() -> None:
    decision_rows = [
        ("DEC-001", "1", "scope-boundary", "User selected `SCOPE-OPTION-002`", "Confirmed `application-card-personal-data-and-recognition` in handoff dir `06-*`.", "Scope option already bounded to Table 4 rows 2-15 and BSR 43-83.", "scope-contract.md", "high", "applied"),
        ("DEC-002", "2", "source-boundary", "`source-selection.md`; XHTML availability", "Proceed with XHTML extraction because `xhtml_available=yes`.", "XHTML is mandatory extraction source.", "source-row-inventory.md", "high", "applied"),
        ("DEC-003", "3", "source-boundary", "Prepared context has 41 rows", "Use standard/legacy scope handoff, not lean-production.", "Lean limit is 12 rows; integrations are heterogeneous.", "workflow-state.yaml", "high", "applied"),
        ("DEC-004", "4", "source-boundary", "Prepared context lacks approved-clarification binding", "Do not create compiler-v3 `source-assertions.json` in this handoff.", "A production manifest must hash-bind approved clarification evidence.", "workflow-state.yaml", "risk:production-rematerialization-required", "applied"),
        ("DEC-005", "5", "coverage", "BSR 83 recognition branch", "Classify recognition observation and field mapping as blocking gaps.", "Source lacks observation interface and field mapping.", "scope-coverage-gaps.md", "high", "applied"),
        ("DEC-006", "6", "coverage", "BSR 79/82/83 file attachment", "Classify file type/count/size/valid fixture as blocking for positive recognition branch.", "No stable positive recognition fixture can be derived.", "scope-coverage-gaps.md", "medium", "applied"),
        ("DEC-007", "7", "coverage", "`CLR-006` and negative-ui policy", "Preserve validation/requiredness obligations as `candidate_tc_required`.", "Source defines restrictions but exact UI reaction is for UI calibration.", "negative-oracle-inventory.md; requiredness-oracle-inventory.md", "high", "applied"),
        ("DEC-008", "8", "source-boundary", "Dictionary references `Пол клиента`, `типы документов`", "Extract only referenced dictionaries into dictionary inventory.", "Do not use incomplete examples.", "dictionary-inventory.md", "high", "applied"),
        ("DEC-009", "9", "mockup", "Figures 2, 4, 5 opened visually", "Use mockups only for UI placement/interaction hints; FT/support wins on defaults.", "Mockups show selected values that conflict with `CLR-008`.", "mockup-visual-inventory.md", "high", "applied"),
        ("DEC-010", "10", "routing", "Coverage gaps exist", "Route active next step to `ft-test-case-reviewer` mode `scope_gap_review`.", "Skill requires `prompt.scope-gaps-to-reviewer.md` before writer.", "workflow-state.yaml; prompt.scope-gaps-to-reviewer.md", "high", "applied"),
        ("DEC-011", "11", "fallback", "Python stdout cp1251 UnicodeEncodeError", "Discard partial cp1251 output and rerun with `PYTHONIOENCODING=utf-8`.", "UTF-8 file-based output preserves source text.", "scope-analyzer-session-log.md", "medium", "applied"),
        ("DEC-012", "12", "fallback", "Initial PDF BSR search timed out", "Rerun PDF search in one page pass.", "Timeout was technical, not source ambiguity.", "source-parity-check.md", "medium", "applied"),
        ("DEC-013", "13", "artifact-format", "User requested human-friendly gap answers", "Render clarification requests as vertical CLR cards instead of a wide Markdown table.", "Cards keep the same structured fields while making the answer area editable by a human.", "scope-clarification-requests.md", "high", "applied"),
        ("DEC-014", "14", "artifact-format", "User rejected internal jargon and metadata editing for BA", "Use plain Russian questions and make `response_status`/`response_type`/`updated_at` agent-managed fields.", "BA should answer business questions, not maintain workflow metadata.", "scope-clarification-requests.md; scope-coverage-gaps.md", "high", "applied"),
        ("DEC-015", "15", "artifact-format", "User requested FT text next to each gap question", "Add `source_quote` and visible `Текст из ФТ` block to clarification cards.", "BA should not have to search source documents to understand why a question exists.", "scope-clarification-requests.md", "high", "applied"),
    ]
    decision_table = [
        "| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in decision_rows:
        decision_table.append("| " + " | ".join(f"`{esc(x)}`" for x in row) + " |")
    write_md(
        "agent-decision-log.md",
        "Agent Decision Log",
        [
            (
                2,
                "Decision Log Metadata",
                "| field | value |\n| --- | --- |\n| ft_slug | `AutoFin/PostFinal-v2` |\n| scope_slug | `application-card-personal-data-and-recognition` |\n| stage | `ft-scope-analyzer` |\n| started_from | `work/stage-handoffs/04-postfinal-v2-source-selection/workflow-state.yaml` |",
            ),
            (2, "Decision Log", "\n".join(decision_table)),
        ],
    )

    session_sections = [
        (
            2,
            "Session Metadata",
            "| field | value |\n| --- | --- |\n| skill | `ft-scope-analyzer` |\n| mode | `manual-scope` |\n| ft_slug | `AutoFin/PostFinal-v2` |\n| scope_slug | `application-card-personal-data-and-recognition` |\n| started_from | `work/stage-handoffs/04-postfinal-v2-source-selection/workflow-state.yaml` |\n| status_after | `ready-for-gap-review` |",
        ),
        (
            2,
            "Inputs Read",
            "\n".join(
                [
                    "- `skills/ft-scope-analyzer/SKILL.md` - stage workflow and required outputs.",
                    "- `references/agent/*scope*`, parity, row inventory, oracle, mockup, workflow, session, decision and prompt formats - artifact contracts.",
                    "- `work/stage-handoffs/04-postfinal-v2-source-selection/source-selection.md` and `workflow-state.yaml` - source locator handoff and XHTML gate.",
                    "- `source/PostFinal-v2.docx`, `source/PostFinal-v2.xhtml`, `source/PostFinal-v2.pdf` - selected FT source trio.",
                    "- `support/application-card-personal-data-and-recognition-approved-clarifications.md` - approved scope clarifications.",
                    "- `support/АФБ справочники 26.06.26.md` - dictionary values for `Пол` and `Тип документа`.",
                    "- `mockups/Рисунок 2...jpg`, `Рисунок 4...jpg`, `Рисунок 5...jpg` - visual inspection.",
                    "- `prepared-bounded-context.json`, `source-row-extraction-spec.json`, `source-row-baseline.json` - hash-bound bounded row registry.",
                ]
            ),
        ),
        (
            2,
            "Inputs Not Used",
            "\n".join(
                [
                    "- `work/stage-handoffs/03-application-card-personal-data-and-recognition/` - prior handoff; broad `rg` output surfaced it, but it was not used as source evidence for current artifacts.",
                    "- Other support clarifications for address/passport/employment - outside selected scope.",
                    "- `test-cases/` and `work/review-cycles/` - writer/reviewer artifacts are outside `ft-scope-analyzer`.",
                    "- `AGENT-NOTES.md` - absent.",
                ]
            ),
        ),
        (
            2,
            "Key Decisions",
            "- See `agent-decision-log.md` for `DEC-001`-`DEC-015`.\n- Active handoff is pre-writer `scope_gap_review`; writer/iteration prompts are present but inactive.",
        ),
        (
            2,
            "Risks And Fallbacks",
            "- `GAP-001`-`GAP-003` block complete recognition positive branch.\n- Compiler-v3 production manifest was not created because approved clarification binding is missing from current prepared context; production must rematerialize.\n- Technical fallbacks are listed below.",
        ),
        (
            2,
            "Validation",
            "- Source checks: XHTML available; DOCX/PDF present; PDF one-pass BSR search found all `BSR 43`-`BSR 83` on pages 16-18.\n- Mockup checks: Figures 2, 4 and 5 opened visually through `view_image`.\n- Artifact generation: `scripts/write_artifact_sections.py --manifest` used for Markdown artifacts.\n- Package validator: `validator-report.scope-06.json`; all current `06-*` workflow/source-selection/source-row/oracle/mockup/session/decision checks pass. Remaining findings are pre-existing package-wide issues in `fts/AutoFin/source/~$*.docx` and legacy `work/stage-handoffs/03-*`.",
        ),
        (
            2,
            "Contamination Check",
            "- Existing `03-*` artifacts and prior test/review outputs were not used as requirement evidence.\n- Current source evidence comes from `source/`, relevant `support/`, visual mockups and regenerated/reused hash-bound bounded context in `06-*`.",
        ),
        (
            2,
            "Artifact Write Strategy",
            "\n".join(
                [
                    "| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `source-row-inventory.md` and companion scope artifacts | `generated/table-heavy` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest`; `_artifact-write/build_scope_handoff.py` | `yes` |",
                ]
            ),
        ),
        (
            2,
            "Event Timeline",
            "\n".join(
                [
                    "| step | event | result | artifact_or_evidence |",
                    "| --- | --- | --- | --- |",
                    "| 1 | Runtime/source locator handoff checked | XHTML gate passed | `source-selection.md` |",
                    "| 2 | Scope selected by user | `application-card-personal-data-and-recognition` locked | `scope-contract.md` |",
                    "| 3 | Bounded context prepared | cache reused, candidate count `41` | `prepared-bounded-context.json` |",
                    "| 4 | Source rows/PDF/support/dictionaries inspected | BSR 43-83 and dictionary values confirmed | `source-parity-check.md`; `dictionary-inventory.md` |",
                    "| 5 | Mockups opened | visual hints captured | `mockup-visual-inventory.md` |",
                    "| 6 | Artifacts materialized | generated via manifest helper | `workflow-state.yaml` |",
                ]
            ),
        ),
        (
            2,
            "Quality Checkpoints",
            "\n".join(
                [
                    "| checkpoint | status | evidence | follow_up |",
                    "| --- | --- | --- | --- |",
                    "| XHTML mandatory gate | `pass` | `source-selection.md`; `xhtml_available=yes` | none |",
                    "| Source row inventory completeness | `pass` | 41 rows from prepared context | reviewer should verify anchors |",
                    "| PDF parity | `pass-with-extraction-risk` | all BSR 43-83 found in PDF pages 16-18 | preserve XHTML/PDF BSR ids |",
                    "| Mockup opened gate | `pass` | `view_image` for Figures 2, 4, 5 | do not use as business rule |",
                    "| Writer readiness | `blocked` | `GAP-001`-`GAP-003` | run `scope_gap_review` first |",
                ]
            ),
        ),
        (
            2,
            "Technical Fallbacks",
            "\n".join(
                [
                    "| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| `TF-001` | UnicodeEncodeError on `\\uf0b7` with cp1251 stdout | Python console output with default stdout encoding | reran file-based extraction with `PYTHONIOENCODING=utf-8`; partial cp1251 output discarded | `n/a` | `n/a` | none; UTF-8 source text used | no action; source text was re-read through UTF-8 path |",
                    "| `TF-002` | PDF BSR search timeout | repeated per-code page scans | one-pass per-page BSR extraction with pypdf | `n/a` | `n/a` | none; timeout output not source evidence | no action; one-pass result was used for parity |",
                    "| `TF-003` | table-heavy Markdown and Russian text | n/a: manifest writer selected during preflight before initial artifact write | file-based generator plus canonical section writer | `work/stage-handoffs/06-application-card-personal-data-and-recognition/_artifact-write/build_scope_handoff.py` | `yes` | low; generated tables need reviewer scan | review generated row mappings and gap ids |",
                ]
            ),
        ),
        (
            2,
            "Handoff Notes For Next Session",
            "- Next active skill is `ft-test-case-reviewer` in `scope_gap_review` mode.\n- Do not start writer until gap review passes and blocking `GAP-001`-`GAP-003` are resolved, explicitly deferred as accepted risks, or excluded by user/analyst decision.\n- For production/promotion route, rematerialize source-first assertions with approved-clarification binding; current handoff is not a compiler-v3 accepted manifest.",
        ),
    ]
    write_md("scope-analyzer-session-log.md", "Scope Analyzer Session Log", session_sections)

    state = """ft_slug: AutoFin/PostFinal-v2
scope_slug: application-card-personal-data-and-recognition
current_stage: ft-scope-analyzer
stage_status: ready-for-gap-review
current_round: 0
next_skill: ft-test-case-reviewer
required_inputs:
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/source-selection.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-contract.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/source-parity-check.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/source-row-inventory.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/dictionary-inventory.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/negative-oracle-inventory.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/requiredness-oracle-inventory.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/mockup-visual-inventory.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-coverage-gaps.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-clarification-requests.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/prompt.scope-gaps-to-reviewer.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/agent-decision-log.md
  - work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-analyzer-session-log.md
  - source/PostFinal-v2.docx
  - source/PostFinal-v2.xhtml
  - source/PostFinal-v2.pdf
  - support/application-card-personal-data-and-recognition-approved-clarifications.md
latest_artifacts:
  source_selection: work/stage-handoffs/06-application-card-personal-data-and-recognition/source-selection.md
  source_locator_selection: work/stage-handoffs/04-postfinal-v2-source-selection/source-selection.md
  prepared_bounded_context: work/stage-handoffs/06-application-card-personal-data-and-recognition/prepared-bounded-context.json
  source_row_extraction_spec: work/stage-handoffs/06-application-card-personal-data-and-recognition/source-row-extraction-spec.json
  source_row_baseline: work/stage-handoffs/06-application-card-personal-data-and-recognition/source-row-baseline.json
  scope_contract: work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-contract.md
  source_parity_check: work/stage-handoffs/06-application-card-personal-data-and-recognition/source-parity-check.md
  source_row_inventory: work/stage-handoffs/06-application-card-personal-data-and-recognition/source-row-inventory.md
  dictionary_inventory: work/stage-handoffs/06-application-card-personal-data-and-recognition/dictionary-inventory.md
  negative_oracle_inventory: work/stage-handoffs/06-application-card-personal-data-and-recognition/negative-oracle-inventory.md
  requiredness_oracle_inventory: work/stage-handoffs/06-application-card-personal-data-and-recognition/requiredness-oracle-inventory.md
  mockup_visual_inventory: work/stage-handoffs/06-application-card-personal-data-and-recognition/mockup-visual-inventory.md
  scope_coverage_gaps: work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-coverage-gaps.md
  scope_clarification_requests: work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-clarification-requests.md
  active_transition_prompt: work/stage-handoffs/06-application-card-personal-data-and-recognition/prompt.scope-gaps-to-reviewer.md
  prompt_scope_to_writer: work/stage-handoffs/06-application-card-personal-data-and-recognition/prompt.scope-to-writer.md
  prompt_scope_to_iteration: work/stage-handoffs/06-application-card-personal-data-and-recognition/prompt.scope-to-iteration.md
  validator_report: work/stage-handoffs/06-application-card-personal-data-and-recognition/validator-report.scope-06.json
  session_log: work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-analyzer-session-log.md
  scope_analyzer_session_log: work/stage-handoffs/06-application-card-personal-data-and-recognition/scope-analyzer-session-log.md
  decision_log: work/stage-handoffs/06-application-card-personal-data-and-recognition/agent-decision-log.md
coverage_gaps:
  blocking: 3
  non_blocking: 5
open_questions:
  - GAP-001 / CLR-011: recognition request/wait observation interface.
  - GAP-002 / CLR-012: recognition result field mapping and success state.
  - GAP-003 / CLR-013: allowed file types/count/size and positive fixture.
  - GAP-004 / CLR-014: DaData selection/no-match/error behavior.
  - GAP-006 / CLR-015: dictionary closed-set/no-extra-values semantics.
blocking_reasons: []
accepted_risks: []
notes:
  - Active route is pre-writer scope_gap_review; writer must not start from this state.
  - Current handoff does not include compiler-v3 source-assertions.json; production route requires rematerialization with approved-clarification binding.
"""
    write_text(HANDOFF / "workflow-state.yaml", state)


def main() -> None:
    make_source_selection()
    make_scope_contract()
    make_source_parity()
    make_source_row_inventory()
    make_dictionary_inventory()
    make_requiredness_inventory()
    make_negative_inventory()
    make_mockup_inventory()
    make_gaps()
    make_clarifications()
    make_prompts()
    make_logs_and_state()


if __name__ == "__main__":
    main()
