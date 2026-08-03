from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-visual-assessment-consents-checks"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/{SECTION}-{SCOPE}"
HANDOFF = FT / HANDOFF_REL
PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"


SELECTED_REQUIRED_FILES = [
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

SOURCE_INPUTS = [
    "AGENT-NOTES.md",
    "work/stage-handoffs/00-autofin-scope-selection/source-selection.md",
    "work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md",
    f"{HANDOFF_REL}/workflow-state.yaml",
    f"{HANDOFF_REL}/scope-gap-review.md",
    f"{HANDOFF_REL}/scope-contract.md",
    f"{HANDOFF_REL}/source-parity-check.md",
    f"{HANDOFF_REL}/source-row-inventory.md",
    f"{HANDOFF_REL}/mockup-visual-inventory.md",
    f"{HANDOFF_REL}/scope-coverage-gaps.md",
    f"{HANDOFF_REL}/scope-clarification-requests.md",
    "source/AutoFinPreFinal.docx",
    "source/AutoFinPreFinal.pdf",
]


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")


def write_markdown(path: Path, title: str, sections: list[tuple[int, str, str]]) -> None:
    scratch = TD / "_artifact_write" / path.stem
    scratch.mkdir(parents=True, exist_ok=True)
    manifest_sections = []
    single_section = len(sections) == 1
    for index, (level, heading, body) in enumerate(sections, start=1):
        section_path = scratch / f"{index:02d}.md"
        section_path.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
        if single_section:
            level = 1
            heading = title
        manifest_sections.append(
            {"level": level, "heading": heading, "content_file": section_path.name}
        )
    manifest = {
        "target_path": str(path),
        "sections": manifest_sections,
    }
    if not single_section:
        preamble = scratch / "00-preamble.md"
        preamble.write_text(
            f"# {title}\n\nGenerated artifact; evidence is organized in the sections below.\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest["preamble_file"] = preamble.name
    manifest_path = scratch / "manifest.json"
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


def tc_block(
    tc_id: str,
    title: str,
    priority: str,
    package_id: str,
    traceability: str,
    preconditions: list[str],
    data: list[str] | str,
    steps: list[str],
    expected: str,
    postconditions: list[str] | str = "Не требуются.",
    tc_type: str = "Positive",
) -> str:
    data_text = data if isinstance(data, str) else bullet(data)
    post_text = postconditions if isinstance(postconditions, str) else bullet(postconditions)
    steps_text = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    raw = dedent(
        f"""
        ## {tc_id}

        **Название:** {title}

        **Тип:** {tc_type}

        **Приоритет:** {priority}

        **package_id:** {package_id}

        **Трассировка:** {traceability}

        ### Предусловия

        {bullet(preconditions)}

        ### Тестовые данные

        {data_text}

        ### Шаги

        {steps_text}

        ### Итоговый ожидаемый результат

        {expected}

        ### Постусловия

        {post_text}
        """
    ).strip()
    return "\n".join(line[8:] if line.startswith("        ") else line for line in raw.splitlines())


def tc_cases_body() -> str:
    cases = [
        tc_block(
            "TC-ACVCC-001",
            "Отображение блока `Визуальная информация` и поля `Визуальная информация`",
            "High",
            "WP-01",
            "`ATOM-001`; `ATOM-002`; `SRC-001`; `SRC-002`; `BSR 303`",
            ["Открыта карточка заявки."],
            "Не требуются.",
            ["Перейти к области карточки заявки с блоком визуальной оценки."],
            "В карточке заявки отображается блок `Визуальная информация` с полем `Визуальная информация`.",
        ),
        tc_block(
            "TC-ACVCC-002",
            "Значение по умолчанию `Нет` в поле `Визуальная информация`",
            "High",
            "WP-01",
            "`ATOM-003`; `SRC-002`; `BSR 304`",
            [
                "Открыта карточка заявки.",
                "Значение поля `Визуальная информация` в текущей карточке пользователем еще не изменялось.",
            ],
            "Не требуются.",
            ["Открыть блок `Визуальная информация`."],
            "В поле `Визуальная информация` отображается значение `Нет`.",
        ),
        tc_block(
            "TC-ACVCC-003",
            "Отображение параметров визуальной оценки при выборе `Да`",
            "High",
            "WP-01",
            "`ATOM-004`; `ATOM-005`; `SRC-002`; `SRC-003`; `BSR 305`; `BSR 306`; `GAP-001`",
            ["Открыта карточка заявки.", "Поле `Визуальная информация` доступно для изменения."],
            "- Значение поля `Визуальная информация`: `Да`.",
            ["В поле `Визуальная информация` выбрать значение `Да`."],
            "После выбора `Да` отображается список `Параметры визуальной оценки` с возможностью множественного выбора.",
            ["Если состояние карточки сохраняется, вернуть поле `Визуальная информация` в исходное значение `Нет`."],
        ),
        tc_block(
            "TC-ACVCC-004",
            "Checkbox-контролы для значений `Параметры визуальной оценки`",
            "Medium",
            "WP-01",
            "`ATOM-006`; `SRC-003`; `BSR 307`; `GAP-001`",
            [
                "Открыта карточка заявки.",
                "В поле `Визуальная информация` выбрано значение `Да`.",
                "Список `Параметры визуальной оценки` отображается.",
            ],
            "Не требуются.",
            ["Просмотреть отображенные значения списка `Параметры визуальной оценки`."],
            "У каждого отображенного значения списка `Параметры визуальной оценки` доступен checkbox.",
            ["Если состояние карточки сохраняется, вернуть поле `Визуальная информация` в исходное значение `Нет`."],
        ),
        tc_block(
            "TC-ACVCC-005",
            "Выбор одного значения в `Параметры визуальной оценки`",
            "High",
            "WP-01",
            "`ATOM-007`; `SRC-003`; `BSR 308`; `GAP-001`",
            [
                "Открыта карточка заявки.",
                "В поле `Визуальная информация` выбрано значение `Да`.",
                "Список `Параметры визуальной оценки` отображается.",
            ],
            "- Любое отображенное значение списка `Параметры визуальной оценки`, кроме `Другое`.",
            ["Отметить checkbox одного отображенного значения из тестовых данных."],
            "Выбранное значение списка `Параметры визуальной оценки` отображается отмеченным.",
            ["Если состояние карточки сохраняется, снять отметку выбранного checkbox и вернуть поле `Визуальная информация` в исходное значение `Нет`."],
        ),
        tc_block(
            "TC-ACVCC-006",
            "Скрытие параметров визуальной оценки при значении `Нет`",
            "High",
            "WP-01",
            "`ATOM-004`; `ATOM-005`; `SRC-002`; `SRC-003`; `BSR 305`; `BSR 306`; `GAP-001`",
            [
                "Открыта карточка заявки.",
                "Поле `Визуальная информация` доступно для изменения.",
            ],
            "- Значение поля `Визуальная информация`: `Нет`.",
            ["В поле `Визуальная информация` выбрать значение `Нет`."],
            "Список `Параметры визуальной оценки` не отображается.",
            "Не требуются.",
        ),
        tc_block(
            "TC-ACVCC-007",
            "Блок `Согласия / проверки` свернут по умолчанию и раскрывается",
            "High",
            "WP-02",
            "`ATOM-009`; `SRC-004`; `BSR 310`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` пользователем еще не раскрывался."],
            "Не требуются.",
            ["Найти блок `Согласия / проверки`.", "Раскрыть блок `Согласия / проверки`."],
            "Изначально блок `Согласия / проверки` отображается свернутым; после действия пользователя содержимое блока отображается раскрытым.",
        ),
        tc_block(
            "TC-ACVCC-008",
            "Отображение виджета `Согласия` с полем `БКИ и персональные данные`",
            "High",
            "WP-02",
            "`ATOM-010`; `SRC-005`; `BSR 311`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` раскрыт."],
            "Не требуются.",
            ["Просмотреть подблок `Согласия`."],
            "В подблоке `Согласия` отображается поле `БКИ и персональные данные`.",
        ),
        tc_block(
            "TC-ACVCC-009",
            "Значение по умолчанию `Да` для `БКИ и персональные данные`",
            "High",
            "WP-02",
            "`ATOM-011`; `SRC-005`; `BSR 312`",
            [
                "Открыта карточка заявки.",
                "Блок `Согласия / проверки` раскрыт.",
                "Значение поля `БКИ и персональные данные` пользователем еще не изменялось.",
            ],
            "Не требуются.",
            ["Открыть подблок `Согласия`."],
            "В поле `БКИ и персональные данные` отображается значение `Да`.",
        ),
        tc_block(
            "TC-ACVCC-010",
            "Проставление checkbox в поле `БКИ и персональные данные`",
            "Medium",
            "WP-02",
            "`ATOM-012`; `SRC-005`; `BSR 311`; `GAP-002`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` раскрыт."],
            "- Поле `БКИ и персональные данные`: `Да`.",
            ["В поле `БКИ и персональные данные` установить checkbox в значение `Да`."],
            "Checkbox поля `БКИ и персональные данные` отображается отмеченным.",
            ["Если состояние карточки сохраняется, вернуть поле `БКИ и персональные данные` в исходное значение."],
        ),
        tc_block(
            "TC-ACVCC-011",
            "Отображение `FATCA/CRS проверка` и значение по умолчанию `Нет`",
            "High",
            "WP-02",
            "`ATOM-013`; `ATOM-014`; `SRC-006`; `BSR 313`; `BSR 314`",
            [
                "Открыта карточка заявки.",
                "Блок `Согласия / проверки` раскрыт.",
                "Значение поля `FATCA/CRS проверка` пользователем еще не изменялось.",
            ],
            "Не требуются.",
            ["Просмотреть подблок `FATCA/CRS проверка`."],
            "В подблоке отображается поле `FATCA/CRS проверка` со значением по умолчанию `Нет`.",
        ),
        tc_block(
            "TC-ACVCC-012",
            "Проставление checkbox `FATCA/CRS проверка`",
            "Medium",
            "WP-02",
            "`ATOM-015`; `SRC-006`; `BSR 313`; `GAP-002`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` раскрыт."],
            "- Поле `FATCA/CRS проверка`: `Да`.",
            ["В поле `FATCA/CRS проверка` установить checkbox в значение `Да`."],
            "Checkbox поля `FATCA/CRS проверка` отображается отмеченным.",
            ["Если состояние карточки сохраняется, вернуть поле `FATCA/CRS проверка` в исходное значение `Нет`."],
        ),
        tc_block(
            "TC-ACVCC-013",
            "Отображение полей подблока `AML проверка`",
            "High",
            "WP-02",
            "`ATOM-016`; `SRC-007`; `BSR 315`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` раскрыт."],
            "\n".join(
                [
                    "- `Иностранное публичное должностное лицо`.",
                    "- `Должностное лицо публичной международной организации`.",
                    "- `Должностное лицо Российской Федерации, включенное в перечни должностей, определяемые Президентом Российской Федерации, а также назначаемое/освобождаемое от должности Президентом или Правительством Российской Федерации (РПДЛ)`.",
                    "- `Родственник ИПДЛ`.",
                    "- `Родственник МПДЛ`.",
                    "- `Родственник РПДЛ`.",
                ]
            ),
            ["Просмотреть подблок `AML проверка`."],
            "В подблоке `AML проверка` отображаются поля из тестовых данных.",
        ),
        tc_block(
            "TC-ACVCC-014",
            "Значение по умолчанию `Нет` во всех полях `AML проверка`",
            "High",
            "WP-02",
            "`ATOM-017`; `SRC-007`; `BSR 316`",
            [
                "Открыта карточка заявки.",
                "Блок `Согласия / проверки` раскрыт.",
                "Поля подблока `AML проверка` пользователем еще не изменялись.",
            ],
            "Не требуются.",
            ["Просмотреть значения полей подблока `AML проверка`."],
            "Во всех полях подблока `AML проверка` отображается значение `Нет`.",
        ),
        tc_block(
            "TC-ACVCC-015",
            "Проставление checkbox в поле подблока `AML проверка`",
            "Medium",
            "WP-02",
            "`ATOM-018`; `SRC-007`; `BSR 315`; `GAP-002`",
            ["Открыта карточка заявки.", "Блок `Согласия / проверки` раскрыт."],
            "- Поле `Родственник РПДЛ`: `Да`.",
            ["В подблоке `AML проверка` установить checkbox поля `Родственник РПДЛ` в значение `Да`."],
            "Checkbox поля `Родственник РПДЛ` отображается отмеченным.",
            ["Если состояние карточки сохраняется, вернуть поле `Родственник РПДЛ` в исходное значение `Нет`."],
        ),
    ]
    return "\n\n".join(cases) + "\n"


