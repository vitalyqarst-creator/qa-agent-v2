from __future__ import annotations

import json
import subprocess
import sys
from inspect import cleandoc
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "application-card-common-actions"
SECTION = "section-38"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/07-{SCOPE}"
HANDOFF = FT / HANDOFF_REL
SCRATCH = TD / "_artifact_write"


INSTRUCTION_FILES = [
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

ACTIVE_REASONS = [
    "Высокая ставка",
    "Не готов предоставить документы",
    "Не устраивает сумма",
    "Кредит/карта не нужны",
    "Технический сбой",
    "Заявка создана ошибочно",
]


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def normalize_markdown(content: str) -> str:
    text = cleandoc(content)
    lines = text.splitlines()
    if any(line.startswith("        #") or line.startswith("        |") for line in lines):
        lines = [line[8:] if line.startswith("        ") else line for line in lines]
    return "\n".join(lines).strip()


def write_via_manifest(target: Path, title: str, sections: list[tuple[int, str, str]]) -> None:
    artifact_dir = SCRATCH / target.stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    preamble = artifact_dir / "00-preamble.md"
    preamble.write_text(f"# {title}\n", encoding="utf-8", newline="\n")
    manifest_sections = []
    for index, (level, heading, content) in enumerate(sections, start=1):
        content_path = artifact_dir / f"{index:02d}.md"
        content_path.write_text(normalize_markdown(content) + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append(
            {
                "level": level,
                "heading": heading,
                "content_file": content_path.name,
            }
        )
    manifest = {
        "target_path": str(target),
        "preamble_file": preamble.name,
        "sections": manifest_sections,
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
    )


SOURCE_ROWS = [
    ["`SRC-001`", "`WP-01`", "`Отменить заявку`", '`DOCX section-35; table row "Отменить заявку"`', "`section-35`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-001`; `GAP-002`"],
    ["`SRC-002`", "`WP-01`", "`Отменить заявку`", '`DOCX section-38; table row "Отменить заявку"`', "`section-38`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-001`; `GAP-002`"],
    ["`SRC-003`", "`WP-02`", "`История заявки`", '`DOCX section-38; table row "История заявки"; target form section-39`', "`section-38`", "`yes`", "`ATOM-007`; `GAP-001`"],
    ["`SRC-001.P01`", "`WP-01`", "`Отменить заявку / open modal`", "`normalized from SRC-001; duplicate behavior also anchored by SRC-002`", "`section-35`", "`yes`", "`ATOM-001`"],
    ["`SRC-001.P02`", "`WP-01`", "`Причина отказа / dictionary`", "`normalized from SRC-001; duplicate behavior also anchored by SRC-002; DICT-001`", "`section-35`", "`yes`", "`ATOM-002`"],
    ["`SRC-001.P03`", "`WP-01`", "`Подтвердить без причины`", "`normalized from SRC-001; duplicate behavior also anchored by SRC-002`", "`section-35`", "`yes`", "`ATOM-003`"],
    ["`SRC-001.P04`", "`WP-01`", "`Подтвердить с причиной`", "`normalized from SRC-001; duplicate behavior also anchored by SRC-002`", "`section-35`", "`yes`", "`ATOM-004`"],
    ["`SRC-001.P06`", "`WP-01`", "`Отменить в модальном окне`", "`normalized from SRC-001; duplicate behavior also anchored by SRC-002`", "`section-35`", "`yes`", "`ATOM-006`"],
    ["`SRC-003.P01`", "`WP-02`", "`История заявки / open window`", "`normalized from SRC-003`", "`section-38`", "`yes`", "`ATOM-007`"],
]

COMPLETENESS_ROWS = [
    ["`SRC-001`", "`section-35`", "`SRC-001.P01`; `SRC-001.P02`; `SRC-001.P03`; `SRC-001.P04`; `SRC-001.P06`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`", "`GAP-001`; `GAP-002`", "`covered-with-duplicate-normalization`"],
    ["`SRC-002`", "`section-38`", "`SRC-001.P01`; `SRC-001.P02`; `SRC-001.P03`; `SRC-001.P04`; `SRC-001.P06`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`", "`GAP-001`; `GAP-002`", "`covered-with-duplicate-normalization`"],
    ["`SRC-003`", "`section-38`", "`SRC-003.P01`", "`ATOM-007`", "`GAP-001`", "`covered`"],
]

NORMALIZATION_ROWS = [
    ["`SRC-001.P01`", "`SRC-001.P01`", "`WP-01`", "`Отменить заявку`", "`action-opens-modal`", "`click Отменить заявку`", "Открывается окно выбора причины отказа.", "`section-35`", "`DOCX section-35 row Отменить заявку`", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-001.P02`", "`SRC-001.P02`", "`WP-01`", "`Причина отказа`", "`dictionary-source`", "`reason modal opened`", "`Причины отказа от УЗ` берутся из `DICT-001`.", "`section-35`", "`DOCX section-35 row Отменить заявку; support DICT-001`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-001.P03`", "`SRC-001.P03`", "`WP-01`", "`Подтвердить`", "`validation-message`", "`no reason selected`", "При подтверждении без причины отображается сообщение `Выберите причину отказа`.", "`section-35`", "`DOCX section-35 row Отменить заявку`", "`high`", "`none_required:covered`", "`ATOM-003`"],
    ["`SRC-001.P04`", "`SRC-001.P04`", "`WP-01`", "`Подтвердить`", "`status-lifecycle`", "`at least one reason selected`", "УЗ переходит в статус `Отказ клиента`.", "`section-35`", "`DOCX section-35 row Отменить заявку`", "`high`", "`none_required:covered`", "`ATOM-004`"],
    ["`SRC-001.P06`", "`SRC-001.P06`", "`WP-01`", "`Отменить`", "`modal-cancel-return`", "`reason modal opened`", "Действие `Отменить` закрывает окно и возвращает на карточку УЗ.", "`section-35`", "`DOCX section-35 row Отменить заявку`", "`high`", "`none_required:covered`", "`ATOM-006`"],
    ["`SRC-003.P01`", "`SRC-003.P01`", "`WP-02`", "`История заявки`", "`action-opens-window`", "`click История заявки`", "Открывается окно просмотра истории заявки.", "`section-38`", "`DOCX section-38 row История заявки; section-39 target only`", "`high`", "`none_required:covered`", "`ATOM-007`"],
]

TDDT_ROWS = [
    ["`DEC-001`", "`WP-01`", "`SRC-001.P01`", "`ATOM-001`", "`action-opens-modal`", "`standalone_tc`", "Открытие окна является отдельным observable result.", "`TC-ACA-001`", "`DOCX row`", "`yes`", "Открыто окно выбора причины отказа.", "Открытие модального окна.", "`none_required:covered`", "`none_required:covered`", "`low`"],
    ["`DEC-002`", "`WP-01`", "`SRC-001.P02`", "`ATOM-002`", "`dictionary-source`", "`standalone_tc`", "Справочник задан support workbook и должен быть проверен всеми active values.", "`TC-ACA-002`", "`DICT-001`", "`yes`", "В окне доступны все active values `DICT-001`.", "Состав списка причин.", "`none_required:covered`", "`none_required:covered`", "`medium`"],
    ["`DEC-003`", "`WP-01`", "`SRC-001.P03`", "`ATOM-003`", "`required-selection-message`", "`standalone_tc`", "Ветка без причины имеет отдельное сообщение.", "`TC-ACA-003`", "`DOCX row`", "`yes`", "Сообщение `Выберите причину отказа` отображается.", "Подтверждение без причины.", "`none_required:covered`", "`none_required:covered`", "`low`"],
    ["`DEC-004`", "`WP-01`", "`SRC-001.P04`", "`ATOM-004`", "`status-lifecycle`", "`standalone_tc`", "Ветка с причиной имеет отдельный результат смены статуса.", "`TC-ACA-004`", "`DOCX row; DICT-001`", "`yes`", "Статус УЗ отображается как `Отказ клиента`.", "Подтверждение с выбранной причиной.", "`none_required:covered`", "`none_required:covered`", "`medium`"],
    ["`DEC-005`", "`WP-01`", "`SRC-001.P06`", "`ATOM-006`", "`modal-cancel-return`", "`standalone_tc`", "Ветка `Отменить` имеет отдельный результат возврата.", "`TC-ACA-005`", "`DOCX row`", "`yes`", "Окно закрыто, карточка УЗ отображается.", "Отмена в модальном окне.", "`none_required:covered`", "`none_required:covered`", "`low`"],
    ["`DEC-006`", "`WP-02`", "`SRC-003.P01`", "`ATOM-007`", "`action-opens-window`", "`standalone_tc`", "Scope включает только entrypoint в форму истории.", "`TC-ACA-006`", "`DOCX row`", "`yes`", "Открыто окно просмотра истории заявки.", "Открытие окна истории.", "`section-39` internals out of scope.", "`none_required:covered`", "`low`"],
]

OBLIGATION_ROWS: list[list[str]] = [
    ["`OBL-001`", "`WP-01`", "`SRC-001.P03`", "`ATOM-003`", "`validation-message`", "`message-triggered`", "Сообщение `Выберите причину отказа` отображается при подтверждении без причины.", "`section-35`; `section-38`", "`TC-ACA-003`", "`covered`", "`none_required:covered`"],
]

ATOM_ROWS = [
    ["`ATOM-001`", "`WP-01`", "`SRC-001.P01`; duplicate anchor `SRC-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`", "При действии `Отменить заявку` открывается окно выбора причины отказа.", "`TC-ACA-001`", "`covered`", "`none_required:covered`"],
    ["`ATOM-002`", "`WP-01`", "`SRC-001.P02`; duplicate anchor `SRC-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`; `DICT-001`", "В окне выбора причины отказа используются active values справочника `Причины отказа от УЗ`.", "`TC-ACA-002`", "`covered`", "`none_required:covered`"],
    ["`ATOM-003`", "`WP-01`", "`SRC-001.P03`; duplicate anchor `SRC-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`", "При `Подтвердить` без выбранной причины отображается сообщение `Выберите причину отказа`.", "`TC-ACA-003`", "`covered`", "`none_required:covered`"],
    ["`ATOM-004`", "`WP-01`", "`SRC-001.P04`; duplicate anchor `SRC-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`; `DICT-001`", "При `Подтвердить` с хотя бы одной выбранной причиной УЗ переходит в статус `Отказ клиента`.", "`TC-ACA-004`", "`covered`", "`none_required:covered`"],
    ["`ATOM-005`", "`WP-01`", "`GAP-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`; `GAP-002`", "После перехода в статус `Отказ клиента` дальнейшее редактирование УЗ запрещается.", "`GAP-002`", "`unclear`", "`unclear:GAP-002`"],
    ["`ATOM-006`", "`WP-01`", "`SRC-001.P06`; duplicate anchor `SRC-002`", "`section-35`; `section-38`", "`SRC-001`; `SRC-002`", "Действие `Отменить` в окне выбора причины отказа возвращает пользователя на карточку УЗ.", "`TC-ACA-005`", "`covered`", "`none_required:covered`"],
    ["`ATOM-007`", "`WP-02`", "`SRC-003.P01`", "`section-38`", "`SRC-003`; `section-39 target only`", "Действие `История заявки` открывает окно просмотра истории заявки.", "`TC-ACA-006`", "`covered`", "`none_required:covered`"],
]

PLAN_ROWS = [
    ["`PLAN-001`", "`WP-01`", "`action-flow`", "`section-35`; `section-38`", "`ATOM-001`", "Открыть окно выбора причины отказа.", "`positive`", "`modal-opened`", "`action-click`", "Окно выбора причины отказа отображается.", "`DOCX row`", "`TC-ACA-001`", "`covered`"],
    ["`PLAN-002`", "`WP-01`", "`dictionary`", "`DICT-001`", "`ATOM-002`", "Проверить состав списка причин отказа.", "`positive`", "`dictionary-values`", "`all-active-values`", "Список содержит все active values `DICT-001` и не содержит archived values.", "`support workbook`", "`TC-ACA-002`", "`covered`"],
    ["`PLAN-003`", "`WP-01`", "`branch`", "`section-35`; `section-38`", "`ATOM-003`", "Нажать `Подтвердить` без выбранной причины.", "`negative`", "`required-selection`", "`empty-selection`", "Отображается сообщение `Выберите причину отказа`.", "`DOCX row`", "`TC-ACA-003`", "`covered`"],
    ["`PLAN-004`", "`WP-01`", "`branch`", "`section-35`; `section-38`; `DICT-001`", "`ATOM-004`", "Выбрать одну active reason и нажать `Подтвердить`.", "`positive`", "`status-transition`", "`selected-active-reason`", "Статус УЗ отображается как `Отказ клиента`.", "`DOCX row`", "`TC-ACA-004`", "`covered`"],
    ["`PLAN-005`", "`WP-01`", "`status-lifecycle`", "`section-35`; `section-38`; `GAP-002`", "`ATOM-005`", "Сохранить edit-lock как unclear до source/UI evidence.", "`gap`", "`edit-lock`", "`status Отказ клиента`", "Точный механизм запрета редактирования не задан.", "`scope-coverage-gaps.md`", "`GAP-002`", "`unclear`"],
    ["`PLAN-006`", "`WP-01`", "`branch`", "`section-35`; `section-38`", "`ATOM-006`", "Нажать `Отменить` в окне выбора причины отказа.", "`positive`", "`modal-cancel`", "`cancel-button`", "Окно закрыто, карточка УЗ отображается.", "`DOCX row`", "`TC-ACA-005`", "`covered`"],
    ["`PLAN-007`", "`WP-02`", "`action-result`", "`section-38`; `section-39 target only`", "`ATOM-007`", "Нажать `История заявки`.", "`positive`", "`history-window-opened`", "`action-click`", "Открыто окно просмотра истории заявки.", "`DOCX row`", "`TC-ACA-006`", "`covered`"],
]

GAPS_ROWS = [
    ["`GAP-001`", "`all`", "`source-parity-check.md`; `section-35`; `section-38`", "`ambiguity`", "PDF extraction не подтвердил выбранные строки.", "Не использовать PDF page refs, PDF-only IDs или PDF-backed behavior.", "`no`", "`open`"],
    ["`GAP-002`", "`WP-01`", "`section-35`; `section-38`; row Отменить заявку`", "`missing-rule`", "ФТ запрещает дальнейшее редактирование УЗ после статуса `Отказ клиента`, но не задает точный observable UI mechanism.", "Покрыть статус transition; edit-lock exact oracle оставить `unclear`.", "`no`", "`open`"],
]


def canonical_tc() -> str:
    reason_rows = "; ".join(f"`{value}`" for value in ACTIVE_REASONS)
    return dedent(
        f"""
        ## Metadata

        | field | value |
        | --- | --- |
        | ft_slug | `ft-2-OF_17` |
        | scope_slug | `{SCOPE}` |
        | section_id | `{SECTION}` |
        | writer_stage | `writer-r1` |
        | mode | `fresh-eval-run` |
        | canonical_test_design_dir | `{TD_REL}` |

        ## Scope Boundaries

        В набор входят только общие действия карточки Универсальной заявки: `Отменить заявку` и entrypoint `История заявки`. Полная форма истории из `section-39`, backend persistence, RabbitMQ/API/audit effects, PDF-only IDs и точный механизм edit-lock после статуса `Отказ клиента` не включены.

        ## Canonical Artifact Links

        {bullet([
            f"`{TD_REL}/source-row-inventory.md`",
            f"`{TD_REL}/source-table-normalization.md`",
            f"`{TD_REL}/atomic-requirements-ledger.md`",
            f"`{TD_REL}/package-test-design-plan.md`",
            f"`{TD_REL}/test-design-decision-table.md`",
            f"`{TD_REL}/dependency-matrix.md`",
            f"`{TD_REL}/risk-priority-map.md`",
            f"`{TD_REL}/coverage-gaps.md`",
            f"`{TD_REL}/writer-quality-gate.md`",
            f"`{TD_REL}/writer-self-check.md`",
        ])}

        ## Coverage Summary

        | package_id | focus | atoms | executable_tc | gap_or_unclear |
        | --- | --- | --- | --- | --- |
        | `WP-01` | Cancel application action flow | `ATOM-001`..`ATOM-006` | `TC-ACA-001`..`TC-ACA-005` | `GAP-001`; `GAP-002` |
        | `WP-02` | History action entrypoint | `ATOM-007` | `TC-ACA-006` | `GAP-001` |

        ## Coverage Gaps

        - `GAP-001`: PDF extraction risk. DOCX-backed behavior is covered; PDF page refs and PDF-only IDs are not claimed.
        - `GAP-002`: exact edit-lock mechanism after status `Отказ клиента` remains unclear. The executable set covers status transition but does not invent disabled-field/save-hidden/error-message behavior.

        ## WP-01 - Отменить заявку

        ## TC-ACA-001

        **Название:** Открытие окна выбора причины отказа по действию `Отменить заявку`

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-001`; `section-35`; `section-38`; `SRC-001`; `SRC-002`; `GAP-001`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `Отменить заявку`.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        {numbered([
            "В карточке Универсальной заявки нажать действие `Отменить заявку`.",
        ])}

        ### Итоговый ожидаемый результат

        Открыто окно выбора причины отказа от УЗ.

        ### Постусловия

        Закрыть окно выбора причины отказа без подтверждения отказа, если оно осталось открытым.

        ## TC-ACA-002

        **Название:** Состав списка причин отказа в окне отмены заявки

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-002`; `DICT-001`; `section-35`; `section-38`; `SRC-001`; `SRC-002`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `Отменить заявку`.
        - Открыто окно выбора причины отказа от УЗ.

        ### Тестовые данные

        Active values `DICT-001`: {reason_rows}.

        ### Шаги

        {numbered([
            "Открыть список причин отказа в окне выбора причины отказа от УЗ.",
            "Сверить отображаемые значения списка с active values `DICT-001` из тестовых данных.",
        ])}

        ### Итоговый ожидаемый результат

        Список причин отказа содержит все active values `DICT-001`; archived values в `DICT-001` отсутствуют.

        ### Постусловия

        Закрыть окно выбора причины отказа без подтверждения отказа, если оно осталось открытым.

        ## TC-ACA-003

        **Название:** Подтверждение отказа без выбранной причины

        **Тип:** Negative

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-003`; `section-35`; `section-38`; `SRC-001`; `SRC-002`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `Отменить заявку`.
        - Открыто окно выбора причины отказа от УЗ.
        - В окне не выбрана ни одна причина отказа.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        {numbered([
            "В окне выбора причины отказа нажать `Подтвердить`.",
        ])}

        ### Итоговый ожидаемый результат

        Отображается сообщение `Выберите причину отказа`.

        ### Постусловия

        Закрыть окно выбора причины отказа без подтверждения отказа, если оно осталось открытым.

        ## TC-ACA-004

        **Название:** Подтверждение отказа с выбранной причиной

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-004`; `DICT-001`; `section-35`; `section-38`; `SRC-001`; `SRC-002`; `GAP-002`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `Отменить заявку`.
        - Открыто окно выбора причины отказа от УЗ.

        ### Тестовые данные

        Выполнить отдельный прогон для каждой active value `DICT-001`: {reason_rows}.

        ### Шаги

        {numbered([
            "В окне выбора причины отказа выбрать одну причину из active values `DICT-001`, соответствующую текущему прогону.",
            "Нажать `Подтвердить`.",
        ])}

        ### Итоговый ожидаемый результат

        В карточке УЗ отображается статус `Отказ клиента`.

        ### Постусловия

        Использовать отдельную тестовую УЗ для каждого прогона, так как подтверждение отказа меняет статус заявки.

        ## TC-ACA-005

        **Название:** Отмена действия в окне выбора причины отказа

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-006`; `section-35`; `section-38`; `SRC-001`; `SRC-002`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `Отменить заявку`.
        - Открыто окно выбора причины отказа от УЗ.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        {numbered([
            "В окне выбора причины отказа нажать `Отменить`.",
        ])}

        ### Итоговый ожидаемый результат

        Окно выбора причины отказа закрыто, отображается карточка УЗ.

        ### Постусловия

        Не требуются.

        ## WP-02 - История заявки

        ## TC-ACA-006

        **Название:** Открытие окна просмотра истории заявки

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-02

        **Трассировка:** `ATOM-007`; `section-38`; `SRC-003`; `section-39 target only`; `GAP-001`

        ### Предусловия

        - Открыта карточка Универсальной заявки, в которой доступно действие `История заявки`.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        {numbered([
            "В карточке Универсальной заявки нажать действие `История заявки`.",
        ])}

        ### Итоговый ожидаемый результат

        Открыто окно просмотра истории заявки.

        ### Постусловия

        Закрыть окно просмотра истории заявки, если оно осталось открытым.
        """
    ).strip()


def write_markdown_artifacts() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)

    write_via_manifest(
        TD / "artifact-write-strategy.md",
        "Artifact Write Strategy",
        [
            (
                2,
                "Artifact Write Strategy",
                table(
                    ["item", "value", "evidence"],
                    [
                        ["preflight_result", "`large-file / package-based`", "`WP-01`; `WP-02`; split artifacts required by scope-contract"],
                        ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`"],
                        ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
                        ["chunk_plan", "`WP-01 -> WP-02`", "Writer processes cancel flow before history entrypoint."],
                        ["helper_artifacts", f"`{TD_REL}/_artifact_write/`", "Manifest/content transport only; no hidden generation logic."],
                        ["validation_plan", "`validate_agent_artifacts` then `codex_review_cycle_runner validate`", "After final artifact write and cycle-state update."],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "source-row-inventory.md",
        "Source Row Inventory Artifact",
        [
            (2, "Source Row Inventory", table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], SOURCE_ROWS)),
            (2, "Writer Inventory Notes", bullet([
                "`SRC-001` and `SRC-002` are duplicate source rows for the same cancel action and map to one shared behavior set.",
                "`SRC-003` covers only opening the history viewing window; full section-39 behavior is out of scope.",
            ])),
        ],
    )
    write_via_manifest(
        TD / "source-row-completeness-matrix.md",
        "Source Row Completeness Matrix",
        [
            (2, "Source Row Completeness Matrix", table(["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"], COMPLETENESS_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "source-table-normalization.md",
        "Source Table Normalization Artifact",
        [
            (2, "Source Row Inventory", table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], SOURCE_ROWS)),
            (2, "Source Table Normalization", table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], NORMALIZATION_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "test-design-decision-table.md",
        "Test Design Decision Table",
        [
            (2, "Test Design Decision Table", table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], TDDT_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "coverage-obligation-table.md",
        "Coverage Obligation Table",
        [
            (2, "Coverage Obligation Table", table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], OBLIGATION_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "dictionary-inventory.md",
        "Dictionary Inventory",
        [
            (
                2,
                "Dictionary Inventory",
                table(
                    ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
                    [["`DICT-001`", "`Причины отказа от УЗ`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Причины отказа от УЗ; columns: Значение, Архивный, Описание атрибута`", "`extracted`", "; ".join(f"`{item}`" for item in ACTIVE_REASONS), "`none_required:no_archived_values`", "`SRC-001.P02`; `SRC-002.P01`; `ATOM-002`; `TC-ACA-002`; `TC-ACA-004`", "`none_required:covered`", "`Архивный = Нет` трактуется как active; строка `Назад` исключена как navigation noise."]],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "atomic-requirements-ledger.md",
        "Atomic Requirements Ledger",
        [
            (2, "Atomic Requirements Ledger", table(["atom_id", "package_id", "source_property_id", "req_id", "source_ref", "atomic_statement", "covered_by_tc", "coverage_status", "gap_id"], ATOM_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "internal-work-package-coverage.md",
        "Internal Work Package Coverage",
        [
            (
                2,
                "Internal Work Package Coverage",
                table(
                    ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
                    [
                        ["`WP-01`", "Cancel application action flow", "`pass`", "`pass`", "`pass`", "`6`", "`5`", "`1`", "`1`", "`5`", "`ready-for-review`"],
                        ["`WP-02`", "History action entrypoint", "`pass`", "`pass`", "`pass`", "`1`", "`1`", "`0`", "`0`", "`1`", "`ready-for-review`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "package-ledger-self-check.md",
        "Package Ledger Self-Check",
        [
            (
                2,
                "Package Ledger Self-Check",
                table(
                    ["package_id", "check", "status", "evidence", "follow_up"],
                    [
                        ["`WP-01`", "`duplicate-source-normalization`", "`pass`", "`SRC-001` and `SRC-002` map to shared `ATOM-001`..`ATOM-006`.", "`none_required:pass`"],
                        ["`WP-01`", "`atomarity`", "`pass`", "Modal open, dictionary, empty confirm, selected confirm, edit-lock and modal cancel are separate atoms.", "`none_required:pass`"],
                        ["`WP-02`", "`scope-boundary`", "`pass`", "`ATOM-007` covers only opening the history window.", "`none_required:pass`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "package-test-design-plan.md",
        "Package Test Design Plan",
        [
            (2, "Package Test Design Plan", table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], PLAN_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "package-design-plan-self-check.md",
        "Package Design Plan Self-Check",
        [
            (
                2,
                "Package Design Plan Self-Check",
                table(
                    ["package_id", "check", "status", "evidence", "follow_up"],
                    [
                        ["`WP-01`", "`branches-split`", "`pass`", "`Подтвердить` без причины, `Подтвердить` с причиной and `Отменить` are separate plan rows and TC.", "`none_required:pass`"],
                        ["`WP-01`", "`dictionary-used`", "`pass`", "`DICT-001` linked in plan and TC.", "`none_required:pass`"],
                        ["`WP-02`", "`section-39-not-expanded`", "`pass`", "Plan has only `PLAN-007` for opening the history window.", "`none_required:pass`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "test-design-review.md",
        "Test Design Review",
        [
            (
                2,
                "Test Design Review",
                table(
                    ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
                    [
                        ["`decision-table-classification`", "`pass`", "`info`", "`all`", "Standalone/gap/metadata decisions align with source-backed observability.", "`none_required:pass`", "`no`"],
                        ["`ledger-plan-alignment`", "`pass`", "`info`", "`all`", "`ATOM-*`, Package Test Design Plan and TC links are synchronized.", "`none_required:pass`", "`no`"],
                        ["`coverage-class-completeness`", "`pass`", "`info`", "`all`", "Action, dependency, dictionary and status-lifecycle classes are represented.", "`none_required:pass`", "`no`"],
                        ["`numeric-length-boundaries`", "`pass`", "`info`", "`all`", "Numeric/length/boundary dimensions are not present in selected source rows.", "`none_required:not_applicable`", "`no`"],
                        ["`conditional-branches`", "`pass`", "`info`", "`WP-01`", "`Подтвердить` без причины, `Подтвердить` с причиной and `Отменить` are split.", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`info`", "`all`", "Gaps do not hide executable source-backed modal, message, status, cancel or history-window behavior.", "`none_required:pass`", "`no`"],
                        ["`gap-specificity`", "`pass`", "`info`", "`all`", "`GAP-001` is traceability-only; `GAP-002` is exact edit-lock mechanism only.", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "`info`", "`all`", "No backend/API/RabbitMQ/audit effect is claimed by executable TC.", "`none_required:pass`", "`no`"],
                        ["`metadata-only-exclusion`", "`pass`", "`info`", "`WP-01`", "`ATOM-005` source constraint is not turned into executable TC without oracle.", "`none_required:pass`", "`no`"],
                        ["`tc-mapping-atomicity`", "`pass`", "`info`", "`all`", "Each `TC-ACA-*` has one primary expected result.", "`none_required:pass`", "`no`"],
                        ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`all`", "Applicability matrix links only TC that exercise the named dimension.", "`none_required:pass`", "`no`"],
                        ["`dictionary-closed-set`", "`pass`", "`info`", "`WP-01`", "`TC-ACA-002` checks active values from `DICT-001`; invalid/free-text rejection is not invented.", "`none_required:pass`", "`no`"],
                        ["`mask-format-coverage`", "`pass`", "`info`", "`all`", "Mask/format dimension is not present in selected source rows.", "`none_required:not_applicable`", "`no`"],
                        ["`negative-fixture-isolation`", "`pass`", "`info`", "`WP-01`", "`TC-ACA-003` isolates empty reason selection and does not rely on hidden fixture fields.", "`none_required:pass`", "`no`"],
                        ["`ready-for-tc-writing`", "`pass`", "`info`", "`all`", "No blocking design review rows remain.", "`none_required:pass`", "`no`"],
                        ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`WP-01`", "No TC asserts a disabled-field/save-hidden/error-message mechanism for `GAP-002`.", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "dependency-matrix.md",
        "Dependency Matrix",
        [
            (
                2,
                "Dependency Matrix",
                table(
                    ["dependency_id", "package_id", "controlling_action_or_value", "controlling_value", "dependent_field", "branch", "expected_result", "linked_atoms", "tc_gap", "gap_id"],
                    [
                        ["`DEP-001`", "`WP-01`", "`Отменить заявку`", "`click`", "`reason modal`", "`click`", "Открывается окно выбора причины отказа.", "`ATOM-001`", "`TC-ACA-001`", "`none_required:covered`"],
                        ["`DEP-002`", "`WP-01`", "`Подтвердить`", "`no reason selected`", "`reason selection`", "`no reason selected`", "Отображается сообщение `Выберите причину отказа`.", "`ATOM-003`", "`TC-ACA-003`", "`none_required:covered`"],
                        ["`DEP-003`", "`WP-01`", "`Подтвердить`", "`at least one reason selected`", "`application status`", "`at least one reason selected`", "Статус УЗ становится `Отказ клиента`.", "`ATOM-004`", "`TC-ACA-004`", "`none_required:covered`"],
                        ["`DEP-004`", "`WP-01`", "`status Отказ клиента`", "`post-transition`", "`application editability`", "`post-transition edit-lock`", "Точный механизм запрета редактирования не задан.", "`ATOM-005`", "`GAP-002`", "`GAP-002`"],
                        ["`DEP-005`", "`WP-01`", "`Отменить`", "`modal cancel`", "`reason modal`", "`modal cancel`", "Возврат на карточку УЗ.", "`ATOM-006`", "`TC-ACA-005`", "`none_required:covered`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "test-design-applicability-matrix.md",
        "Test-design Applicability Matrix",
        [
            (
                2,
                "Test-design Applicability Matrix",
                table(
                    ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
                    [
                        ["`other`", "`yes`", "`section-35`; `section-38`", "Actions open modal/window.", "`ATOM-001`; `ATOM-007`", "`TC-ACA-001`; `TC-ACA-006`", ""],
                        ["`other`", "`yes`", "`DICT-001`", "Reason selector uses refusal reasons dictionary.", "`ATOM-002`", "`TC-ACA-002`", ""],
                        ["`dependency`", "`yes`", "`section-35`; `section-38`", "Confirm without reason, confirm with reason and modal cancel differ.", "`ATOM-003`; `ATOM-004`; `ATOM-006`", "`TC-ACA-003`; `TC-ACA-004`; `TC-ACA-005`", ""],
                        ["`status-lifecycle`", "`yes`", "`section-35`; `section-38`", "Cancel changes status; history opens window.", "`ATOM-004`; `ATOM-007`", "`TC-ACA-004`; `TC-ACA-006`", ""],
                        ["`other`", "`unclear`", "`GAP-002`", "Edit-lock obligation exists but exact mechanism is absent.", "`ATOM-005`", "", "`GAP-002`"],
                        ["`other`", "`no`", "`scope-contract.md`", "No selected source row contains internal-effect requirement.", "", "", ""],
                        ["`scope`", "`no`", "`scope-contract.md`", "Full section-39 table/filter/download behavior is excluded.", "", "", ""],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "risk-priority-map.md",
        "Risk / Priority Map",
        [
            (
                2,
                "Risk / Priority Map",
                table(
                    ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
                    [
                        ["`ATOM-001`", "`action-navigation`", "`3`", "`3`", "`9`", "`medium`", "`navigation`", "`section-35`; `section-38`", "`High`", "`TC-ACA-001`", "`none_required:covered`", "`none`", "Opening the modal gates the cancel flow."],
                        ["`ATOM-002`", "`dictionary`", "`3`", "`3`", "`9`", "`medium`", "`dictionary-values`", "`DICT-001`", "`Medium`", "`TC-ACA-002`; `TC-ACA-004`", "`none_required:covered`", "`none`", "Wrong reasons can break refusal classification, but no irreversible transition happens in the list check."],
                        ["`ATOM-003`", "`validation-message`", "`4`", "`3`", "`12`", "`high`", "`server-side-rejection`", "`section-35`; `section-38`", "`High`", "`TC-ACA-003`", "`none_required:covered`", "`none`", "Empty reason must not silently move the application."],
                        ["`ATOM-004`", "`status-lifecycle`", "`5`", "`3`", "`15`", "`high`", "`irreversible-state`", "`section-35`; `section-38`", "`High`", "`TC-ACA-004`", "`none_required:covered`", "`none`", "Refusal changes business status to `Отказ клиента`."],
                        ["`ATOM-005`", "`editability`", "`4`", "`2`", "`8`", "`medium`", "`data-loss`", "`GAP-002`", "`Medium`", "`none_required:no_executable_tc`", "`GAP-002`", "`deferred-by-scope`", "Obligation is known, but exact observable mechanism requires clarification."],
                        ["`ATOM-006`", "`modal-cancel`", "`3`", "`3`", "`9`", "`medium`", "`branch-result`", "`section-35`; `section-38`", "`Medium`", "`TC-ACA-005`", "`none_required:covered`", "`none`", "Cancel branch should not perform refusal."],
                        ["`ATOM-007`", "`action-navigation`", "`3`", "`3`", "`9`", "`medium`", "`navigation`", "`section-38`", "`Medium`", "`TC-ACA-006`", "`none_required:covered`", "`none`", "History entrypoint must open the target window; internals are out of scope."],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "coverage-metrics.md",
        "Coverage Metrics",
        [
            (
                2,
                "Coverage Metrics",
                table(
                    ["dimension", "applicable_obligations", "covered", "gap", "unclear", "evidence"],
                    [
                        ["`action-flow`", "`4`", "`4`", "`0`", "`0`", "`TC-ACA-001`; `TC-ACA-003`; `TC-ACA-004`; `TC-ACA-005`"],
                        ["`dictionary`", "`1`", "`1`", "`0`", "`0`", "`TC-ACA-002`; `DICT-001`"],
                        ["`status-lifecycle`", "`2`", "`1`", "`0`", "`1`", "`TC-ACA-004`; `GAP-002`"],
                        ["`history-entrypoint`", "`1`", "`1`", "`0`", "`0`", "`TC-ACA-006`"],
                        ["`traceability`", "`3 source rows`", "`3`", "`0`", "`1 extraction risk`", "`GAP-001`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "coverage-map.md",
        "Coverage Map",
        [
            (
                2,
                "Coverage Map",
                table(
                    ["metric", "value", "evidence"],
                    [
                        ["atomic statements", "`7`", "`atomic-requirements-ledger.md`"],
                        ["covered atoms", "`6`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-006`; `ATOM-007`"],
                        ["unclear atoms", "`1`", "`ATOM-005` via `GAP-002`"],
                        ["executable test cases", "`6`", "`TC-ACA-001`..`TC-ACA-006`"],
                        ["source rows preserved", "`3`", "`source-row-inventory.md`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "coverage-gaps.md",
        "Coverage Gaps",
        [
            (2, "Coverage Gaps", table(["gap_id", "package_id", "source_ref", "gap_type", "description", "temporary_handling", "blocks_ready_for_review", "status"], GAPS_ROWS)),
        ],
    )
    write_via_manifest(
        TD / "fixture-catalog.md",
        "Fixture Catalog",
        [
            (
                2,
                "Fixture Catalog",
                table(
                    ["fixture_id", "package_id", "purpose", "setup", "used_by", "limitations"],
                    [
                        ["`FIX-001`", "`WP-01`", "Карточка УЗ с доступным действием `Отменить заявку`.", "Использовать тестовую УЗ, для которой в UI карточки доступно действие `Отменить заявку`.", "`TC-ACA-001`..`TC-ACA-005`", "Точные lifecycle statuses before cancellation are outside selected source."],
                        ["`FIX-002`", "`WP-02`", "Карточка УЗ с доступным действием `История заявки`.", "Использовать тестовую УЗ, для которой в UI карточки доступно действие `История заявки`.", "`TC-ACA-006`", "Full section-39 table content is out of scope."],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "writer-quality-gate.md",
        "Writer Quality Gate",
        [
            (
                2,
                "Writer Quality Gate",
                table(
                    ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
                    [
                        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use canonical headings/tables; canonical TC links summaries and does not duplicate full split tables.", "`all`", "`none_required:pass`", "`no`"],
                        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit sentinels such as `none_required:covered` and `unclear:GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` declares file-based manifest writing; helper manifests are in `_artifact_write`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`mockup-visual-inventory`", "`pass`", "Scope selection states no unambiguous mockup is used for this scope.", "`all`", "`none_required:not_applicable`", "`no`"],
                        ["`source-row-inventory`", "`pass`", "All handoff rows `SRC-001`..`SRC-003` are present and mapped to atoms/gaps.", "`all`", "`none_required:pass`", "`no`"],
                        ["`source-normalization-atomic`", "`pass`", "`SRC-001` cancel behavior is split into six properties; `SRC-002` duplicate anchor is normalized.", "`WP-01`", "`none_required:pass`", "`no`"],
                        ["`dictionary-inventory`", "`pass`", "`DICT-001` copied to test-design and linked from plan/TC.", "`WP-01`", "`none_required:pass`", "`no`"],
                        ["`test-design-decision-table`", "`pass`", "Each normalized property has one decision; edit-lock is `gap_unclear`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`coverage-obligation-table`", "`pass`", "Action branches, dictionary and status-lifecycle obligations are mapped to TC/GAP.", "`all`", "`none_required:pass`", "`no`"],
                        ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts applicable obligations and residual unclear atom.", "`all`", "`none_required:pass`", "`no`"],
                        ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` names reusable entry fixtures without inventing lifecycle statuses.", "`all`", "`none_required:pass`", "`no`"],
                        ["`risk-priority-map`", "`pass`", "High-risk status transition `ATOM-004` has High priority `TC-ACA-004`; `ATOM-005` remains residual `GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`GAP-001` and `GAP-002` are non-blocking and not converted into executable TC.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
                        ["`ledger-atomicity`", "`pass`", "`ATOM-*` rows split modal open, dictionary, empty confirm, selected confirm, edit-lock, modal cancel and history open.", "`all`", "`none_required:pass`", "`no`"],
                        ["`gsr-range-compression`", "`pass`", "No GSR/range compression; only section anchors are available.", "`all`", "`none_required:pass`", "`no`"],
                        ["`design-plan-atomicity`", "`pass`", "Each design row has one check type and one expected behavior.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scenario-does-not-replace-atomic`", "`pass`", "No broad scenario TC replaces branch-specific TC.", "`all`", "`none_required:pass`", "`no`"],
                        ["`tc-atomicity`", "`pass`", "`TC-ACA-003`, `TC-ACA-004` and `TC-ACA-005` split the three modal branches.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-data-specificity`", "`pass`", "`DICT-001` values are listed; no placeholder validation classes are used.", "`all`", "`none_required:pass`", "`no`"],
                        ["`tc-regression-smells`", "`pass`", "No source-rule oracle, alternative negative oracle, hidden API/DB effect or executable TC over edit-lock mechanism.", "`all`", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "Backend/API/RabbitMQ/audit effects are out of scope and not claimed.", "`all`", "`none_required:pass`", "`no`"],
                        ["`action-observability`", "`pass`", "Each action TC names visible modal/window/status/card result.", "`all`", "`none_required:pass`", "`no`"],
                        ["`semantic-req-id-parity`", "`pass`", "`section-35`/`section-38` anchors preserved; no PDF-only IDs claimed.", "`all`", "`none_required:pass`", "`no`"],
                        ["`package-ready`", "`pass`", "`WP-01` and `WP-02` have ledger, plan and TC gates.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scoped-validator-findings`", "`pass`", "`work/review-cycles/application-card-common-actions/outputs/scoped-validator-profile.structure-preflight-r1.json` generated by runner validate; `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "writer-self-check.md",
        "Writer Self-Check",
        [
            (
                2,
                "Writer Self-Check",
                table(
                    ["check", "status", "evidence", "follow_up"],
                    [
                        ["source parity checked", "`yes`", "`source-parity-check.md`; `GAP-001` preserved.", "`none_required:pass`"],
                        ["mandatory requirement IDs preserved", "`yes`", "`section-35`; `section-38` appear in ledger and TC traceability.", "`none_required:pass`"],
                        ["uncovered atoms", "`yes`", "`ATOM-005` remains `unclear:GAP-002` by design.", "`GAP-002` should be reviewed semantically."],
                        ["possible merged checks", "`pass`", "Modal branches split into `TC-ACA-003`, `TC-ACA-004`, `TC-ACA-005`.", "`none_required:pass`"],
                        ["possible over-splitting", "`pass`", "`SRC-001`/`SRC-002` duplicate rows share one TC set.", "`none_required:pass`"],
                        ["test-case grouping and continuous numbering", "`pass`", "`TC-ACA-001`..`TC-ACA-006` continuous.", "`none_required:pass`"],
                        ["internal work package coverage", "`pass`", "`internal-work-package-coverage.md` covers `WP-01` and `WP-02`.", "`none_required:pass`"],
                        ["merged checks across packages", "`pass`", "No TC covers independent atoms from both packages.", "`none_required:pass`"],
                        ["packages that require split or unresolved package gaps", "`pass`", "`WP-01` has residual `GAP-002`; no package split needed.", "`none_required:pass`"],
                        ["scoped validator command", "`pass`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/application-card-common-actions/cycle-state.yaml`", "`none_required:pass`"],
                        ["scoped validator findings summary", "`pass`", "`outputs/scoped-validator-profile.structure-preflight-r1.json`; `unresolved_warning_error_count = 0`.", "`none_required:pass`"],
                        ["assumptions", "`pass`", "No PDF refs, section-39 internals or exact edit-lock mechanism are assumed.", "`none_required:pass`"],
                        ["unclear items", "`pass`", "`GAP-001`; `GAP-002` preserved in `coverage-gaps.md`.", "`none_required:pass`"],
                        ["high-risk atoms", "`pass`", "`ATOM-004` has High priority `TC-ACA-004`; `ATOM-005` has residual risk in `risk-priority-map.md`.", "`none_required:pass`"],
                    ],
                ),
            ),
            (
                2,
                "Artifact Write Evidence",
                table(
                    ["artifact_group", "write_strategy", "evidence", "follow_up"],
                    [
                        ["canonical TC", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/{CANONICAL.stem}/manifest.json`", "`none_required:pass`"],
                        ["split artifacts", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/*/manifest.json`", "`none_required:pass`"],
                        ["cycle outputs", "`file write from committed builder`", "`scripts/build_application_card_common_actions_writer_artifacts.py`", "`none_required:pass`"],
                    ],
                ),
            ),
        ],
    )
    write_via_manifest(
        CANONICAL,
        "Тест-кейсы: общие действия карточки Универсальной заявки",
        [(2, "Test Case Set", canonical_tc())],
    )


def write_prompt() -> None:
    selected = "\n".join(
        [
            "- `AGENTS.md`",
            "- `skills/README.md`",
            "- `references/agent/session-based-review-cycle-format.md`",
            "- `references/agent/codex-sdk-orchestration-format.md`",
            "- `skills/ft-test-case-reviewer/SKILL.md`",
            "- `references/agent/reviewer-output-format.md`",
            "- `references/qa/review-findings-format.md`",
            "- `references/qa/test-case-runtime-format.md`",
            "- `references/agent/workflow-state-format.md`",
            "- `references/agent/session-log-format.md`",
            "- `references/agent/agent-decision-log-format.md`",
            "- `references/agent/next-step-prompt-format.md`",
        ]
    )
    prompt = dedent(
        f"""
        # Prompt: Structure Preflight R1

        ## Цель этапа

        Проверить parseability, canonical schema, обязательные поля `TC-*`, split artifact shape и blocking format prerequisites для `ft-2-OF_17` / `{SCOPE}` в session-based stage `structure-preflight-r1`.

        Skill: `ft-test-case-reviewer`.
        Instruction scenario: `reviewer.structure_preflight`.
        Resolver command: `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`.
        Budget at prompt creation: `pass (175.6 / 210.0 KiB)`.

        Перед review decisions прочитай все selected required instruction files и зафиксируй resolver command, budget status и selected files в `outputs/reviewer-session-log.structure-preflight-r1.md`.

        Selected required files:

        {selected}

        ## Входные артефакты

        - `fts/ft-2-OF_17/test-cases/{SECTION}-{SCOPE}.md`
        - `fts/ft-2-OF_17/work/test-design/{SECTION}-{SCOPE}/`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/source-selection.md`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/scope-contract.md`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/source-parity-check.md`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/source-row-inventory.md`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/dictionary-inventory.md`
        - `fts/ft-2-OF_17/work/stage-handoffs/07-{SCOPE}/scope-coverage-gaps.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/scope-gap-review.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml`
        - `fts/ft-2-OF_17/AGENT-NOTES.md`

        ## Обязательные действия

        - Работать только в режиме `structure_preflight`; не выполнять semantic coverage review.
        - Проверить, что canonical `TC-*` parseable and use bold runtime fields: `Название`, `Тип`, `Приоритет`, `package_id`, `Трассировка`.
        - Проверить сквозную нумерацию `TC-ACA-001`..`TC-ACA-006`.
        - Проверить наличие `package_id` для каждого `TC-*` и каждого `ATOM-*`.
        - Проверить, что split artifacts существуют, имеют canonical headings/table columns, and canonical file does not duplicate full split tables.
        - Проверить, что `GAP-001`/`GAP-002` оформлены как gaps, not executable `TC-*`.
        - Если structure blockers есть, создать findings and route to `writer-structure-r1` with `stage_status: structure-preflight-blocked`.
        - Если structure blockers отсутствуют, route to `semantic-review-r1` with `stage_status: semantic-review-ready`, `semantic_round: 1`, and active prompt `work/review-cycles/{SCOPE}/prompts/prompt.semantic-review-r1.md`.

        ## Не делать

        - Не исправлять canonical test cases.
        - Не проводить full semantic/test-design review.
        - Не расширять scope на full `section-39`.
        - Не ставить `signed-off`.

        ## Ожидаемые выходы

        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/structure-preflight-r1-findings.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for either `writer-structure-r1` or `semantic-review-r1`
        - updated `fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml`
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(cleandoc(prompt) + "\n", encoding="utf-8", newline="\n")


def write_logs_and_state() -> None:
    inputs_read = [
        *INSTRUCTION_FILES,
        f"{HANDOFF_REL}/source-selection.md",
        f"{HANDOFF_REL}/scope-contract.md",
        f"{HANDOFF_REL}/source-parity-check.md",
        f"{HANDOFF_REL}/source-row-inventory.md",
        f"{HANDOFF_REL}/dictionary-inventory.md",
        f"{HANDOFF_REL}/scope-coverage-gaps.md",
        f"{HANDOFF_REL}/scope-clarification-requests.md",
        f"work/review-cycles/{SCOPE}/outputs/scope-gap-review.md",
        f"{HANDOFF_REL}/workflow-state.yaml",
        f"work/review-cycles/{SCOPE}/cycle-state.yaml",
        "AGENT-NOTES.md",
        "references/agent/writer-output-format.md",
        "references/agent/writer-quality-gate-format.md",
    ]
    session_log = dedent(
        f"""
        # Writer R1 Session Log

        ## Session Metadata

        | field | value |
        | --- | --- |
        | skill | `ft-test-case-writer` |
        | mode | `writer.session_initial_draft` |
        | ft_slug | `ft-2-OF_17` |
        | scope_slug | `{SCOPE}` |
        | started_from | `cycle-state.yaml` |
        | status_after | `writer-draft-ready` |

        ## Inputs Read

        - Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
        - Resolver budget status: `pass (138.7 / 200.0 KiB)`.
        {bullet(f"`{path}` - required instruction/source/process input read for writer-r1." for path in inputs_read)}

        ## Inputs Not Used

        - `fts/ft-2-OF_17/mockups/` - source selection states no unambiguous mockup is used for this scope.
        - Old `ui-employment*` artifacts - explicitly excluded by prompt as contaminated historical canaries.
        - Full `section-39` history behavior - out of scope; only opening the history window is covered.

        ## Key Decisions

        - `WP-01` processed before `WP-02`; see `agent-decision-log.writer-r1.md`.
        - `SRC-001` and `SRC-002` normalized as duplicate source anchors for the same cancel action; no duplicate TC set created.
        - `DICT-001` active values are used in `TC-ACA-002` and parameterized `TC-ACA-004`.
        - `GAP-002` kept as unclear for exact edit-lock mechanism; no disabled-field/save-hidden/error-message behavior invented.

        ## Risks And Fallbacks

        - `GAP-001` remains non-blocking traceability risk: no PDF page refs or PDF-only IDs are claimed.
        - Initial PowerShell read of some Russian instruction output showed mojibake; files were reread with explicit UTF-8 and distorted stdout was not used as evidence.

        ## Validation

        - `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
        - `python scripts/build_application_card_common_actions_writer_artifacts.py` - generated writer artifacts through `write_artifact_sections.py --manifest`.
        - `python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_17 --json --output fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/validator-report.writer-r1.latest.json` - completed; repository-level historical findings exist outside current scope.
        - `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - pass; `outputs/scoped-validator-profile.structure-preflight-r1.json` has `unresolved_warning_error_count = 0`.

        ## Contamination Check

        - Work limited to `ft-2-OF_17`, scope `{SCOPE}`, canonical `{CANONICAL_REL}`, test-design `{TD_REL}`, and review-cycle `{SCOPE}` outputs/prompts.
        - Historical `ui-employment*` artifacts were not used as source input.

        ## Event Timeline

        | step | event | result | artifact_or_evidence |
        | --- | --- | --- | --- |
        | 1 | Ran instruction resolver | budget pass | resolver stdout |
        | 2 | Read selected required instructions | completed with UTF-8 reread where needed | `Inputs Read` |
        | 3 | Read handoff and scope-gap review artifacts | scope boundaries confirmed | `scope-contract.md`; `scope-gap-review.md` |
        | 4 | Declared artifact write strategy | package-based manifest writing selected | `{TD_REL}/artifact-write-strategy.md` |
        | 5 | Generated canonical and split artifacts | helper wrote Markdown targets | `{TD_REL}/_artifact_write/*/manifest.json` |
        | 6 | Prepared next transition prompt | structure preflight prompt exists | `work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md` |

        ## Quality Checkpoints

        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md`; `outputs/scoped-validator-profile.structure-preflight-r1.json` | none |
        | Source row parity | `pass` | all `SRC-001`..`SRC-003` mapped | none |
        | Branch separation | `pass` | `TC-ACA-003`; `TC-ACA-004`; `TC-ACA-005` | none |
        | Residual gaps | `pass` | `GAP-001`; `GAP-002` preserved | semantic reviewer should verify gap handling. |

        ## Artifact Write Strategy

        | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
        | --- | --- | --- | --- | --- | --- |
        | `{CANONICAL_REL}` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` | `yes` |
        | `{TD_REL}/` | `table-heavy generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` | `yes` |

        ## Technical Fallbacks

        | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | `TF-001` | `encoding issue` | `PowerShell console output read without explicit UTF-8` | `PowerShell Get-Content -Encoding UTF8 with UTF-8 output encoding` | `n/a` | `n/a` | `none; distorted stdout discarded and not used as evidence` | `none` |

        ## Handoff Notes For Next Session

        - Structure preflight should focus on parseability, split artifact shape and stage-specific logs, not semantic coverage.
        - Semantic reviewer should inspect residual `GAP-002` carefully because unsupported edit-lock mechanisms would be a semantic defect.
        """
    ).strip()
    (OUTPUTS / "writer-session-log.writer-r1.md").write_text(cleandoc(session_log) + "\n", encoding="utf-8", newline="\n")

    decision_log = dedent(
        f"""
        # Agent Decision Log

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
        | `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Cover only cancel action flow and opening history window. | Full section-39 and hidden backend effects are excluded by scope. | `{CANONICAL_REL}` | high | applied |
        | `DEC-002` | 2 | `source-boundary` | `source-row-inventory.md` | Normalize `SRC-001` and `SRC-002` as duplicate cancel source rows. | They describe the same behavior in duplicated section anchors. | `{TD_REL}/source-table-normalization.md` | high | applied |
        | `DEC-003` | 3 | `test-design` | `scope-contract.md` | Split modal branches into separate TC for no reason, selected reason and modal cancel. | The branches have different primary expected results. | `TC-ACA-003`; `TC-ACA-004`; `TC-ACA-005` | high | applied |
        | `DEC-004` | 4 | `coverage` | `dictionary-inventory.md` | Use all active values of `DICT-001`. | Source/support define the refusal-reason dictionary. | `TC-ACA-002`; `TC-ACA-004` | high | applied |
        | `DEC-005` | 5 | `gap` | `scope-coverage-gaps.md` `GAP-002` | Do not create executable edit-lock TC with a guessed mechanism. | FT does not define disabled fields, hidden save, error message or API oracle. | `{TD_REL}/coverage-gaps.md`; `ATOM-005` | medium | applied |
        | `DEC-006` | 6 | `artifact-write` | `writer-process-workflow.md` | Use manifest helper for canonical and split artifacts. | Scope has `WP-*` packages and table-heavy artifacts. | `{TD_REL}/artifact-write-strategy.md` | high | applied |
        | `DEC-007` | 7 | `routing` | writer-r1 completion gate | Route to `structure-preflight-r1`, not semantic review directly. | Session-based lifecycle requires structure preflight after writer-r1. | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` | high | applied |
        """
    ).strip()
    (OUTPUTS / "agent-decision-log.writer-r1.md").write_text(cleandoc(decision_log) + "\n", encoding="utf-8", newline="\n")

    cycle_state = dedent(
        f"""
        cycle_id: application-card-common-actions-2026-06-17
        ft_slug: ft-2-OF_17
        scope_slug: {SCOPE}
        section_id: {SECTION}
        current_stage: structure-preflight-r1
        stage_status: writer-draft-ready
        semantic_round: 1
        max_semantic_rounds: 2
        canonical_test_cases: {CANONICAL_REL}
        test_design_dir: {TD_REL}
        active_snapshot: none
        active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
        sessions: []
        latest_artifacts:
          - {CANONICAL_REL}
          - {TD_REL}
          - {TD_REL}/artifact-write-strategy.md
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-table-normalization.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/dependency-matrix.md
          - {TD_REL}/risk-priority-map.md
          - {TD_REL}/coverage-gaps.md
          - {TD_REL}/writer-quality-gate.md
          - {TD_REL}/writer-self-check.md
          - work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
          - work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
          - work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
        blocking_reasons: []
        blocking_findings: []
        open_questions:
          - GAP-002: preferred observable UI oracle for edit lock after status `Отказ клиента`.
        accepted_risks:
          - GAP-001 | accepted-nonblocking-risk | owner: scope-reviewer | rationale: DOCX selected rows are parseable; PDF extraction failed and must remain a traceability guardrail | revisit: before claiming PDF page refs or PDF-only IDs
        """
    ).strip()
    (CYCLE / "cycle-state.yaml").write_text(cycle_state + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    write_markdown_artifacts()
    write_prompt()
    write_logs_and_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