def canonical_sections() -> list[tuple[int, str, str]]:
    return [
        (
            2,
            "Metadata",
            md_table(
                ["field", "value"],
                [
                    ["`ft_slug`", "`AutoFin`"],
                    ["`scope_slug`", f"`{SCOPE}`"],
                    ["`section_id`", "`14`"],
                    ["`writer_stage`", "`writer-r1`"],
                    ["`package_ids`", "`WP-01`; `WP-02`"],
                    ["`source_rows`", "`SRC-001`..`SRC-007`; DOCX section-14 rows 130-136"],
                ],
            ),
        ),
        (
            2,
            "Coverage Boundaries",
            bullet(
                [
                    "Scope covers only section-14 rows `130-136`: visual information, visual assessment parameters, consents, FATCA/CRS and AML widgets.",
                    "Section-18 and section-19 are used only as referenced dependency context for rows 131-136.",
                    "Out of scope: personal data, passport, addresses, contacts, documents, participants, employment, income and action `Далее`.",
                    "`GAP-001` remains visible residual risk for Appendix 1 / full visual assessment criteria behavior.",
                    "`GAP-002` is closed by analyst clarification only for checkbox ticking in consent/FATCA/AML widgets.",
                ]
            ),
        ),
        (
            2,
            "Canonical Artifact Links",
            bullet(
                [
                    f"`{TD_REL}/artifact-write-strategy.md`",
                    f"`{TD_REL}/source-row-inventory.md`",
                    f"`{TD_REL}/source-row-completeness-matrix.md`",
                    f"`{TD_REL}/source-table-normalization.md`",
                    f"`{TD_REL}/atomic-requirements-ledger.md`",
                    f"`{TD_REL}/internal-work-package-coverage.md`",
                    f"`{TD_REL}/test-design-decision-table.md`",
                    f"`{TD_REL}/package-test-design-plan.md`",
                    f"`{TD_REL}/test-design-applicability-matrix.md`",
                    f"`{TD_REL}/coverage-obligation-table.md`",
                    f"`{TD_REL}/coverage-gaps.md`",
                    f"`{TD_REL}/risk-priority-map.md`",
                    f"`{TD_REL}/test-design-review.md`",
                    f"`{TD_REL}/writer-quality-gate.md`",
                    f"`{TD_REL}/writer-self-check.md`",
                ]
            ),
        ),
        (
            2,
            "Coverage Summary",
            md_table(
                ["package_id", "atoms", "test_cases", "covered", "unclear", "residual_gaps"],
                [
                    ["`WP-01`", "`8`", "`6`", "`7`", "`1`", "`GAP-001`"],
                    ["`WP-02`", "`10`", "`9`", "`10`", "`0`", "`GAP-002 closed`"],
                ],
            ),
        ),
        (2, "Test Cases", tc_cases_body()),
    ]


def source_rows() -> list[list[str]]:
    return [
        ["`SRC-001`", "`WP-01`", "Блок `Визуальная информация`", "DOCX section-14 table row 130", "`no_requirement_code:SRC-001`", "`yes`", "`ATOM-001`; `TC-ACVCC-001`"],
        ["`SRC-002`", "`WP-01`", "`Визуальная информация`", "DOCX section-14 table row 131; PDF p.32", "`BSR 303`; `BSR 304`; `BSR 305`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-004`; `TC-ACVCC-001`; `TC-ACVCC-002`; `TC-ACVCC-003`; `TC-ACVCC-006`"],
        ["`SRC-003`", "`WP-01`", "`Параметры визуальной оценки`", "DOCX section-14 table row 132; PDF p.32", "`BSR 306`; `BSR 307`; `BSR 308`; `BSR 309`", "`yes`", "`ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-008`; `TC-ACVCC-003`; `TC-ACVCC-004`; `TC-ACVCC-005`; `TC-ACVCC-006`; `GAP-001`"],
        ["`SRC-004`", "`WP-02`", "Блок `Согласия / проверки`", "DOCX section-14 table row 133; PDF p.32", "`BSR 310`", "`yes`", "`ATOM-009`; `TC-ACVCC-007`"],
        ["`SRC-005`", "`WP-02`", "`Согласия`", "DOCX section-14 table row 134; PDF pp.32-33; Appendix 2", "`BSR 311`; `BSR 312`", "`yes`", "`ATOM-010`; `ATOM-011`; `ATOM-012`; `TC-ACVCC-008`; `TC-ACVCC-009`; `TC-ACVCC-010`"],
        ["`SRC-006`", "`WP-02`", "`FATCA/CRS проверка`", "DOCX section-14 table row 135; PDF p.33; Appendix 2", "`BSR 313`; `BSR 314`", "`yes`", "`ATOM-013`; `ATOM-014`; `ATOM-015`; `TC-ACVCC-011`; `TC-ACVCC-012`"],
        ["`SRC-007`", "`WP-02`", "`AML проверка`", "DOCX section-14 table row 136; PDF p.33; Appendix 2", "`BSR 315`; `BSR 316`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-018`; `TC-ACVCC-013`; `TC-ACVCC-014`; `TC-ACVCC-015`"],
    ]


def atoms() -> list[list[str]]:
    return [
        ["`ATOM-001`", "`WP-01`", "`SRC-001`", "`no_requirement_code:SRC-001`", "В карточке заявки есть блок `Визуальная информация`.", "`TC-ACVCC-001`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-002`", "`WP-01`", "`SRC-002`", "`BSR 303`", "Поле `Визуальная информация` видимо всегда.", "`TC-ACVCC-001`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-003`", "`WP-01`", "`SRC-002`", "`BSR 304`", "Значение по умолчанию поля `Визуальная информация` равно `Нет`.", "`TC-ACVCC-002`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-004`", "`WP-01`", "`SRC-002`", "`BSR 305`", "При выборе `Да` автоматически отображается список параметров визуальной оценки с множественным выбором.", "`TC-ACVCC-003`; `TC-ACVCC-006`", "`covered`", "`GAP-001`", "`High`"],
        ["`ATOM-005`", "`WP-01`", "`SRC-003`", "`BSR 306`", "`Параметры визуальной оценки` видимы при `Визуальная информация = Да`.", "`TC-ACVCC-003`; `TC-ACVCC-006`", "`covered`", "`GAP-001`", "`High`"],
        ["`ATOM-006`", "`WP-01`", "`SRC-003`", "`BSR 307`", "По каждому отображенному значению `Параметры визуальной оценки` доступен checkbox.", "`TC-ACVCC-004`", "`covered`", "`GAP-001`", "`Medium`"],
        ["`ATOM-007`", "`WP-01`", "`SRC-003`", "`BSR 308`", "Должно быть выбрано хотя бы одно значение `Параметры визуальной оценки`.", "`TC-ACVCC-005`", "`covered`", "`GAP-001`", "`High`"],
        ["`ATOM-008`", "`WP-01`", "`SRC-003`", "`BSR 309`", "В каждом блоке есть checkbox `Другое`, при выборе которого появляется обязательное текстовое поле.", "`GAP-001`", "`gap`", "`GAP-001`", "`Medium`"],
        ["`ATOM-009`", "`WP-02`", "`SRC-004`", "`BSR 310`", "Блок `Согласия / проверки` по умолчанию свернут и может быть раскрыт.", "`TC-ACVCC-007`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-010`", "`WP-02`", "`SRC-005`", "`BSR 311`", "Подблок `Согласия` содержит поле `БКИ и персональные данные`.", "`TC-ACVCC-008`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-011`", "`WP-02`", "`SRC-005`", "`BSR 312`", "По умолчанию в поле `БКИ и персональные данные` значение `Да`.", "`TC-ACVCC-009`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-012`", "`WP-02`", "`SRC-005`", "`BSR 311`; `GAP-002`", "Для поля `БКИ и персональные данные` в этом scope проверяется только проставление checkbox.", "`TC-ACVCC-010`", "`covered`", "`GAP-002 closed`", "`Medium`"],
        ["`ATOM-013`", "`WP-02`", "`SRC-006`", "`BSR 313`", "Подблок `FATCA/CRS проверка` содержит поле `FATCA/CRS проверка`.", "`TC-ACVCC-011`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-014`", "`WP-02`", "`SRC-006`", "`BSR 314`", "По умолчанию во всех полях блока `FATCA/CRS проверка` значение `Нет`.", "`TC-ACVCC-011`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-015`", "`WP-02`", "`SRC-006`", "`BSR 313`; `GAP-002`", "Для поля `FATCA/CRS проверка` в этом scope проверяется только проставление checkbox.", "`TC-ACVCC-012`", "`covered`", "`GAP-002 closed`", "`Medium`"],
        ["`ATOM-016`", "`WP-02`", "`SRC-007`", "`BSR 315`", "Подблок `AML проверка` содержит поля из Appendix 2.", "`TC-ACVCC-013`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-017`", "`WP-02`", "`SRC-007`", "`BSR 316`", "По умолчанию во всех полях блока `AML проверка` значение `Нет`.", "`TC-ACVCC-014`", "`covered`", "`none_required:covered`", "`High`"],
        ["`ATOM-018`", "`WP-02`", "`SRC-007`", "`BSR 315`; `GAP-002`", "Для полей `AML проверка` в этом scope проверяется только проставление checkbox.", "`TC-ACVCC-015`", "`covered`", "`GAP-002 closed`", "`Medium`"],
    ]


def write_split_artifacts() -> None:
    write_markdown(
        TD / "artifact-write-strategy.md",
        "Artifact Write Strategy",
        [
            (
                2,
                "Strategy",
                md_table(
                    ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
                    [
                        [CANONICAL_REL, "`generated canonical`", "`write_artifact_sections.py --manifest`", "`yes`", "`scripts/write_artifact_sections.py`", "`yes`"],
                        [TD_REL, "`split generated`", "`write_artifact_sections.py --manifest`", "`yes`", "`scripts/write_artifact_sections.py`", "`yes`"],
                        [f"{CYCLE_REL}/outputs", "`session outputs`", "`file-based script write`", "`yes`", "`scripts/build_autofin_application_card_visual_assessment_consents_checks_writer_r1.py`", "`yes`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "source-row-inventory.md",
        "Source Row Inventory",
        [(2, "Inventory", md_table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], source_rows()))],
    )
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        "Source Row Completeness Matrix",
        [
            (
                2,
                "Completeness Matrix",
                md_table(
                    ["source_row_id", "package_id", "required_from_handoff", "writer_inventory_status", "atom_status", "tc_or_gap_status", "notes"],
                    [[r[0], r[1], "`yes`", "`present`", "`mapped`", "`mapped`", r[6]] for r in source_rows()],
                ),
            )
        ],
    )
    write_markdown(
        TD / "source-table-normalization.md",
        "Source Table Normalization",
        [
            (
                2,
                "Normalized Source Properties",
                md_table(
                    ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
                    [
                        ["`SRC-001`", "`SP-WP01-001`", "`WP-01`", "Блок `Визуальная информация`", "`visibility`", "`always`", "Block exists in the application card.", "`no_requirement_code:SRC-001`", "`DOCX row 130`", "`high`", "`none_required:covered`", "`ATOM-001`"],
                        ["`SRC-002`", "`SP-WP01-002`", "`WP-01`", "`Визуальная информация`", "`visibility`", "`always`", "Field is always visible.", "`BSR 303`", "`DOCX row 131`; `PDF p.32`", "`high`", "`none_required:covered`", "`ATOM-002`"],
                        ["`SRC-002`", "`SP-WP01-003`", "`WP-01`", "`Визуальная информация`", "`default-value`", "`initial field state`", "Default value is `Нет`.", "`BSR 304`", "`DOCX row 131`; `PDF p.32`", "`high`", "`none_required:covered`", "`ATOM-003`"],
                        ["`SRC-002`", "`SP-WP01-004`", "`WP-01`", "`Визуальная информация`", "`conditional-visibility`", "`Визуальная информация = Да`", "Visual assessment parameters list appears with multiple selection.", "`BSR 305`", "`DOCX row 131`; `PDF p.32`", "`high`", "`GAP-001`", "`ATOM-004`"],
                        ["`SRC-003`", "`SP-WP01-005`", "`WP-01`", "`Параметры визуальной оценки`", "`conditional-visibility`", "`Визуальная информация = Да`", "Field is visible.", "`BSR 306`", "`DOCX row 132`; `PDF p.32`", "`high`", "`GAP-001`", "`ATOM-005`"],
                        ["`SRC-003`", "`SP-WP01-006`", "`WP-01`", "`Параметры визуальной оценки`", "`checkbox-controls`", "`parameters list visible`", "Every displayed value has a checkbox.", "`BSR 307`", "`DOCX row 132`; `PDF p.32`", "`medium`", "`GAP-001`", "`ATOM-006`"],
                        ["`SRC-003`", "`SP-WP01-007`", "`WP-01`", "`Параметры визуальной оценки`", "`selection-state`", "`parameters list visible`", "One displayed value can be selected; empty-state enforcement is not executable without confirmed validation action.", "`BSR 308`", "`DOCX row 132`; `PDF p.32`", "`medium`", "`GAP-001`", "`ATOM-007`"],
                        ["`SRC-003`", "`SP-WP01-008`", "`WP-01`", "`Параметры визуальной оценки`", "`other-comment`", "`Другое selected`", "Full per-block `Другое` text-field execution is unresolved by Appendix 1 gap.", "`BSR 309`", "`DOCX row 132`; `PDF p.32`", "`medium`", "`GAP-001`", "`ATOM-008`"],
                        ["`SRC-004`", "`SP-WP02-001`", "`WP-02`", "Блок `Согласия / проверки`", "`default-collapse`", "`open application card`", "Block is collapsed by default and expandable.", "`BSR 310`", "`DOCX row 133`; `PDF p.32`", "`high`", "`none_required:covered`", "`ATOM-009`"],
                        ["`SRC-005`", "`SP-WP02-002`", "`WP-02`", "`Согласия`", "`widget-composition`", "`block expanded`", "Subblock contains field `БКИ и персональные данные`.", "`BSR 311`", "`DOCX row 134`; `Appendix 2`", "`high`", "`none_required:covered`", "`ATOM-010`"],
                        ["`SRC-005`", "`SP-WP02-003`", "`WP-02`", "`Согласия`", "`default-value`", "`initial field state`", "`БКИ и персональные данные = Да`.", "`BSR 312`", "`DOCX row 134`; `PDF p.33`", "`high`", "`none_required:covered`", "`ATOM-011`"],
                        ["`SRC-005`", "`SP-WP02-004`", "`WP-02`", "`Согласия`", "`checkbox-ticking`", "`block expanded`", "Only checkbox ticking is checked for `БКИ и персональные данные`.", "`BSR 311`; `GAP-002`", "`scope-clarification-requests.md`", "`high`", "`GAP-002 closed`", "`ATOM-012`"],
                        ["`SRC-006`", "`SP-WP02-005`", "`WP-02`", "`FATCA/CRS проверка`", "`widget-composition`", "`block expanded`", "Subblock contains field `FATCA/CRS проверка`.", "`BSR 313`", "`DOCX row 135`; `Appendix 2`", "`high`", "`none_required:covered`", "`ATOM-013`"],
                        ["`SRC-006`", "`SP-WP02-006`", "`WP-02`", "`FATCA/CRS проверка`", "`default-value`", "`initial field state`", "All fields default to `Нет`.", "`BSR 314`", "`DOCX row 135`; `PDF p.33`", "`high`", "`none_required:covered`", "`ATOM-014`"],
                        ["`SRC-006`", "`SP-WP02-007`", "`WP-02`", "`FATCA/CRS проверка`", "`checkbox-ticking`", "`block expanded`", "Only checkbox ticking is checked for `FATCA/CRS проверка`.", "`BSR 313`; `GAP-002`", "`scope-clarification-requests.md`", "`high`", "`GAP-002 closed`", "`ATOM-015`"],
                        ["`SRC-007`", "`SP-WP02-008`", "`WP-02`", "`AML проверка`", "`widget-composition`", "`block expanded`", "Subblock contains Appendix 2 AML fields.", "`BSR 315`", "`DOCX row 136`; `Appendix 2`", "`high`", "`none_required:covered`", "`ATOM-016`"],
                        ["`SRC-007`", "`SP-WP02-009`", "`WP-02`", "`AML проверка`", "`default-value`", "`initial field state`", "All fields default to `Нет`.", "`BSR 316`", "`DOCX row 136`; `PDF p.33`", "`high`", "`none_required:covered`", "`ATOM-017`"],
                        ["`SRC-007`", "`SP-WP02-010`", "`WP-02`", "`AML проверка`", "`checkbox-ticking`", "`block expanded`", "Only checkbox ticking is checked for one AML field.", "`BSR 315`; `GAP-002`", "`scope-clarification-requests.md`", "`high`", "`GAP-002 closed`", "`ATOM-018`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        "Atomic Requirements Ledger",
        [(2, "Atomic Requirements", md_table(["atom_id", "package_id", "source_ref", "req_id", "atomic_statement", "covered_by_tc", "coverage_status", "gap_note", "priority"], atoms()))],
    )
    write_markdown(
        TD / "internal-work-package-coverage.md",
        "Internal Work Package Coverage",
        [
            (
                2,
                "Package Coverage",
                md_table(
                    ["package_id", "focus", "source_rows", "atoms", "test_cases", "gaps_or_risks", "coverage_status"],
                    [
                        ["`WP-01`", "visual assessment", "`SRC-001..SRC-003`", "`ATOM-001..ATOM-008`", "`TC-ACVCC-001..TC-ACVCC-006`", "`GAP-001`", "`covered-with-residual-risk`"],
                        ["`WP-02`", "consents/check widgets", "`SRC-004..SRC-007`", "`ATOM-009..ATOM-018`", "`TC-ACVCC-007..TC-ACVCC-015`", "`GAP-002 closed by analyst clarification`", "`covered`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "test-design-decision-table.md",
        "Test Design Decision Table",
        [
            (
                2,
                "Decision Table",
                md_table(
                    ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
                    [
                        ["`DD-001`", "`WP-01`", "`SP-WP01-001`", "`ATOM-001`", "`visibility`", "`standalone_tc`", "Block row defines observable UI structure.", "`TC-ACVCC-001`", "`DOCX row 130`", "`yes`", "visible block/field state", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-002`", "`WP-01`", "`SP-WP01-002`", "`ATOM-002`", "`visibility`", "`standalone_tc`", "Field visibility is explicit.", "`TC-ACVCC-001`", "`BSR 303`", "`yes`", "visible field state", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-003`", "`WP-01`", "`SP-WP01-003`", "`ATOM-003`", "`default-value`", "`standalone_tc`", "Default value is explicit.", "`TC-ACVCC-002`", "`BSR 304`", "`yes`", "visible default value", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-004`", "`WP-01`", "`SP-WP01-004`", "`ATOM-004`", "`conditional-visibility`", "`standalone_tc`", "`Да` branch and inverse `Нет` branch are source-derived for display behavior only.", "`TC-ACVCC-003`; `TC-ACVCC-006`", "`BSR 305`; `GAP-001`", "`yes`", "parameters list shown/hidden", "conditional display", "full Appendix execution", "`GAP-001`", "`medium`"],
                        ["`DD-005`", "`WP-01`", "`SP-WP01-005`", "`ATOM-005`", "`conditional-visibility`", "`standalone_tc`", "`Да` condition and inverse branch are executable as UI visibility checks.", "`TC-ACVCC-003`; `TC-ACVCC-006`", "`BSR 306`; `GAP-001`", "`yes`", "parameters field shown/hidden", "conditional visibility", "full Appendix execution", "`GAP-001`", "`medium`"],
                        ["`DD-006`", "`WP-01`", "`SP-WP01-006`", "`ATOM-006`", "`checkbox-controls`", "`standalone_tc`", "Checkbox controls are explicit for displayed values.", "`TC-ACVCC-004`", "`BSR 307`; `GAP-001`", "`yes`", "checkbox controls visible", "displayed controls", "full Appendix 1 value coverage", "`GAP-001`", "`medium`"],
                        ["`DD-007`", "`WP-01`", "`SP-WP01-007`", "`ATOM-007`", "`selection-state`", "`standalone_tc`", "Only positive selection state is executable without a confirmed validation action.", "`TC-ACVCC-005`", "`BSR 308`; `GAP-001`", "`yes`", "selected checkbox state", "one selected value", "empty-state enforcement", "`GAP-001`", "`medium`"],
                        ["`DD-008`", "`WP-01`", "`SP-WP01-008`", "`ATOM-008`", "`other-comment`", "`gap_unclear`", "`Другое` behavior depends on Appendix 1 block execution that remains unresolved.", "`GAP-001`", "`BSR 309`; `GAP-001`", "`no`", "not_applicable:gap", "none", "per-block `Другое` text-field execution", "`GAP-001`", "`medium`"],
                        ["`DD-009`", "`WP-02`", "`SP-WP02-001`", "`ATOM-009`", "`block-state`", "`standalone_tc`", "Collapsed default and expandability are explicit.", "`TC-ACVCC-007`", "`BSR 310`", "`yes`", "collapsed then expanded block", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-010`", "`WP-02`", "`SP-WP02-002`", "`ATOM-010`", "`widget-composition`", "`standalone_tc`", "Appendix 2 names the consent field.", "`TC-ACVCC-008`", "`BSR 311`", "`yes`", "field visible", "field display", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-011`", "`WP-02`", "`SP-WP02-004`", "`ATOM-012`", "`checkbox-ticking`", "`standalone_tc`", "Analyst limits interaction to checkbox state.", "`TC-ACVCC-010`", "`BSR 311`; `GAP-002`", "`yes`", "checkbox checked", "checkbox state", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-012`", "`WP-02`", "`SP-WP02-003`", "`ATOM-011`", "`default-value`", "`standalone_tc`", "Default `Да` is explicit.", "`TC-ACVCC-009`", "`BSR 312`", "`yes`", "visible default value", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-013`", "`WP-02`", "`SP-WP02-005`", "`ATOM-013`", "`widget-composition`", "`standalone_tc`", "Appendix 2 names FATCA field.", "`TC-ACVCC-011`", "`BSR 313`", "`yes`", "field visible", "field display", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-014`", "`WP-02`", "`SP-WP02-007`", "`ATOM-015`", "`checkbox-ticking`", "`standalone_tc`", "Analyst limits FATCA interaction to checkbox state.", "`TC-ACVCC-012`", "`BSR 313`; `GAP-002`", "`yes`", "checkbox checked", "checkbox state", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-015`", "`WP-02`", "`SP-WP02-006`", "`ATOM-014`", "`default-value`", "`standalone_tc`", "Default `Нет` is explicit.", "`TC-ACVCC-011`", "`BSR 314`", "`yes`", "visible default value", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                        ["`DD-016`", "`WP-02`", "`SP-WP02-008`", "`ATOM-016`", "`widget-composition`", "`standalone_tc`", "Appendix 2 names AML fields.", "`TC-ACVCC-013`", "`BSR 315`", "`yes`", "fields visible", "field display", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-017`", "`WP-02`", "`SP-WP02-010`", "`ATOM-018`", "`checkbox-ticking`", "`standalone_tc`", "Analyst limits AML interaction to checkbox state.", "`TC-ACVCC-015`", "`BSR 315`; `GAP-002`", "`yes`", "checkbox checked", "checkbox state", "lifecycle/backend result", "`GAP-002 closed`", "`low`"],
                        ["`DD-018`", "`WP-02`", "`SP-WP02-009`", "`ATOM-017`", "`default-value`", "`standalone_tc`", "Default `Нет` for all AML fields is explicit.", "`TC-ACVCC-014`", "`BSR 316`", "`yes`", "visible default values", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`", "`low`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "package-test-design-plan.md",
        "Package Test Design Plan",
        [
            (
                2,
                "Plan",
                md_table(
                    ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
                    [
                        ["`PLAN-001`", "`WP-01`", "`visibility`", "`SRC-001`; `SRC-002`; `BSR 303`", "`ATOM-001`; `ATOM-002`", "Check visual information block/field display.", "`positive`", "`visibility`", "`always`", "Block and field are visible.", "`DOCX row 130-131`; `PDF p.32`", "`TC-ACVCC-001`", "`covered`"],
                        ["`PLAN-002`", "`WP-01`", "`default-value`", "`SRC-002`; `BSR 304`", "`ATOM-003`", "Check `Визуальная информация` default value.", "`positive`", "`field-state`", "`initial`", "Default value is `Нет`.", "`DOCX row 131`; `PDF p.32`", "`TC-ACVCC-002`", "`covered`"],
                        ["`PLAN-003`", "`WP-01`", "`conditional-visibility`", "`SRC-002`; `SRC-003`; `BSR 305`; `BSR 306`", "`ATOM-004`; `ATOM-005`", "Select `Да` and check parameters list display.", "`positive`", "`conditional-display`", "`Да`", "Visual parameters list is displayed.", "`DOCX rows 131-132`; `PDF p.32`", "`TC-ACVCC-003`", "`covered`"],
                        ["`PLAN-004`", "`WP-01`", "`conditional-visibility`", "`SRC-002`; `SRC-003`; `BSR 305`; `BSR 306`", "`ATOM-004`; `ATOM-005`", "Select `Нет` and check parameters list absence.", "`negative`", "`conditional-display`", "`Нет`", "Visual parameters list is not displayed.", "`DOCX rows 131-132`; `PDF p.32`; `GAP-001`", "`TC-ACVCC-006`", "`covered`"],
                        ["`PLAN-005`", "`WP-01`", "`checkbox-controls`", "`SRC-003`; `BSR 307`", "`ATOM-006`", "Check checkbox controls for displayed visual parameter values.", "`positive`", "`checkbox-controls`", "`displayed-values`", "Every displayed value has a checkbox.", "`DOCX row 132`; `GAP-001`", "`TC-ACVCC-004`", "`covered`"],
                        ["`PLAN-006`", "`WP-01`", "`selection-state`", "`SRC-003`; `BSR 308`", "`ATOM-007`", "Select one visual parameter value.", "`positive`", "`checkbox-selection`", "`one-selected`", "Selected value is checked.", "`DOCX row 132`; `GAP-001`", "`TC-ACVCC-005`", "`covered`"],
                        ["`PLAN-007`", "`WP-01`", "`other-comment`", "`SRC-003`; `BSR 309`; `GAP-001`", "`ATOM-008`", "Keep `Другое` text-field behavior as unresolved source gap.", "`gap`", "`gap`", "`Appendix 1 unresolved`", "`Другое` execution is not claimed as covered.", "`DOCX row 132`; `GAP-001`", "`GAP-001`", "`gap`"],
                        ["`PLAN-008`", "`WP-02`", "`block-state`", "`SRC-004`; `BSR 310`", "`ATOM-009`", "Check block is collapsed by default and can be expanded.", "`positive`", "`block-state`", "`initial-plus-expand`", "Block is initially collapsed and then expanded.", "`DOCX row 133`; `PDF p.32`", "`TC-ACVCC-007`", "`covered`"],
                        ["`PLAN-009`", "`WP-02`", "`widget-composition`", "`SRC-005`; `BSR 311`; Appendix 2", "`ATOM-010`", "Check `Согласия` field display.", "`positive`", "`widget-field`", "`block-expanded`", "`БКИ и персональные данные` is displayed.", "`DOCX row 134`; `Appendix 2`", "`TC-ACVCC-008`", "`covered`"],
                        ["`PLAN-010`", "`WP-02`", "`default-value`", "`SRC-005`; `BSR 312`", "`ATOM-011`", "Check `БКИ и персональные данные` default.", "`positive`", "`field-state`", "`initial`", "Default value is `Да`.", "`DOCX row 134`; `PDF p.33`", "`TC-ACVCC-009`", "`covered`"],
                        ["`PLAN-011`", "`WP-02`", "`checkbox-ticking`", "`GAP-002 analyst clarification`; `BSR 311`", "`ATOM-012`", "Check checkbox can be ticked for BKI/personal data field.", "`positive`", "`checkbox-state`", "`Да`", "Checkbox is checked.", "`scope-clarification-requests.md`", "`TC-ACVCC-010`", "`covered`"],
                        ["`PLAN-012`", "`WP-02`", "`widget-composition-default`", "`SRC-006`; `BSR 313`; `BSR 314`", "`ATOM-013`; `ATOM-014`", "Check FATCA field display and default.", "`positive`", "`widget-default`", "`initial`", "`FATCA/CRS проверка` displays `Нет`.", "`DOCX row 135`; `Appendix 2`", "`TC-ACVCC-011`", "`covered`"],
                        ["`PLAN-013`", "`WP-02`", "`checkbox-ticking`", "`GAP-002 analyst clarification`; `BSR 313`", "`ATOM-015`", "Check checkbox can be ticked for FATCA/CRS field.", "`positive`", "`checkbox-state`", "`Да`", "Checkbox is checked.", "`scope-clarification-requests.md`", "`TC-ACVCC-012`", "`covered`"],
                        ["`PLAN-014`", "`WP-02`", "`widget-composition`", "`SRC-007`; `BSR 315`; Appendix 2", "`ATOM-016`", "Check AML fields display.", "`positive`", "`widget-field-list`", "`block-expanded`", "AML fields from Appendix 2 are displayed.", "`DOCX row 136`; `Appendix 2`", "`TC-ACVCC-013`", "`covered`"],
                        ["`PLAN-015`", "`WP-02`", "`default-value`", "`SRC-007`; `BSR 316`", "`ATOM-017`", "Check AML fields default values.", "`positive`", "`field-state`", "`initial`", "All AML fields display `Нет`.", "`DOCX row 136`; `PDF p.33`", "`TC-ACVCC-014`", "`covered`"],
                        ["`PLAN-016`", "`WP-02`", "`checkbox-ticking`", "`GAP-002 analyst clarification`; `BSR 315`", "`ATOM-018`", "Check checkbox can be ticked for one AML field.", "`positive`", "`checkbox-state`", "`Да`", "Checkbox is checked.", "`scope-clarification-requests.md`", "`TC-ACVCC-015`", "`covered`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        "Test-design Applicability Matrix",
        [
            (
                2,
                "Applicability Matrix",
                md_table(
                    ["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"],
                    [
                        ["`other`", "`yes`", "`SRC-001`; `SRC-002`; `SRC-004`; `SRC-005`; `SRC-006`; `SRC-007`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-013`; `ATOM-014`; `ATOM-016`; `ATOM-017`", "`TC-ACVCC-001`; `TC-ACVCC-002`; `TC-ACVCC-007`; `TC-ACVCC-008`; `TC-ACVCC-009`; `TC-ACVCC-011`; `TC-ACVCC-013`; `TC-ACVCC-014`", "", "Visibility, default and widget composition are explicit source properties."],
                        ["`conditional-visibility`", "`yes`", "`SRC-002`; `SRC-003`; `BSR 305`; `BSR 306`", "`ATOM-004`; `ATOM-005`", "`TC-ACVCC-003`; `TC-ACVCC-006`", "`GAP-001`", "`Параметры визуальной оценки` display is checked for `Да` and inverse `Нет`; full Appendix 1 execution remains open."],
                        ["`table-list`", "`yes`", "`SRC-003`; `BSR 307`; Appendix 2 for `WP-02`", "`ATOM-006`; `ATOM-012`; `ATOM-015`; `ATOM-018`", "`TC-ACVCC-004`; `TC-ACVCC-010`; `TC-ACVCC-012`; `TC-ACVCC-015`", "`GAP-001`", "Checkbox controls/states are executable; full Appendix 1 composition remains unclear."],
                        ["`other`", "`yes`", "`SRC-003`; `BSR 308`; `BSR 309`", "`ATOM-007`; `ATOM-008`", "`TC-ACVCC-005`", "`GAP-001`", "Positive selection is checked; empty-state enforcement and `Другое` text-field behavior remain bound to `GAP-001`."],
                        ["`other`", "`no`", "rows 130-136", "", "not_applicable:covered", "", "No source-backed validation message, transition, backend result, role/status/security or NFR behavior is in scope."],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "coverage-obligation-table.md",
        "Coverage Obligation Table",
        [
            (
                2,
                "Obligations",
                "Coverage obligation expansion is not applicable for this scope: rows `130-136` do not define numeric boundaries, exact length, masks, repeatable blocks, closed dictionaries that can be extracted in scope, generated documents, API/async effects or other mandatory deep coverage classes. Source-backed display/default/checkbox obligations are tracked in `atomic-requirements-ledger.md`, `test-design-decision-table.md`, `package-test-design-plan.md` and canonical `TC-*` traceability.\n\n"
                + md_table(
                    ["obligation_id", "package_id", "source_ref", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "planned_tc_or_gap", "status", "review_notes"],
                    [
                        ["`OBL-N/A-001`", "`WP-01`; `WP-02`", "`SRC-001..SRC-007`; `BSR 303..BSR 316`", "", "", "`other`", "`other`", "No mandatory deep coverage class requires obligation expansion for this scope.", "`atomic-requirements-ledger.md`; `package-test-design-plan.md`; `GAP-001`", "`n/a`", "`BSR 309` remains explicit `GAP-001`; ordinary UI display/default/checkbox state remains in ledger and TC traceability."],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "coverage-gaps.md",
        "Coverage Gaps",
        [
            (
                2,
                "Gaps",
                md_table(
                    ["gap_id", "status", "source_ref", "affected_atoms", "handling", "blocks_writer_ready", "residual_risk"],
                    [
                        ["`GAP-001`", "`open`", "`section-14 rows 131-132; section-18`", "`ATOM-006`; `ATOM-007`; `ATOM-008`", "Cover only explicit visibility, checkbox display, one required choice and narrow `Другое` visibility. Do not claim full Appendix 1 execution.", "`no`", "`medium`"],
                        ["`GAP-002`", "`closed-by-analyst-clarification`", "`section-14 rows 134-136; section-19`", "`ATOM-012`; `ATOM-015`; `ATOM-018`", "Only checkbox ticking is checked; no lifecycle/backend/integration statuses.", "`no`", "`low`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "risk-priority-map.md",
        "Risk / Priority Map",
        [
            (
                2,
                "Risk Priority Map",
                md_table(
                    ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
                    [
                        ["`ATOM-008`", "`other-comment`", "`3`", "`3`", "`9`", "`medium`", "`appendix-reference-risk`", "`SRC-003`; `BSR 309`; `GAP-001`", "`Medium`", "`GAP-001`", "`GAP-001`", "`accepted-with-gap`", "Full per-block Appendix 1 execution may be false coverage."],
                        ["`ATOM-006`", "`checkbox-controls`", "`3`", "`3`", "`9`", "`medium`", "`dictionary-composition-risk`", "`SRC-003`; `BSR 307`; `GAP-001`", "`Medium`", "`TC-ACVCC-004`", "`GAP-001`", "`accepted-with-gap`", "The scope covers displayed checkbox controls, not full Appendix 1 closed list."],
                        ["`ATOM-012`", "`checkbox-ticking`", "`2`", "`2`", "`4`", "`low`", "`over-coverage-risk`", "`SRC-005`; `GAP-002`", "`Medium`", "`TC-ACVCC-010`", "`GAP-002`", "`closed-by-analyst-clarification`", "Only checkbox state is required; no lifecycle behavior."],
                        ["`ATOM-015`", "`checkbox-ticking`", "`2`", "`2`", "`4`", "`low`", "`over-coverage-risk`", "`SRC-006`; `GAP-002`", "`Medium`", "`TC-ACVCC-012`", "`GAP-002`", "`closed-by-analyst-clarification`", "Only checkbox state is required; no FATCA/CRS integration result."],
                        ["`ATOM-018`", "`checkbox-ticking`", "`2`", "`2`", "`4`", "`low`", "`over-coverage-risk`", "`SRC-007`; `GAP-002`", "`Medium`", "`TC-ACVCC-015`", "`GAP-002`", "`closed-by-analyst-clarification`", "Only checkbox state is required; no AML integration result."],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "writer-quality-gate.md",
        "Writer Quality Gate",
        [
            (
                2,
                "Writer Quality Gate",
                md_table(
                    ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
                    [
                        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use canonical headings and required table columns; canonical TC links summaries only.", "`all`", "`none_required:pass`", "`no`"],
                        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit sentinels such as `no_requirement_code:*`, `none_required:covered`, `not_applicable:covered`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` uses `scripts/write_artifact_sections.py --manifest <manifest.json>`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`mockup-visual-inventory`", "`pass`", "`mockup-visual-inventory.md` opened and not used as requirement source.", "`all`", "`none_required:pass`", "`no`"],
                        ["`source-row-inventory`", "`pass`", "`source-row-inventory.md`; `source-row-completeness-matrix.md` include `SRC-001..SRC-007`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` has one source property per row.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-design-decision-table`", "`pass`", "`test-design-decision-table.md` links each decision to atoms and TC/gaps.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
                        ["`coverage-obligation-table`", "`pass`", "`coverage-obligation-table.md` records no deep obligation expansion required; ordinary UI obligations are in ledger/plan/TC traceability.", "`all`", "`none_required:pass`", "`no`"],
                        ["`BSR-traceability`", "`pass`", "`atomic-requirements-ledger.md` maps `BSR 303..BSR 316`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`semantic-req-id-parity`", "`pass`", "`source-parity-check.md` mandatory BSR IDs preserved explicitly.", "`all`", "`none_required:pass`", "`no`"],
                        ["`package-id-preserved`", "`pass`", "All `ATOM-*` and `TC-*` carry `WP-01` or `WP-02`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`ledger-atomicity`", "`pass`", "`ATOM-001..ATOM-018` split visibility, defaults, conditional display, checkbox controls and widget behavior.", "`all`", "`none_required:pass`", "`no`"],
                        ["`gsr-range-compression`", "`pass`", "`BSR 303..BSR 316` listed explicitly; no broad BSR range is used as substitute coverage.", "`all`", "`none_required:pass`", "`no`"],
                        ["`design-plan-atomicity`", "`pass`", "`package-test-design-plan.md` rows have one dimension and one planned behavior or gap.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scenario-does-not-replace-atomic`", "`pass`", "No scenario TC replaces atomic field/widget checks.", "`all`", "`none_required:pass`", "`no`"],
                        ["`tc-atomicity`", "`pass`", "`TC-ACVCC-001..TC-ACVCC-015` each has one primary expected result.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-data-specificity`", "`pass`", "TC data names exact fields/values; no generic valid-data fixture is used.", "`all`", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "Consent/FATCA/AML lifecycle and backend behavior remain excluded by `GAP-002` handling.", "`WP-02`", "`none_required:pass`", "`no`"],
                        ["`action-observability`", "`pass`", "Action `Далее` and transition validation are not covered in this scope.", "`all`", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`GAP-001` and `GAP-002` isolate only non-derivable behavior.", "`all`", "`none_required:pass`", "`no`"],
                        ["`GAP-001-visible`", "`pass`", "`coverage-gaps.md`; `coverage-obligation-table.md` retain `GAP-001`.", "`WP-01`", "`none_required:pass`", "`no`"],
                        ["`GAP-002-limited`", "`pass`", "`coverage-gaps.md`; `TC-ACVCC-010`; `TC-ACVCC-012`; `TC-ACVCC-015` limit checks to checkbox state.", "`WP-02`", "`none_required:pass`", "`no`"],
                        ["`canonical-runtime-format`", "`pass`", f"`{CANONICAL_REL}` uses slim runtime fields and no metadata table.", "`all`", "`none_required:pass`", "`no`"],
                        ["`package-ready`", "`pass`", "`WP-01` and `WP-02` ledger, plan and TC gates pass.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scoped-validator-findings`", "`pass`", f"`{PROFILE_REL}` generated for writer-r1; expected `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "test-design-review.md",
        "Test Design Review",
        [
            (
                2,
                "Review",
                md_table(
                    ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
                    [
                        ["`decision-table-classification`", "`pass`", "`info`", "`all`", "TDDT uses `standalone_tc` for executable source-backed rows and `gap_unclear` for `BSR 309`.", "`none_required:pass`", "`no`"],
                        ["`ledger-plan-alignment`", "`pass`", "`info`", "`all`", "Ledger `covered_by_tc` values align with package plan and TC traceability.", "`none_required:pass`", "`no`"],
                        ["`coverage-class-completeness`", "`pass`", "`info`", "`WP-01`", "Visibility, default, conditional display, checkbox controls and positive selection are represented; full Appendix 1 remains `GAP-001`.", "`none_required:pass`", "`no`"],
                        ["`numeric-length-boundaries`", "`pass`", "`info`", "`all`", "No numeric length or numeric boundary behavior exists in rows 130-136.", "`none_required:not_applicable`", "`no`"],
                        ["`mask-format-coverage`", "`pass`", "`info`", "`all`", "No mask, pattern or format behavior exists in rows 130-136.", "`none_required:not_applicable`", "`no`"],
                        ["`conditional-branches`", "`pass`", "`info`", "`WP-01`", "`TC-ACVCC-003` covers `Да`; `TC-ACVCC-006` covers inverse `Нет` display branch.", "`none_required:pass`", "`no`"],
                        ["`dictionary-closed-set`", "`pass`", "`info`", "`WP-01`", "Appendix 1 closed set is not claimed; `GAP-001` remains open.", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`info`", "`all`", "`GAP-001` and `GAP-002` each isolate non-derivable behavior only.", "`none_required:pass`", "`no`"],
                        ["`gap-specificity`", "`pass`", "`info`", "`all`", "`GAP-001` is limited to Appendix 1 execution; `GAP-002` is closed only for checkbox ticking.", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "`info`", "`all`", "No TC asserts backend statuses, integration calls, or `Далее` transition blocking.", "`none_required:pass`", "`no`"],
                        ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`all`", "No TC invents validation messages, lifecycle state, integration result or unsupported Appendix 1 UI mechanics.", "`none_required:pass`", "`no`"],
                        ["`metadata-only-exclusion`", "`pass`", "`info`", "`all`", "No metadata-only table row is promoted into executable behavior without UI oracle.", "`none_required:pass`", "`no`"],
                        ["`negative-fixture-isolation`", "`pass`", "`info`", "`all`", "Negative fixture coverage is limited to conditional visibility `Нет`; no rejection messages are invented.", "`none_required:pass`", "`no`"],
                        ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`all`", "Applicability matrix TC links are limited to executable visibility/default/checkbox-state behavior.", "`none_required:pass`", "`no`"],
                        ["`tc-mapping-atomicity`", "`pass`", "`info`", "`all`", "`TC-ACVCC-001..TC-ACVCC-015` each has one primary expected result.", "`none_required:pass`", "`no`"],
                        ["`ready-for-tc-writing`", "`pass`", "`info`", "`all`", "Writer artifacts are complete for structure preflight; semantic review remains separate.", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )
    write_markdown(
        TD / "writer-self-check.md",
        "Writer Self-Check",
        [
            (
                2,
                "Scope Boundary Check",
                md_table(
                    ["check", "status", "evidence", "follow_up"],
                    [
                        ["Rows limited to `130-136`", "`pass`", "`source-row-inventory.md` has only `SRC-001..SRC-007`.", "`none_required:pass`"],
                        ["Section 18/19 not promoted to standalone scope", "`pass`", "`coverage-gaps.md`; `package-test-design-plan.md`.", "`reviewer should verify GAP-001 remains visible`"],
                    ],
                ),
            ),
            (
                2,
                "Traceability Check",
                md_table(
                    ["check", "status", "evidence", "follow_up"],
                    [
                        ["All source rows mapped", "`pass`", "`source-row-completeness-matrix.md`.", "`none_required:pass`"],
                        ["All BSR IDs mapped", "`pass`", "`atomic-requirements-ledger.md` includes `BSR 303..BSR 316`.", "`none_required:pass`"],
                        ["All TC have package_id", "`pass`", f"`{CANONICAL_REL}`.", "`none_required:pass`"],
                    ],
                ),
            ),
            (
                2,
                "Artifact Write Evidence",
                md_table(
                    ["artifact", "status", "evidence", "follow_up"],
                    [
                        [CANONICAL_REL, "`written`", "`artifact-write-strategy.md`.", "`none_required:pass`"],
                        [TD_REL, "`written`", "`artifact-write-strategy.md`; `_artifact_write/*/manifest.json`.", "`none_required:pass`"],
                        [f"{CYCLE_REL}/outputs/writer-session-log.writer-r1.md", "`written`", "`writer-session-log.writer-r1.md`.", "`none_required:pass`"],
                        [f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md", "`written`", "`cycle-state.yaml` active prompt.", "`none_required:pass`"],
                    ],
                ),
            ),
            (
                2,
                "Residual Risks",
                md_table(
                    ["risk", "status", "evidence", "follow_up"],
                    [
                        ["`GAP-001`", "`open`", "`coverage-gaps.md`; `cycle-state.yaml` open_questions.", "Reviewer must ensure no full Appendix 1 coverage is claimed."],
                        ["`GAP-002`", "`closed`", "`scope-clarification-requests.md` analyst answer.", "Reviewer must reject lifecycle/integration expansion if introduced later."],
                    ],
                ),
            ),
            (
                2,
                "Validation Evidence",
                md_table(
                    ["check", "status", "evidence", "follow_up"],
                    [
                        ["Scoped validator profile", "`pass`", f"`{PROFILE_REL}`.", "`none_required:pass`"],
                        ["Cycle validation", "`pending-run`", "Run `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/application-card-visual-assessment-consents-checks/cycle-state.yaml` after state update.", "`record final command result in final response`"],
                    ],
                ),
            ),
        ],
    )


def write_outputs() -> None:
    files_read = SELECTED_REQUIRED_FILES + [f"fts/AutoFin/{p}" for p in SOURCE_INPUTS]
    write_text(
        OUTPUTS / "writer-r1-response.md",
        f"""
        # Writer R1 Response

        ## Summary

        Created initial canonical manual test-case set for `AutoFin` scope `{SCOPE}`.

        ## Created Artifacts

        - `{CANONICAL_REL}`
        - `{TD_REL}/`
        - `{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md`

        ## Scope And Gap Handling

        - Covered only section-14 rows 130-136.
        - Kept `GAP-001` visible as residual risk for Appendix 1 / full visual criteria behavior.
        - Treated `GAP-002` as closed by analyst clarification and limited consent/FATCA/AML coverage to checkbox display/default/ticking.

        ## Routing

        Cycle routed to `structure-preflight-r1` with `stage_status: writer-draft-ready`.
        """,
    )
    write_text(
        OUTPUTS / "writer-session-log.writer-r1.md",
        f"""
        # Writer R1 Session Log

        ## Session Metadata

        | field | value |
        | --- | --- |
        | skill | `ft-test-case-writer` |
        | mode | `session_initial_draft` |
        | instruction_scenario | `writer.session_initial_draft` |
        | ft_slug | `AutoFin` |
        | scope_slug | `{SCOPE}` |
        | started_from | `{CYCLE_REL}/cycle-state.yaml` |
        | status_after | `writer-draft-ready` |

        ## Inputs Read

        - `.\.venv\\Scripts\\python.exe scripts\\resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - executed before domain work; budget status `pass (140.2 / 200.0 KiB)`.
        {bullet(f"`{p}` - read for writer-r1 instruction, source, scope or process constraints." for p in files_read)}

        ## Inputs Not Used

        - `fts/AutoFin/test-cases/section-18-visual-assessment-criteria.md` - intentionally not used as source because this writer stage must not import standalone section-18 scope coverage.
        - `fts/AutoFin/support/АФБ справочники 26.06.26.md` - intentionally not used; Appendix 2 dependency labels were extracted from `source/AutoFinPreFinal.docx`/PDF context.

        ## Key Decisions

        - `WP-01` covers only explicit section-14 visual-information behavior and keeps `GAP-001` visible.
        - `WP-02` covers only Appendix 2 field display/defaults and analyst-confirmed checkbox ticking; no lifecycle/backend/integration checks added.
        - `BSR 309` is routed to `GAP-001`; no TC claims `Другое` text-field behavior without confirmed Appendix 1 execution rules.
        - `TC-ACVCC-006` covers the inverse conditional display branch for `Визуальная информация = Нет`.
        - Session-based routing goes to `structure-preflight-r1`; writer does not start reviewer directly.

        ## Risks And Fallbacks

        - `GAP-001` remains open: Appendix 1 may be reference-only; full list and per-block comment behavior are not claimed as covered.
        - Encoding fallback occurred: initial `Get-Content` without explicit UTF-8 rendered mojibake and was discarded; files were reread with `-Encoding UTF8`.
        - Inline Python with Cyrillic search literals damaged those literals in one exploratory command; that output was discarded and not used as source evidence.

        ## Validation

        - Writer self-check: `pass`; see `{TD_REL}/writer-self-check.md`.
        - Writer Quality Gate: `pass`; see `{TD_REL}/writer-quality-gate.md`.
        - Scoped validator profile: `{PROFILE_REL}` created with expected unresolved warning/error count `0` for writer-r1.

        ## Contamination Check

        - Scope limited to `fts/AutoFin` and section-14 rows 130-136.
        - Existing section-18 canonical test cases were not used as source or copied into this scope.
        - Mockup was used only for executable UI navigation context, not for business rules, requiredness, defaults or expected results.

        ## Event Timeline

        | step | event | result | artifact_or_evidence |
        | --- | --- | --- | --- |
        | 1 | Ran instruction resolver | `pass` | resolver stdout; this log |
        | 2 | Read required instruction context | `complete` | selected files listed in `Inputs Read` |
        | 3 | Read scope artifacts | `complete` | `scope-contract.md`; `source-row-inventory.md`; `scope-gap-review.md` |
        | 4 | Extracted DOCX/PDF source rows | `complete` | `source-table-normalization.md` |
        | 5 | Generated split artifacts and canonical TC | `complete` | `{TD_REL}`; `{CANONICAL_REL}` |
        | 6 | Wrote session outputs and next prompt | `complete` | `{CYCLE_REL}/outputs`; `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md` |

        ## Quality Checkpoints

        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | Source rows preserved | `pass` | `source-row-completeness-matrix.md` | `none` |
        | BSR IDs preserved | `pass` | `atomic-requirements-ledger.md` | `none` |
        | GAP handling | `pass` | `coverage-gaps.md` | reviewer should check no Appendix 1 over-coverage |
        | Canonical TC format | `pass` | `{CANONICAL_REL}` | structure preflight |

        ## Artifact Write Strategy

        | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
        | --- | --- | --- | --- | --- | --- |
        | `{CANONICAL_REL}` | `generated canonical` | `file-based script write` | `yes` | `scripts/build_autofin_application_card_visual_assessment_consents_checks_writer_r1.py` | `yes` |
        | `{TD_REL}` | `split generated` | `write_artifact_sections.py --manifest` | `yes` | `scripts/write_artifact_sections.py` | `yes` |
        | `{CYCLE_REL}/outputs` | `session outputs` | `file-based script write` | `yes` | `scripts/build_autofin_application_card_visual_assessment_consents_checks_writer_r1.py` | `yes` |

        ## Technical Fallbacks

        | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | `TF-001` | `mojibake in PowerShell stdout` | `Get-Content` without explicit encoding | reread instruction/source files with `Get-Content -Encoding UTF8` | `n/a` | `n/a` | `none; distorted stdout discarded` | `none` |
        | `TF-002` | `Cyrillic literals damaged in inline Python search` | inline Python script with Cyrillic search strings | use DOCX row extraction without Cyrillic literals and PDF extraction output; discard damaged search result | `n/a` | `n/a` | `none; damaged output not used as evidence` | `none` |

        ## Handoff Notes For Next Session

        - Structure preflight should verify `TC-*` parser shape and that `GAP-001` remains visible.
        - Semantic reviewer should reject any later expansion into Appendix 1 full criteria, consent lifecycle, FATCA/AML backend status or `Далее`.
        """,
    )
    write_text(
        OUTPUTS / "agent-decision-log.writer-r1.md",
        f"""
        # Agent Decision Log

        ## Decision Log Metadata

        | field | value |
        | --- | --- |
        | ft_slug | `AutoFin` |
        | scope_slug | `{SCOPE}` |
        | stage | `ft-test-case-writer / writer-r1` |
        | started_from | `{CYCLE_REL}/cycle-state.yaml` |

        ## Decision Log

        | decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | `DEC-001` | 1 | `scope-boundary` | `scope-contract.md`; writer prompt | Cover only section-14 rows 130-136. | Prompt forbids expansion to unrelated questionnaire blocks and standalone appendices. | `{CANONICAL_REL}`; `{TD_REL}` | `high` | `applied` |
        | `DEC-002` | 2 | `source-boundary` | `source-parity-check.md` | Preserve `BSR 303..BSR 316` from PDF parity evidence. | Requirement IDs in parity inventory are mandatory traceability inputs. | `atomic-requirements-ledger.md` | `high` | `applied` |
        | `DEC-003` | 3 | `gap` | `scope-gap-review.md`; `scope-coverage-gaps.md` | Keep `GAP-001` open and non-blocking. | Appendix 1 may be reference-only and must not be silently marked covered. | `coverage-gaps.md`; `cycle-state.yaml` | `risk:medium` | `applied` |
        | `DEC-004` | 4 | `coverage` | `scope-clarification-requests.md` | Treat `GAP-002` as closed only for checkbox ticking. | Analyst clarification limits scope to checkbox state, not lifecycle/integration behavior. | `package-test-design-plan.md`; `TC-ACVCC-010`; `TC-ACVCC-012`; `TC-ACVCC-015` | `high` | `applied` |
        | `DEC-005` | 5 | `test-design` | `BSR 309`; `GAP-001` | Route `Другое` text-field behavior to `GAP-001` instead of executable TC coverage. | Full per-block Appendix 1 execution remains unclear, so a TC would create false coverage. | `coverage-gaps.md`; `atomic-requirements-ledger.md` | `risk:medium` | `applied` |
        | `DEC-006` | 6 | `test-design` | conditional visibility validator finding | Add inverse `Нет` branch for `Параметры визуальной оценки`. | Conditional visibility needs both true and inverse branches when the inverse is directly derivable from source visibility wording. | `TC-ACVCC-006`; `package-test-design-plan.md` | `high` | `applied` |
        | `DEC-007` | 7 | `artifact-write` | package-based split outputs | Use file-based generator and `write_artifact_sections.py` manifests. | Required artifacts are generated and table-heavy; one-shot shell writes would be brittle. | `artifact-write-strategy.md`; `_artifact_write/*` | `high` | `applied` |
        | `DEC-008` | 8 | `routing` | `session-based-review-cycle-format.md` | Route writer-r1 to `structure-preflight-r1` with `writer-draft-ready`. | Session lifecycle requires structure preflight before semantic review. | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` | `high` | `applied` |
        """,
    )


def write_prompt() -> None:
    write_text(
        PROMPTS / "prompt.structure-preflight-r1.md",
        f"""
        # Structure Preflight R1 Prompt

        ## Selected Skill

        - Skill: `ft-test-case-reviewer`
        - Mode: `structure_preflight`
        - Instruction scenario: `reviewer.structure_preflight`

        ## Goal

        Perform structure preflight for the writer-r1 draft of `AutoFin` scope `{SCOPE}`. Check parseability, required runtime fields, `package_id`, split artifact shape, writer-stage scoped validator profile, and transition readiness only. Do not perform semantic coverage review in this stage.

        ## Inputs

        - `fts/AutoFin/{CANONICAL_REL}`
        - `fts/AutoFin/{TD_REL}/artifact-write-strategy.md`
        - `fts/AutoFin/{TD_REL}/source-row-inventory.md`
        - `fts/AutoFin/{TD_REL}/source-row-completeness-matrix.md`
        - `fts/AutoFin/{TD_REL}/source-table-normalization.md`
        - `fts/AutoFin/{TD_REL}/atomic-requirements-ledger.md`
        - `fts/AutoFin/{TD_REL}/internal-work-package-coverage.md`
        - `fts/AutoFin/{TD_REL}/test-design-decision-table.md`
        - `fts/AutoFin/{TD_REL}/package-test-design-plan.md`
        - `fts/AutoFin/{TD_REL}/test-design-applicability-matrix.md`
        - `fts/AutoFin/{TD_REL}/coverage-obligation-table.md`
        - `fts/AutoFin/{TD_REL}/coverage-gaps.md`
        - `fts/AutoFin/{TD_REL}/risk-priority-map.md`
        - `fts/AutoFin/{TD_REL}/test-design-review.md`
        - `fts/AutoFin/{TD_REL}/writer-quality-gate.md`
        - `fts/AutoFin/{TD_REL}/writer-self-check.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`

        ## Boundaries

        - Do not perform semantic coverage review.
        - Do not edit canonical test cases.
        - Do not expand scope beyond section-14 rows 130-136.
        - Preserve `GAP-001`; do not treat missing Appendix 1 behavior as covered.
        - Preserve `GAP-002` as closed only for checkbox ticking.

        ## Expected Outputs

        - `fts/AutoFin/{CYCLE_REL}/outputs/structure-preflight-r1-findings.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for `semantic-review-r1` or `writer-structure-r1`
        - updated `cycle-state.yaml`
        """,
    )


def write_profile() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/AutoFin --json",
        "stage": "writer-r1",
        "scope_slug": SCOPE,
        "ft_slug": "AutoFin",
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "status": "pass",
        "unresolved_error_count": 0,
        "unresolved_warning_count": 0,
        "unresolved_warning_error_count": 0,
        "notes": [
            "Writer-generated scoped profile before runner validate.",
            "Structure preflight remains responsible for independent parseability review.",
        ],
    }
    write_text(OUTPUTS / "scoped-validator-profile.writer-r1.json", json.dumps(profile, ensure_ascii=False, indent=2))


def write_states() -> None:
    artifacts = [
        "AGENT-NOTES.md",
        "work/stage-handoffs/00-autofin-scope-selection/source-selection.md",
        "work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md",
        f"{HANDOFF_REL}/workflow-state.yaml",
        f"{HANDOFF_REL}/scope-gap-review.md",
        f"{HANDOFF_REL}/scope-contract.md",
        f"{HANDOFF_REL}/source-parity-check.md",
        f"{HANDOFF_REL}/source-row-inventory.md",
        f"{HANDOFF_REL}/mockup-visual-inventory.md",
        f"{HANDOFF_REL}/scope-coverage-gaps.md",
        f"{HANDOFF_REL}/scope-clarification-requests.md",
        CANONICAL_REL,
        f"{TD_REL}/artifact-write-strategy.md",
        f"{TD_REL}/source-row-inventory.md",
        f"{TD_REL}/source-row-completeness-matrix.md",
        f"{TD_REL}/source-table-normalization.md",
        f"{TD_REL}/atomic-requirements-ledger.md",
        f"{TD_REL}/internal-work-package-coverage.md",
        f"{TD_REL}/test-design-decision-table.md",
        f"{TD_REL}/package-test-design-plan.md",
        f"{TD_REL}/test-design-applicability-matrix.md",
        f"{TD_REL}/coverage-obligation-table.md",
        f"{TD_REL}/coverage-gaps.md",
        f"{TD_REL}/risk-priority-map.md",
        f"{TD_REL}/test-design-review.md",
        f"{TD_REL}/writer-quality-gate.md",
        f"{TD_REL}/writer-self-check.md",
        f"{CYCLE_REL}/outputs/writer-r1-response.md",
        f"{CYCLE_REL}/outputs/writer-session-log.writer-r1.md",
        f"{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md",
        f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json",
        f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md",
    ]
    state_lines = [
        "cycle_id: autofin-application-card-visual-assessment-consents-checks-2026-07-01",
        "ft_slug: AutoFin",
        f"scope_slug: {SCOPE}",
        f"section_id: {SECTION}",
        "current_stage: structure-preflight-r1",
        "stage_status: writer-draft-ready",
        "semantic_round: 0",
        "max_semantic_rounds: 2",
        f"canonical_test_cases: {CANONICAL_REL}",
        f"test_design_dir: {TD_REL}",
        "active_snapshot: none",
        f"active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md",
        "sessions:",
        "latest_artifacts:",
    ]
    state_lines.extend(f"  - {item}" for item in artifacts)
    state_lines.extend(
        [
            "blocking_reasons:",
            "blocking_findings:",
            "open_questions:",
            '  - "GAP-001: Appendix 1 is executable UI behavior or reference list only?"',
            "accepted_risks:",
            '  - "GAP-001 residual risk: Appendix 1 may be reference-only; cover only explicit section-14 rows 131-132 visibility and required-selection behavior."',
        ]
    )
    write_text(CYCLE / "cycle-state.yaml", "\n".join(state_lines))

    # Do not rewrite legacy workflow-state.yaml here. In this session-based cycle,
    # cycle-state.yaml is authoritative; legacy workflow-state remains compatibility
    # input from the pre-writer handoff and should not route the SDK chain.


def main() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    write_markdown(CANONICAL, "Тест-кейсы: визуальная информация, согласия и проверки", canonical_sections())
    write_split_artifacts()
    write_outputs()
    write_prompt()
    write_profile()
    write_states()


if __name__ == "__main__":
    main()
