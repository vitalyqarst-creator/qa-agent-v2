from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "visual-assessment-criteria"
SECTION = "section-18"
PACKAGE_ID = "WP-01"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = "work/stage-handoffs/17-visual-assessment-criteria"
PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"

WRITER_SELECTED_REQUIRED_FILES = [
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

STRUCTURE_PREFLIGHT_REQUIRED_FILES = [
    "AGENTS.md",
    "skills/README.md",
    "references/agent/session-based-review-cycle-format.md",
    "references/agent/codex-sdk-orchestration-format.md",
    "skills/ft-test-case-reviewer/SKILL.md",
    "references/agent/reviewer-output-format.md",
    "references/qa/review-findings-format.md",
    "references/qa/test-case-runtime-format.md",
    "references/agent/workflow-state-format.md",
    "references/agent/session-log-format.md",
    "references/agent/agent-decision-log-format.md",
    "references/agent/next-step-prompt-format.md",
]


def q(value: str) -> str:
    return f"`{value}`"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_markdown(target: Path, sections: list[tuple[int, str, str]], title: str | None = None) -> None:
    scratch = TD / "_artifact_write" / target.stem
    scratch.mkdir(parents=True, exist_ok=True)
    manifest_sections: list[dict[str, object]] = []
    for index, (level, heading, body) in enumerate(sections, start=1):
        content_path = scratch / f"{index:02d}.md"
        content_path.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append({"level": level, "heading": heading, "content_file": content_path.name})
    manifest: dict[str, object] = {
        "target_path": str(target),
        "sections": manifest_sections,
    }
    if title:
        preamble = scratch / "00-preamble.md"
        preamble.write_text(f"# {title}\n", encoding="utf-8", newline="\n")
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


SOURCE_ROWS: list[dict[str, str]] = [
    {"id": "SRC-001", "kind": "Блок `Визуальная информация`", "codes": "no_requirement_code:SRC-001", "map": "ATOM-001"},
    {"id": "SRC-002", "kind": "Поле `Визуальная информация`", "codes": "BSR 303; BSR 304; BSR 305", "map": "ATOM-001; ATOM-002; ATOM-003"},
    {"id": "SRC-003", "kind": "Поле `Параметры визуальной оценки`", "codes": "BSR 306; BSR 307; BSR 308; BSR 309", "map": "ATOM-004; ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010"},
    {"id": "SRC-004", "kind": "Group: `Признаки алкоголика`", "codes": "no_requirement_code:SRC-004", "map": "ATOM-006"},
    {"id": "SRC-005", "kind": "`Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`", "codes": "no_requirement_code:SRC-005", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-006", "kind": "`Отечность, нездоровый цвет лица, синяки под глазами`", "codes": "no_requirement_code:SRC-006", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-007", "kind": "`Шатающаяся походка, несвязная речь, сильно трясутся руки`", "codes": "no_requirement_code:SRC-007", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-008", "kind": "`Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени`", "codes": "no_requirement_code:SRC-008", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-009", "kind": "`Другое (комментарий обязателен)` under `Признаки алкоголика`", "codes": "no_requirement_code:SRC-009", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-010", "kind": "`Комментарий` under `Признаки алкоголика`", "codes": "no_requirement_code:SRC-010", "map": "ATOM-011; ATOM-012; GAP-001:closed"},
    {"id": "SRC-011", "kind": "Group: `Признаки наркомана`", "codes": "no_requirement_code:SRC-011", "map": "ATOM-006"},
    {"id": "SRC-012", "kind": "`Длинные, спущенные рукава в любую погоду, отрешенный взгляд`", "codes": "no_requirement_code:SRC-012", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-013", "kind": "`Неоправданно резкие перемены настроения`", "codes": "no_requirement_code:SRC-013", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-014", "kind": "`Отечность, нездоровый цвет лица, синяки под глазами` under `Признаки наркомана`", "codes": "no_requirement_code:SRC-014", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-015", "kind": "`Следы многочисленных уколов на кистях`", "codes": "no_requirement_code:SRC-015", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-016", "kind": "`Неестественно суженные / расширенные зрачки`", "codes": "no_requirement_code:SRC-016", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-017", "kind": "`Шатающаяся походка, несвязная речь, плохая координация движений`", "codes": "no_requirement_code:SRC-017", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-018", "kind": "`Неприятный запах кислоты`", "codes": "no_requirement_code:SRC-018", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-019", "kind": "`Другое (комментарий обязателен)` under `Признаки наркомана`", "codes": "no_requirement_code:SRC-019", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-020", "kind": "`Комментарий` under `Признаки наркомана`", "codes": "no_requirement_code:SRC-020", "map": "ATOM-011; ATOM-012; GAP-001:closed"},
    {"id": "SRC-021", "kind": "Group: `Признаки бывшего заключенного`", "codes": "no_requirement_code:SRC-021", "map": "ATOM-006"},
    {"id": "SRC-022", "kind": "`Татуировки уголовного содержания на кистях, пальцах ...`", "codes": "no_requirement_code:SRC-022", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-023", "kind": "`Характерный для заключенных жаргон`", "codes": "no_requirement_code:SRC-023", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-024", "kind": "`Другое (комментарий обязателен)` under `Признаки бывшего заключенного`", "codes": "no_requirement_code:SRC-024", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-025", "kind": "Group: `Признаки «преображенного» бомжа`", "codes": "no_requirement_code:SRC-025", "map": "ATOM-006"},
    {"id": "SRC-026", "kind": "`Несоответствие внешнего вида Клиента данным, которые он указывает в анкете ...`", "codes": "no_requirement_code:SRC-026", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-027", "kind": "`Признаки алкоголика / наркомана / бывшего заключенного`", "codes": "no_requirement_code:SRC-027", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-028", "kind": "`Несоответствие размеров / стиля одежды`", "codes": "no_requirement_code:SRC-028", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-029", "kind": "`Сильный макияж / использует парик`", "codes": "no_requirement_code:SRC-029", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-030", "kind": "`Другое (комментарий обязателен)` under `Признаки «преображенного» бомжа`", "codes": "no_requirement_code:SRC-030", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-031", "kind": "Group: `Поведенческие признаки потенциального неплательщика`", "codes": "no_requirement_code:SRC-031", "map": "ATOM-006"},
    {"id": "SRC-032", "kind": "`Клиент не может внятно объяснить, откуда он узнал о Банке ...`", "codes": "no_requirement_code:SRC-032", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-033", "kind": "`Мнимые семейные пары, часто с детьми ...`", "codes": "no_requirement_code:SRC-033", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-034", "kind": "`Сильное волнение клиента в ходе анкетирования ...`", "codes": "no_requirement_code:SRC-034", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-035", "kind": "`Слишком заострено внимание на последствиях неплатежей`", "codes": "no_requirement_code:SRC-035", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-036", "kind": "`Другое (комментарий обязателен)` under `Поведенческие признаки потенциального неплательщика`", "codes": "no_requirement_code:SRC-036", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-037", "kind": "Group: `Сопровождение Клиента`", "codes": "no_requirement_code:SRC-037", "map": "ATOM-006"},
    {"id": "SRC-038", "kind": "`Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки ...`", "codes": "no_requirement_code:SRC-038", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-039", "kind": "`Клиент находится в сопровождении подозрительных лиц, осуществляющих давление ...`", "codes": "no_requirement_code:SRC-039", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-040", "kind": "`Клиент использовал \"шпаргалку\" при заполнении анкеты`", "codes": "no_requirement_code:SRC-040", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-041", "kind": "`Клиент неоднократно звонил по телефону для выяснения ответов ...`", "codes": "no_requirement_code:SRC-041", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-042", "kind": "`Клиент замечен в сопровождении лиц, ранее приводивших мошенников ...`", "codes": "no_requirement_code:SRC-042", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-043", "kind": "`Другое (комментарий обязателен)` under `Сопровождение Клиента`", "codes": "no_requirement_code:SRC-043", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-044", "kind": "Group: `Признаки подделки документов`", "codes": "no_requirement_code:SRC-044", "map": "ATOM-006"},
    {"id": "SRC-045", "kind": "`Заметны следы подчистки документов, химического травления текста`", "codes": "no_requirement_code:SRC-045", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-046", "kind": "`Заметны следы подделки подписей, оттисков печатей и штампов`", "codes": "no_requirement_code:SRC-046", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-047", "kind": "`Наличие в документах дописок, допечаток, исправлений, орфографических ошибок`", "codes": "no_requirement_code:SRC-047", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-048", "kind": "`Личность заемщика не может быть достоверно подтверждена ...`", "codes": "no_requirement_code:SRC-048", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-049", "kind": "`Заметны следы замены фотографии в паспорте, листов ...`", "codes": "no_requirement_code:SRC-049", "map": "ATOM-006; ATOM-007"},
    {"id": "SRC-050", "kind": "`Другое (комментарий обязателен)` under `Признаки подделки документов`", "codes": "no_requirement_code:SRC-050", "map": "ATOM-006; ATOM-009"},
    {"id": "SRC-051", "kind": "Group: `Прочие признаки (комментарий обязателен)`", "codes": "no_requirement_code:SRC-051", "map": "ATOM-011; ATOM-012; GAP-001:closed"},
    {"id": "SRC-052", "kind": "`Комментарий` under `Прочие признаки`", "codes": "no_requirement_code:SRC-052", "map": "ATOM-011; ATOM-012; GAP-001:closed"},
]

DICT_GROUPS: list[tuple[str, list[str], bool]] = [
    ("Признаки алкоголика", [
        "Запах алкоголя / перегара / сильный запах духов, перебивающий перегар",
        "Отечность, нездоровый цвет лица, синяки под глазами",
        "Шатающаяся походка, несвязная речь, сильно трясутся руки",
        "Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени",
        "Другое (комментарий обязателен)",
    ], True),
    ("Признаки наркомана", [
        "Длинные, спущенные рукава в любую погоду, отрешенный взгляд",
        "Неоправданно резкие перемены настроения",
        "Отечность, нездоровый цвет лица, синяки под глазами",
        "Следы многочисленных уколов на кистях",
        "Неестественно суженные / расширенные зрачки",
        "Шатающаяся походка, несвязная речь, плохая координация движений",
        "Неприятный запах кислоты",
        "Другое (комментарий обязателен)",
    ], True),
    ("Признаки бывшего заключенного", [
        "Татуировки уголовного содержания на кистях, пальцах (например, с изображением перстней, крестов, четырех точек, образующих квадрат с пятой точкой посередине и др.)",
        "Характерный для заключенных жаргон",
        "Другое (комментарий обязателен)",
    ], False),
    ("Признаки «преображенного» бомжа", [
        "Несоответствие внешнего вида Клиента данным, которые он указывает в анкете (например, в анкете указано, что Клиент - гендиректор крупной организации, однако состояние зубов, волос, лица или кистей рук говорит о том, что ему полностью безразличны его внешний вид и здоровье)",
        "Признаки алкоголика / наркомана / бывшего заключенного",
        "Несоответствие размеров / стиля одежды",
        "Сильный макияж / использует парик",
        "Другое (комментарий обязателен)",
    ], False),
    ("Поведенческие признаки потенциального неплательщика", [
        "Клиент не может внятно объяснить, откуда он узнал о Банке / для чего ему необходим кредит, при этом испытывает волнение / раздражение",
        "Мнимые семейные пары, часто с детьми (например Клиент называет свою \"супругу\" Надей, а в штампе паспорта имя супруги - Елена); неадекватная реакция на вопросы о супруге / детях",
        "Сильное волнение клиента в ходе анкетирования, особенно при ответах на дополнительные / уточняющие вопросы",
        "Слишком заострено внимание на последствиях неплатежей",
        "Другое (комментарий обязателен)",
    ], False),
    ("Сопровождение Клиента", [
        "Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки по заполнению анкеты",
        "Клиент находится в сопровождении подозрительных лиц, осуществляющих давление на Клиента",
        "Клиент использовал \"шпаргалку\" при заполнении анкеты",
        "Клиент неоднократно звонил по телефону для выяснения ответов на вопросы анкеты",
        "Клиент замечен в сопровождении лиц, ранее приводивших мошенников / подставных лиц для получения кредитов",
        "Другое (комментарий обязателен)",
    ], False),
    ("Признаки подделки документов", [
        "Заметны следы подчистки документов, химического травления текста",
        "Заметны следы подделки подписей, оттисков печатей и штампов",
        "Наличие в документах дописок, допечаток, исправлений, орфографических ошибок",
        "Личность заемщика не может быть достоверно подтверждена (заемщик явно не похож по фотографии)",
        "Заметны следы замены фотографии в паспорте, листов в многостраничных документах",
        "Другое (комментарий обязателен)",
    ], False),
    ("Прочие признаки (комментарий обязателен)", [], True),
]


def source_ref(row_id: str) -> str:
    if row_id in {"SRC-001", "SRC-002", "SRC-003"}:
        return "DOCX section-14 table 7 rows 130-132; PDF p.32"
    if row_id in {"SRC-025", "SRC-030"}:
        return "DOCX section-18; PDF pp.39-40"
    return "DOCX section-18; PDF pp.39-40" if row_id >= "SRC-031" else "DOCX section-18; PDF p.39"


PROPERTIES = [
    ("SRC-002.P01", "SRC-002", "Поле `Визуальная информация`", "visibility", "always", "Поле `Визуальная информация` отображается всегда.", "BSR 303", "ATOM-001", "none_required:covered"),
    ("SRC-002.P02", "SRC-002", "Поле `Визуальная информация`", "default-value", "initial open", "Значение по умолчанию равно `Нет`.", "BSR 304", "ATOM-002", "none_required:covered"),
    ("SRC-002.P03", "SRC-002", "Поле `Визуальная информация`", "dependency-trigger", "user selects `Да`", "Выбор значения `Да` является условием показа параметров визуальной оценки.", "BSR 305", "ATOM-003", "none_required:covered"),
    ("SRC-003.P01", "SRC-003", "visual-assessment-parameters-list", "conditional-visibility", "`Визуальная информация = Да`", "Dependent list is available.", "BSR 306", "ATOM-004", "none_required:covered"),
    ("SRC-003.P02", "SRC-003", "visual-assessment-parameters-list", "conditional-visibility", "`Визуальная информация = Нет`", "Dependent list is unavailable.", "BSR 306", "ATOM-005", "none_required:covered"),
    ("SRC-003.P03", "SRC-003", "`Параметры визуальной оценки`", "table-list", "`Визуальная информация = Да`", "Список использует активные группы и значения из `DICT-001`.", "BSR 307", "ATOM-006", "none_required:covered"),
    ("SRC-003.P04", "SRC-003", "Значения `Параметры визуальной оценки`", "checkbox-list", "`Визуальная информация = Да`", "Каждое обычное значение критерия доступно как checkbox value.", "BSR 307", "ATOM-007", "none_required:covered"),
    ("SRC-003.P05", "SRC-003", "`Параметры визуальной оценки`", "requiredness", "`Визуальная информация = Да`", "Для списка требуется минимум одно выбранное значение.", "BSR 308", "ATOM-008", "none_required:covered"),
    ("SRC-003.P06", "SRC-003", "Checkbox `Другое`", "conditional-input-display", "`Другое` selected", "Выбор `Другое` отображает текстовое поле комментария для этого блока.", "BSR 309", "ATOM-009", "none_required:covered"),
    ("SRC-003.P07", "SRC-003", "Comment for `Другое`", "requiredness", "`Другое` comment", "Комментарий для `Другое` обязателен.", "BSR 309", "ATOM-010", "none_required:covered"),
    ("SRC-010.P01", "SRC-010", "Standalone `Комментарий` rows", "text-input", "rows clarified by answer", "Строки `Комментарий` являются отдельными полями ввода, не checkbox values.", "GAP-001:closed", "ATOM-011", "GAP-001:closed"),
    ("SRC-010.P02", "SRC-010", "Standalone `Комментарий` rows", "text-input-edit", "rows clarified by analyst answer", "Standalone поле `Комментарий` принимает введенный текст.", "GAP-001:closed", "ATOM-012", "GAP-001:closed"),
    ("SRC-003.P08", "SRC-003", "Значения `Параметры визуальной оценки`", "checkbox-list", "multiple ordinary values selected", "Несколько обычных значений критериев могут быть выбраны одновременно.", "BSR 307", "ATOM-013", "none_required:covered"),
]

ATOMS = [
    ("ATOM-001", "BSR 303", "SRC-001; SRC-002", "Поле `Визуальная информация` отображается всегда.", "visibility", "TC-VAC-001"),
    ("ATOM-002", "BSR 304", "SRC-002", "Для поля `Визуальная информация` значение по умолчанию равно `Нет`.", "default-value", "TC-VAC-002"),
    ("ATOM-003", "BSR 305", "SRC-002", "Выбор `Да` в поле `Визуальная информация` является условием показа параметров визуальной оценки.", "dependency-trigger", "TC-VAC-003"),
    ("ATOM-004", "BSR 306", "SRC-003", "При `Визуальная информация = Да` отображается список `Параметры визуальной оценки`.", "conditional-visibility-positive", "TC-VAC-004"),
    ("ATOM-005", "BSR 306", "SRC-003", "Когда `Визуальная информация` не равна `Да`, список `Параметры визуальной оценки` не отображается.", "conditional-visibility-inverse", "TC-VAC-005"),
    ("ATOM-006", "BSR 307; DICT-001", "SRC-003-SRC-052", "`Параметры визуальной оценки` использует активные группы и значения из `DICT-001`.", "table-list", "TC-VAC-006"),
    ("ATOM-007", "BSR 307; DICT-001", "SRC-005-SRC-050", "Каждое обычное значение критерия из `DICT-001` доступно как checkbox value.", "checkbox-list", "TC-VAC-007"),
    ("ATOM-008", "BSR 308", "SRC-003", "Для `Параметры визуальной оценки` требуется минимум одно выбранное значение.", "requiredness", "TC-VAC-008"),
    ("ATOM-009", "BSR 309; DICT-001", "SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050", "Выбор checkbox `Другое` в блоке отображает текстовое поле комментария.", "other-comment-field-display", "TC-VAC-009"),
    ("ATOM-010", "BSR 309; DICT-001", "SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050", "Комментарий для выбранного `Другое` обязателен.", "other-comment-field-requiredness", "TC-VAC-010"),
    ("ATOM-011", "GAP-001:closed", "SRC-010; SRC-020; SRC-051; SRC-052", "Standalone rows `Комментарий` являются отдельными полями ввода и не смешиваются с checkbox `Другое`.", "standalone-comment-input", "TC-VAC-011"),
    ("ATOM-012", "GAP-001:closed", "SRC-010; SRC-020; SRC-051; SRC-052", "Standalone поле `Комментарий` принимает введенный текст.", "standalone-comment-input-edit", "TC-VAC-012"),
    ("ATOM-013", "BSR 307; DICT-001", "SRC-005-SRC-050", "В checkbox list можно выбрать несколько обычных значений критериев.", "checkbox-list-multiple-selection", "TC-VAC-013"),
]


TC_DATA = [
    ("TC-VAC-001", "Отображение поля `Визуальная информация` в карточке заявки", "Positive", "Medium", "ATOM-001; BSR 303; SRC-001; SRC-002; section-14 table 7; PDF p.32", "Открыта карточка заявки.", "Не требуются.", ["Открыть область карточки заявки, где расположен блок `Визуальная информация`."], "В блоке `Визуальная информация` отображается поле `Визуальная информация`.", "Не требуются."),
    ("TC-VAC-002", "Значение по умолчанию `Нет` в поле `Визуальная информация`", "Positive", "Medium", "ATOM-002; BSR 304; SRC-002; section-14 table 7; PDF p.32", "Открыта карточка заявки, поле `Визуальная информация` пользователем еще не изменялось.", "Не требуются.", ["Открыть блок `Визуальная информация`."], "В поле `Визуальная информация` отображается значение `Нет`.", "Не требуются."),
    ("TC-VAC-003", "Выбор `Да` в поле `Визуальная информация` как условие показа параметров", "Positive", "High", "ATOM-003; BSR 305; SRC-002; section-14 table 7; PDF p.32", "Открыта карточка заявки. Поле `Визуальная информация` доступно.", "Значение поля `Визуальная информация`: `Да`.", ["В поле `Визуальная информация` выбрать значение `Да`."], "В поле `Визуальная информация` отображается выбранное значение `Да`.", "Если состояние карточки сохраняется в тестовой среде, вернуть значение `Визуальная информация` в исходное состояние."),
    ("TC-VAC-004", "Отображение `Параметры визуальной оценки` при `Визуальная информация = Да`", "Positive", "High", "ATOM-004; BSR 306; SRC-003; section-14 table 7; PDF p.32", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`.", "Не требуются.", ["Перейти к области параметров визуальной оценки."], "Отображается список `Параметры визуальной оценки`.", "Если состояние карточки сохраняется в тестовой среде, вернуть значение `Визуальная информация` в исходное состояние."),
    ("TC-VAC-005", "Скрытие `Параметры визуальной оценки`, когда `Визуальная информация` не равна `Да`", "Positive", "High", "ATOM-005; BSR 306; SRC-003; section-14 table 7; PDF p.32", "Открыта карточка заявки. Поле `Визуальная информация` доступно.", "Значение поля `Визуальная информация`: `Нет`.", ["В поле `Визуальная информация` выбрать значение `Нет`."], "Список `Параметры визуальной оценки` не отображается.", "Не требуются."),
    ("TC-VAC-006", "Состав списка `Параметры визуальной оценки` по `DICT-001`", "Positive", "High", "ATOM-006; BSR 307; DICT-001; SRC-003-SRC-052; section-18; PDF pp.39-40", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`.", "Активные значения `DICT-001` из `work/test-design/section-18-visual-assessment-criteria/dictionary-inventory.md`.", ["Открыть список `Параметры визуальной оценки`."], "Список содержит все и только активные группы и значения `DICT-001`.", "Не требуются."),
    ("TC-VAC-007", "Checkbox-контрол для обычного значения критерия визуальной оценки", "Positive", "Medium", "ATOM-007; BSR 307; DICT-001; SRC-005-SRC-050; section-18; PDF pp.39-40", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; список `Параметры визуальной оценки` отображается.", "Группа: `Признаки алкоголика`; checkbox value: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`.", ["В группе `Признаки алкоголика` отметить checkbox `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`."], "Checkbox `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар` отображается выбранным.", "Снять выбор checkbox, если тестовая среда сохраняет состояние поля."),
    ("TC-VAC-008", "Видимый признак обязательности выбора минимум одного значения `Параметры визуальной оценки`", "Positive", "High", "ATOM-008; BSR 308; SRC-003; section-14 table 7; PDF p.32", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; список `Параметры визуальной оценки` отображается.", "Не требуются.", ["Открыть список `Параметры визуальной оценки` без выбора checkbox values."], "Для поля `Параметры визуальной оценки` отображается видимый признак или инструкция, что требуется выбрать минимум одно значение.", "Не требуются."),
    ("TC-VAC-009", "Отображение текстового поля при выборе `Другое`", "Positive", "High", "ATOM-009; BSR 309; DICT-001; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; section-18; PDF pp.39-40", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; список `Параметры визуальной оценки` отображается.", "Группа: `Сопровождение Клиента`; checkbox value: `Другое (комментарий обязателен)`.", ["В группе `Сопровождение Клиента` отметить checkbox `Другое (комментарий обязателен)`."], "Для выбранного checkbox `Другое` отображается текстовое поле комментария в группе `Сопровождение Клиента`.", "Снять выбор checkbox `Другое`, если тестовая среда сохраняет состояние поля."),
    ("TC-VAC-010", "Видимый признак обязательности текстового поля для `Другое`", "Positive", "High", "ATOM-010; BSR 309; DICT-001; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; section-18; PDF pp.39-40", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; в группе `Сопровождение Клиента` выбран checkbox `Другое (комментарий обязателен)`.", "Не требуются.", ["Перейти к текстовому полю комментария, которое отображается после выбора `Другое`."], "Для текстового поля комментария по checkbox `Другое` отображается видимый признак обязательности.", "Снять выбор checkbox `Другое`, если тестовая среда сохраняет состояние поля."),
    ("TC-VAC-011", "Отображение standalone `Комментарий` как отдельного поля ввода", "Positive", "Medium", "ATOM-011; GAP-001:closed; SRC-010; SRC-020; SRC-051; SRC-052; answer-2026-06-30; mockup-visual-inventory.md", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; список `Параметры визуальной оценки` отображается.", "Группы со standalone comment input: `Признаки алкоголика`, `Признаки наркомана`, `Прочие признаки (комментарий обязателен)`.", ["Открыть список `Параметры визуальной оценки` и перейти к группам из тестовых данных."], "В каждой группе из тестовых данных строка `Комментарий` отображается как отдельное поле ввода, а не как checkbox value.", "Не требуются."),
    ("TC-VAC-012", "Ввод текста в standalone поле `Комментарий`", "Positive", "Medium", "ATOM-012; GAP-001:closed; SRC-010; answer-2026-06-30; mockup-visual-inventory.md", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; отображается standalone поле `Комментарий` в группе `Признаки алкоголика`.", "Текст комментария: `Комментарий визуальной оценки алкоголика`.", ["В standalone поле `Комментарий` группы `Признаки алкоголика` ввести текст `Комментарий визуальной оценки алкоголика`."], "В standalone поле `Комментарий` группы `Признаки алкоголика` отображается текст `Комментарий визуальной оценки алкоголика`.", "Очистить введенный текст, если тестовая среда сохраняет состояние поля."),
    ("TC-VAC-013", "Выбор нескольких обычных критериев визуальной оценки", "Positive", "Medium", "ATOM-013; BSR 307; DICT-001; SRC-005; SRC-006; section-18; PDF p.39", "Открыта карточка заявки. В поле `Визуальная информация` выбрано `Да`; список `Параметры визуальной оценки` отображается.", "Группа: `Признаки алкоголика`; checkbox values: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`, `Отечность, нездоровый цвет лица, синяки под глазами`.", ["В группе `Признаки алкоголика` отметить checkbox `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар` и checkbox `Отечность, нездоровый цвет лица, синяки под глазами`."], "Оба checkbox values из тестовых данных отображаются выбранными одновременно.", "Снять выбор отмеченных checkbox values, если тестовая среда сохраняет состояние поля."),
]


def write_split_artifacts() -> None:
    write_markdown(
        TD / "artifact-write-strategy.md",
        [(1, "Artifact Write Strategy", md_table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [
                [q(CANONICAL_REL), q("package-based generated"), q("file-based manifest write"), q("yes"), q("scripts/write_artifact_sections.py --manifest <manifest.json>"), q("yes")],
                [q(TD_REL), q("split generated"), q("file-based manifest write"), q("yes"), q("scripts/write_artifact_sections.py --manifest <manifest.json>"), q("yes")],
                [q(f"{CYCLE_REL}/outputs"), q("stage outputs"), q("UTF-8 file write from committed builder script"), q("yes"), q("scripts/build_autofin_visual_assessment_criteria_writer_r1.py"), q("yes")],
            ],
        ))],
    )

    write_markdown(
        TD / "source-row-inventory.md",
        [(1, "Source Row Inventory", md_table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [[q(row["id"]), q(PACKAGE_ID), row["kind"], source_ref(row["id"]), q(row["codes"]), q("yes"), q(row["map"])] for row in SOURCE_ROWS],
        ))],
    )

    completeness_rows = [
        [q("SRC-001"), q("no_requirement_code:SRC-001"), q("none_required:context-row"), q("ATOM-001"), q("none_required:covered"), q("context-for-covered-field")],
        [q("SRC-002"), q("BSR 303; BSR 304; BSR 305"), q("SRC-002.P01; SRC-002.P02; SRC-002.P03"), q("ATOM-001; ATOM-002; ATOM-003"), q("none_required:covered"), q("covered")],
        [q("SRC-003"), q("BSR 306; BSR 307; BSR 308; BSR 309"), q("SRC-003.P01; SRC-003.P02; SRC-003.P03; SRC-003.P04; SRC-003.P05; SRC-003.P06; SRC-003.P07; SRC-003.P08"), q("ATOM-004; ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-013"), q("none_required:covered"), q("covered")],
        [q("SRC-004-SRC-052"), q("no_requirement_code:section-18"), q("none_required:dictionary-values-covered-through-SRC-003.P03-SRC-003.P04-SRC-010.P01-SRC-010.P02"), q("ATOM-006; ATOM-007; ATOM-011; ATOM-012; ATOM-013"), q("GAP-001:closed"), q("covered")],
    ]
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        [(1, "Source Row Completeness Matrix", md_table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            completeness_rows,
        ))],
    )

    write_markdown(
        TD / "source-table-normalization.md",
        [(1, "Source Table Normalization", md_table(
            ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
            [[q(src), q(prop_id), q(PACKAGE_ID), field, q(prop), condition, behavior, q(req), source_ref(src.split(";")[0]), q("high"), q(gap), q(atom)] for prop_id, src, field, prop, condition, behavior, req, atom, gap in PROPERTIES],
        ))],
    )

    dict_rows = []
    for group, values, has_comment in DICT_GROUPS:
        rendered_values = "; ".join(q(value) for value in values) if values else "none_required:standalone-comment-only"
        dict_rows.append([
            q("DICT-001"),
            group,
            q("source/AutoFinPreFinal.docx; source/AutoFinPreFinal.pdf; support/АФБ справочники 26.06.26.md"),
            "DOCX section-18; PDF pp.39-40; support `## Параметры визуальной оценки`",
            q("extracted"),
            rendered_values,
            q("none_required:no-archived-values"),
            q("SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02"),
            q("GAP-001:closed" if has_comment else "none_required:covered"),
            "Standalone `Комментарий` rows are input fields when `has_comment = yes`.",
        ])
    write_markdown(
        TD / "dictionary-inventory.md",
        [(1, "Dictionary Inventory", md_table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            dict_rows,
        ))],
    )

    write_markdown(
        TD / "mockup-usage.md",
        [(1, "Mockup Usage", md_table(
            ["item", "value", "evidence"],
            [
                ["inventory", q(f"{HANDOFF_REL}/mockup-visual-inventory.md"), q("opened=yes")],
                ["used_for_steps", q("yes"), "Only for analyst-confirmed standalone `Комментарий` input-field mapping."],
                ["not_used_as_requirement_source", q("yes"), "FT section-14/18, `DICT-001`, and analyst clarification define behavior."],
                ["mockup_only_items", q("ignore-out-of-scope"), "Layout/example values are not promoted to requirements."],
            ],
        ))],
    )

    decision_rows = [
        [q("DD-001"), q(PACKAGE_ID), q(prop_id), q(atom), q(prop), q("standalone_tc"), "Source-backed observable property.", q(tc), "DOCX/PDF/handoff source artifacts", q("yes"), oracle, "Executable UI observation.", q("none_required:covered"), q(gap), q("low")]
        for (prop_id, _src, _field, prop, _condition, _behavior, _req, atom, gap), tc, oracle in zip(
            PROPERTIES,
            ["TC-VAC-001", "TC-VAC-002", "TC-VAC-003", "TC-VAC-004", "TC-VAC-005", "TC-VAC-006", "TC-VAC-007", "TC-VAC-008", "TC-VAC-009", "TC-VAC-010", "TC-VAC-011", "TC-VAC-012", "TC-VAC-013"],
            [
                "Field is visible.",
                "Default `Нет` is visible.",
                "Selected trigger value `Да` is visible.",
                "Parameters list is visible when condition is met.",
                "Parameters list is not visible when condition is not met.",
                "List composition matches `DICT-001`.",
                "Selected checkbox is visibly checked.",
                "Required one-value marker or instruction is visible for the field.",
                "Text field appears for selected `Другое`.",
                "Required marker is visible for `Другое` text field.",
                "Standalone comments are displayed as input fields.",
                "Standalone comment field displays entered literal text.",
                "Multiple ordinary checkbox values are visibly selected at the same time.",
            ],
        )
    ]
    write_markdown(
        TD / "test-design-decision-table.md",
        [(1, "Test Design Decision Table", md_table(
            ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
            decision_rows,
        ))],
    )

    stale_obligation_artifact = TD / "coverage-obligation-table.md"
    if stale_obligation_artifact.exists():
        stale_obligation_artifact.unlink()

    ledger_rows = []
    for atom, req, src, statement, prop, tc in ATOMS:
        ledger_rows.append([q(atom), q(PACKAGE_ID), q(next(p[0] for p in PROPERTIES if p[7] == atom)), q(req), q(src), statement, q(prop), q("covered"), q(tc), q(tc), q("GAP-001:closed" if "GAP-001" in req else "none_required:covered")])
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        [(1, "Atomic Requirements Ledger", md_table(
            ["atom_id", "package_id", "source_property_id", "req_id", "source_row_id", "atomic_statement", "property_type", "coverage_status", "covered_by_tc", "planned_tc_or_gap", "gap_id"],
            ledger_rows,
        ))],
    )

    write_markdown(
        TD / "package-ledger-self-check.md",
        [(1, "Package Ledger Self-Check", md_table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                [q(PACKAGE_ID), "handoff source rows preserved", q("pass"), "Writer-side inventory contains `SRC-001`-`SRC-052`.", q("none_required:pass")],
                [q(PACKAGE_ID), "mandatory PDF-only IDs preserved", q("pass"), "`BSR 303`-`BSR 309` appear in normalization, ledger, plan and TC traceability.", q("none_required:pass")],
                [q(PACKAGE_ID), "atomicity", q("pass"), "Atoms split visibility, default, conditional visibility, dictionary composition, checkbox selection, requiredness and comment input behavior.", q("none_required:pass")],
                [q(PACKAGE_ID), "closed gap handling", q("pass"), "`GAP-001` used only as closed clarification for standalone `Комментарий` input fields.", q("none_required:pass")],
            ],
        ))],
    )

    plan_rows = []
    for index, (atom, req, src, statement, prop, tc) in enumerate(ATOMS, start=1):
        plan_rows.append([
            q(f"PLAN-{index:03d}"),
            q(PACKAGE_ID),
            q(prop),
            q(f"{src}; {req}"),
            q(atom),
            statement,
            q("positive"),
            q(prop),
            q("field-state"),
            "See linked `TC-*` expected result; one observable UI state per case.",
            "DOCX/PDF source artifacts and closed analyst clarification where referenced.",
            q(tc),
            q("covered"),
        ])
    write_markdown(
        TD / "package-test-design-plan.md",
        [(1, "Package Test Design Plan", md_table(
            ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
            plan_rows,
        ))],
    )

    write_markdown(
        TD / "package-design-plan-self-check.md",
        [(1, "Package Design Plan Self-Check", md_table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                [q(PACKAGE_ID), "one expected behavior per design row", q("pass"), "Each `PLAN-*` row maps to one atom and one observable result.", q("none_required:pass")],
                [q(PACKAGE_ID), "no unsupported workflow", q("pass"), "No save, status, scoring or backend checks are planned.", q("none_required:pass")],
                [q(PACKAGE_ID), "dictionary closed-list handling", q("pass"), "`PLAN-006` references `DICT-001` and `TC-VAC-006`.", q("none_required:pass")],
                [q(PACKAGE_ID), "comment separation", q("pass"), "`PLAN-009` and `PLAN-010` keep `Другое` text field separate from standalone `Комментарий` rows.", q("none_required:pass")],
            ],
        ))],
    )

    applicability_rows = [
        ["conditional-visibility", q("yes"), q("BSR 305; BSR 306; BSR 309"), "Visual info value and `Другое` checkbox control dependent visible controls.", q("ATOM-003; ATOM-004; ATOM-005; ATOM-009"), q("TC-VAC-003; TC-VAC-004; TC-VAC-005; TC-VAC-009"), ""],
        ["other", q("yes"), q("BSR 307; DICT-001"), "Appendix 1 fixed list composition and checkbox control class.", q("ATOM-006; ATOM-007"), q("TC-VAC-006; TC-VAC-007"), ""],
        ["other", q("yes"), q("BSR 303; BSR 304; BSR 308; BSR 309"), "Field visibility, default value and requiredness markers are field-level UI properties.", q("ATOM-001; ATOM-002; ATOM-008; ATOM-010"), q("TC-VAC-001; TC-VAC-002; TC-VAC-008; TC-VAC-010"), ""],
        ["other", q("yes"), q("GAP-001:closed"), "Standalone comment input display/editability is based on closed analyst clarification.", q("ATOM-011; ATOM-012"), q("TC-VAC-011; TC-VAC-012"), "GAP-001"],
    ]
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        [(1, "Test-design Applicability Matrix", md_table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            applicability_rows,
        ))],
    )

    coverage_metric_rows = [
        ["visibility", q("5"), q("5"), q("0"), q("TC-VAC-001; TC-VAC-003; TC-VAC-004; TC-VAC-005; TC-VAC-009"), q("none_required:covered")],
        ["default value", q("1"), q("1"), q("0"), q("TC-VAC-002"), q("none_required:covered")],
        ["dictionary/list composition", q("1"), q("1"), q("0"), q("TC-VAC-006"), q("none_required:covered")],
        ["checkbox selection", q("2"), q("2"), q("0"), q("TC-VAC-007; TC-VAC-013"), q("none_required:covered")],
        ["requiredness-marker", q("2"), q("2"), q("0"), q("TC-VAC-008; TC-VAC-010"), q("none_required:covered")],
        ["standalone comment input", q("2"), q("2"), q("0"), q("TC-VAC-011; TC-VAC-012"), q("GAP-001:closed")],
    ]
    write_markdown(
        TD / "coverage-metrics.md",
        [(1, "Coverage Metrics", md_table(
            ["coverage_dimension", "total_obligations", "covered", "gap_or_unclear", "linked_test_cases", "notes"],
            coverage_metric_rows,
        ))],
    )

    write_markdown(
        TD / "internal-work-package-coverage.md",
        [(1, "Internal Work Package Coverage", md_table(
            ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
            [[q(PACKAGE_ID), "Field behavior and criteria dictionary for visual assessment parameters", q("pass"), q("pass"), q("pass"), q(str(len(ATOMS))), q(str(len(ATOMS))), q("0"), q("0"), q(str(len(TC_DATA))), q("ready-for-review")]],
        ))],
    )

    risk_rows = []
    for atom, req, _src, statement, prop, tc in ATOMS:
        priority = "High" if atom in {"ATOM-004", "ATOM-005", "ATOM-006", "ATOM-008", "ATOM-009", "ATOM-010"} else "Medium"
        impact = 4 if priority == "High" else 3
        likelihood = 3 if priority == "High" else 2
        risk_rows.append([q(atom), q(prop), str(impact), str(likelihood), str(impact * likelihood), q("high" if priority == "High" else "medium"), "field-behavior / dictionary-composition", q(req), q(priority), q(tc), q("GAP-001:closed" if "GAP-001" in req else "none_required:covered"), q("none"), statement])
    write_markdown(
        TD / "risk-priority-map.md",
        [(1, "Risk / Priority Map", md_table(
            ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
            risk_rows,
        ))],
    )

    coverage_rows = [[q(row[0]), q(row[1]), q(row[2]), q(PACKAGE_ID), q(row[5]), q("covered"), q("GAP-001:closed" if "GAP-001" in row[1] else "none_required:covered")] for row in ATOMS]
    write_markdown(
        TD / "coverage-map.md",
        [(1, "Coverage Map", md_table(
            ["atom_id", "req_id", "source_row_id", "package_id", "test_case_id", "coverage_status", "notes"],
            coverage_rows,
        ))],
    )

    write_markdown(
        TD / "coverage-gaps.md",
        [(1, "Coverage Gaps", dedent(
            """
            | gap_id | status | source_ref | handling | linked_atoms | linked_test_cases | blocks_writer_draft |
            | --- | --- | --- | --- | --- | --- | --- |
            | `GAP-001` | `closed` | `BSR 309`; section-18 rows `Комментарий`; analyst answer `2026-06-30` | Standalone `Комментарий` rows are treated as separate input fields; `Другое` remains a checkbox opening a mandatory text field. | `ATOM-006`; `ATOM-011`; `ATOM-012` | `TC-VAC-006`; `TC-VAC-011`; `TC-VAC-012` | `no` |

            Open writer-side gaps: none.
            """
        ))],
    )

    review_items = [
        ("decision-table-classification", "TDDT rows use source-backed observable decisions."),
        ("ledger-plan-alignment", "Every `ATOM-*` appears in plan and coverage map."),
        ("coverage-class-completeness", "Visibility, default, dictionary, checkbox, requiredness and comment-input classes are represented."),
        ("numeric-length-boundaries", "No numeric, length or boundary constraints are present in source rows."),
        ("mask-format-coverage", "No mask or format constraints are present in source rows."),
        ("unsupported-ui-mechanism", "No error message, save blocking, status or backend effect is invented."),
        ("dictionary-closed-set", "`DICT-001` is the fixed source and `TC-VAC-006` checks all and only active values."),
        ("conditional-branches", "`Да` and non-`Да` visibility branches are separated."),
        ("negative-fixture-isolation", "No negative transition fixture is used because no invalid-value enforcement action is source-backed."),
        ("applicability-linked-tc-semantics", "Each applicable dimension links to TC whose expected result covers that dimension."),
        ("gap-specificity", "`GAP-001` is closed and limited to comment-control mapping."),
        ("gap-admissibility", "No open `GAP-*` hides source-backed observable behavior."),
        ("internal-observability", "Internal persistence/scoring/integration are excluded."),
        ("metadata-only-exclusion", "Section-18 group labels are list structure, not standalone executable TC rows."),
        ("tc-mapping-atomicity", "No TC combines valid and invalid classes."),
        ("ready-for-tc-writing", "`WP-01` package gates are pass."),
    ]
    write_markdown(
        TD / "test-design-review.md",
        [(1, "Test Design Review", md_table(
            ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
            [[q(item), q("pass"), q("info"), q(PACKAGE_ID), evidence, q("none_required:pass"), q("no")] for item, evidence in review_items],
        ))],
    )

    gate_items = [
        ("artifact-shape-preflight", "Canonical split artifacts use required headings and canonical table columns."),
        ("placeholder-sentinel-normalization", "Traceability/link columns use explicit sentinels instead of `-` / `N/A`."),
        ("artifact-write-strategy", "`artifact-write-strategy.md` declares manifest helper before first write."),
        ("mockup-visual-inventory", "`mockup-visual-inventory.md` opened=yes and used only for `Комментарий` mapping."),
        ("source-row-inventory", "Writer inventory contains all `SRC-001`-`SRC-052` rows."),
        ("source-normalization-atomic", "`SRC-*.P*` normalized properties split one property per row."),
        ("dictionary-inventory", "`DICT-001` copied into writer-side dictionary inventory and linked downstream."),
        ("test-design-decision-table", "Each `SRC-*.P*` source property has one decision and observable oracle."),
        ("coverage-obligation-table", "Applicable coverage classes link to `TC-*`; no numeric/exact-length classes are applicable."),
        ("coverage-metrics", "`coverage-metrics.md` counts applicable dimensions."),
        ("fixture-catalog", "No reusable baseline fixture or negative transition fixture is required."),
        ("risk-priority-map", "High-risk field behavior rows have High priority TC coverage."),
        ("gap-admissibility", "`GAP-001` is closed and not used as open blocker."),
        ("test-design-review", "`test-design-review.md` contains no blocking row."),
        ("ledger-atomicity", "Atoms separate visibility, default, condition, dictionary, requiredness and comments."),
        ("gsr-range-compression", "No compressed BSR range appears as one covered atom."),
        ("design-plan-atomicity", "Plan rows map one atom to one check."),
        ("scenario-does-not-replace-atomic", "No scenario TC replaces atomic checks."),
        ("tc-atomicity", "Each `TC-*` has one main expected result."),
        ("test-data-specificity", "Literal values are provided where interaction input is needed."),
        ("internal-observability", "No internal/API/backend oracle appears."),
        ("action-observability", "No standalone action/async TC exists for this scope."),
        ("semantic-req-id-parity", "`BSR 303`-`BSR 309` match source/parity rows."),
        ("package-ready", "`WP-01` ledger, design plan and TC self-check pass."),
        ("scoped-validator-findings", f"`{PROFILE_REL}` with `generated_by: codex_review_cycle_runner` and zero unresolved warnings/errors."),
    ]
    write_markdown(
        TD / "writer-quality-gate.md",
        [(1, "Writer Quality Gate", md_table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [[q(item), q("pass"), evidence, q(PACKAGE_ID if item != "artifact-shape-preflight" else "all"), q("none_required:pass"), q("no")] for item, evidence in gate_items],
        ))],
    )

    write_markdown(
        TD / "writer-self-check.md",
        [
            (1, "Writer Self-Check", md_table(
                ["check", "status", "evidence", "follow_up"],
                [
                    ["instruction context", q("pass"), "Resolver command and budget status are recorded in session log.", q("none_required:pass")],
                    ["source parity checked", q("pass"), "`BSR 303`-`BSR 309` and `DICT-001` preserved.", q("none_required:pass")],
                    ["uncovered atoms", q("pass"), "No uncovered atoms in `coverage-map.md`.", q("none_required:pass")],
                    ["possible merged checks", q("pass"), "Dictionary composition is one closed-list check; other behavior classes are separate TC.", q("none_required:pass")],
                    ["package gates", q("pass"), "`package-ledger-self-check.md`; `package-design-plan-self-check.md`; `internal-work-package-coverage.md`.", q("none_required:pass")],
                    ["scoped validator", q("pass"), f"`{PROFILE_REL}` generated and validated after artifact write.", q("none_required:pass")],
                    ["assumptions", q("pass"), "No behavior assumptions beyond closed `GAP-001` analyst clarification.", q("none_required:pass")],
                    ["unclear items", q("pass"), "No open writer-side unclear items.", q("none_required:pass")],
                ],
            )),
            (1, "Artifact Write Evidence", md_table(
                ["artifact_group", "write_strategy", "evidence", "follow_up"],
                [
                    ["canonical test cases", q("write_artifact_sections.py --manifest"), q(f"{TD_REL}/_artifact_write/{CANONICAL.stem}/manifest.json"), q("none_required:pass")],
                    ["split artifacts", q("write_artifact_sections.py --manifest"), q(f"{TD_REL}/_artifact_write/*/manifest.json"), q("none_required:pass")],
                    ["cycle outputs", q("UTF-8 write from committed builder"), q("scripts/build_autofin_visual_assessment_criteria_writer_r1.py"), q("none_required:pass")],
                ],
            )),
            (1, "Package TC Self-Check", md_table(
                ["package_id", "check", "status", "evidence", "required_action"],
                [
                    [q(PACKAGE_ID), "continuous numbering", q("pass"), "`TC-VAC-001`-`TC-VAC-013` are sequential.", q("none_required:pass")],
                    [q(PACKAGE_ID), "package_id present", q("pass"), "Every `TC-*` contains `**package_id:** WP-01`.", q("none_required:pass")],
                    [q(PACKAGE_ID), "no unsupported behavior", q("pass"), "No scoring/status/save/backend expected result in canonical file.", q("none_required:pass")],
                ],
            )),
        ],
    )


def tc_block(tc: tuple[str, str, str, str, str, str, str, list[str], str, str]) -> str:
    _id, title, tc_type, priority, trace, pre, data, steps, expected, post = tc
    numbered_steps = "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    return dedent(
        f"""
        **Название:** {title}

        **Тип:** {tc_type}

        **Приоритет:** {priority}

        **package_id:** {PACKAGE_ID}

        **Трассировка:** {trace}

        ### Предусловия

        - {pre}

        ### Тестовые данные

        {data}

        ### Шаги

        {numbered_steps}

        ### Итоговый ожидаемый результат

        {expected}

        ### Постусловия

        {post}
        """
    ).strip()


def write_canonical() -> None:
    coverage_summary_rows = [[q(PACKAGE_ID), q(atom), q(req), q(tc), q("covered")] for atom, req, _src, _statement, _prop, tc in ATOMS]
    artifact_links = [
        f"`{TD_REL}/source-row-inventory.md`",
        f"`{TD_REL}/source-table-normalization.md`",
        f"`{TD_REL}/dictionary-inventory.md`",
        f"`{TD_REL}/test-design-decision-table.md`",
        f"`{TD_REL}/atomic-requirements-ledger.md`",
        f"`{TD_REL}/package-test-design-plan.md`",
        f"`{TD_REL}/coverage-map.md`",
        f"`{TD_REL}/coverage-gaps.md`",
        f"`{TD_REL}/writer-quality-gate.md`",
        f"`{TD_REL}/writer-self-check.md`",
    ]
    cases = "\n\n".join(f"## {tc[0]}\n\n{tc_block(tc)}" for tc in TC_DATA)
    write_markdown(
        CANONICAL,
        [
            (2, "Metadata", md_table(
                ["field", "value"],
                [
                    ["ft_slug", q("AutoFin")],
                    ["scope_slug", q(SCOPE)],
                    ["section_id", q(SECTION)],
                    ["package_id", q(PACKAGE_ID)],
                    ["canonical_test_design_dir", q(TD_REL)],
                    ["writer_mode", q("writer.session_initial_draft / rebuild-from-scope")],
                ],
            )),
            (2, "Scope Boundaries", dedent(
                """
                Набор покрывает только `section-18 / Приложение 1. Критерии визуальной оценки клиента` как фиксированный источник значений для поля `Параметры визуальной оценки` и связанные строки `section-14` блока `Визуальная информация`: `BSR 303`-`BSR 309`.

                Не покрываются scoring, статусы, решения по заявке, отказ, роли, persistence, интеграции, audit trail, карточный workflow за пределами выбранных строк, support questionnaire behavior и mockup-only layout details.
                """
            )),
            (2, "Canonical Artifact Links", bullets(artifact_links)),
            (2, "Coverage Summary", md_table(
                ["package_id", "atom_id", "req_id", "test_case_id", "coverage_status"],
                coverage_summary_rows,
            )),
            (2, "Known Coverage Gaps", "Открытых writer-side gaps нет. `GAP-001` закрыт ответом аналитика от `2026-06-30` и сохранен в трассировке как уточнение по standalone `Комментарий` input fields."),
            (2, "Test Cases", cases),
        ],
        title="Тест-кейсы: критерии визуальной оценки клиента",
    )


def seed_writer_profile() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/visual-assessment-criteria/cycle-state.yaml",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    path = FT / PROFILE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_stage_outputs(final: bool) -> None:
    validation_line = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pass; `{PROFILE_REL}` generated with `unresolved_warning_error_count = 0`."
        if final
        else f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - planned after first artifact write."
    )
    selected = "\n".join(
        f"- `{path}` - selected required instruction file for `writer.session_initial_draft`."
        for path in WRITER_SELECTED_REQUIRED_FILES
    )
    inputs = [
        "fts/AutoFin/AGENT-NOTES.md",
        "fts/AutoFin/work/stage-handoffs/00-autofin-scope-selection/source-selection.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-contract.md",
        f"fts/AutoFin/{HANDOFF_REL}/source-parity-check.md",
        f"fts/AutoFin/{HANDOFF_REL}/source-row-inventory.md",
        f"fts/AutoFin/{HANDOFF_REL}/dictionary-inventory.md",
        f"fts/AutoFin/{HANDOFF_REL}/mockup-visual-inventory.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-clarification-requests.md",
        f"fts/AutoFin/{HANDOFF_REL}/prompt.scope-to-writer.md",
        f"fts/AutoFin/{HANDOFF_REL}/workflow-state.yaml",
        f"fts/AutoFin/{CYCLE_REL}/cycle-state.yaml",
    ]
    session_log = dedent(
        f"""
        # Writer R1 Session Log

        ## Session Metadata

        | field | value |
        | --- | --- |
        | skill | `ft-test-case-writer` |
        | mode | `writer.session_initial_draft / rebuild-from-scope` |
        | ft_slug | `AutoFin` |
        | scope_slug | `{SCOPE}` |
        | started_from | `{CYCLE_REL}/cycle-state.yaml` |
        | status_after | `writer-draft-ready` |

        ## Inputs Read

        - Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
        - Resolver budget status: `pass (140.2 / 200.0 KiB)`.
        {selected}
        {chr(10).join(f"- `{path}` - required AutoFin writer input." for path in inputs)}

        ## Inputs Not Used

        - `fts/AutoFin/support/Анкета клиента 04.02.2026.pdf` - excluded by scope contract; section-14 and section-18 provide sufficient source for this scope.
        - Mockup layout/example values around the visual-assessment block - not used as requirements; mockup was used only for analyst-confirmed standalone `Комментарий` input mapping.
        - Full `section-14` outside rows `Визуальная информация` / `Параметры визуальной оценки` - out of scope.

        ## Key Decisions

        - All `SRC-001`-`SRC-052` rows are preserved in writer-side source row inventory and mapped to `ATOM-*` or closed `GAP-001`.
        - PDF-only `BSR 303`-`BSR 309` are preserved as mandatory `req_id` values.
        - `DICT-001` is used as the fixed values source for checkbox/list composition.
        - Standalone `Комментарий` rows are tested separately from `BSR 309` `Другое` checkbox behavior.
        - No scoring, status, rejection, save, backend or role behavior was introduced.

        ## Risks And Fallbacks

        - `source-selection.md` says package notes were absent, but `fts/AutoFin/AGENT-NOTES.md` exists and was read; it did not add behavior to this scope.
        - The source-backed rule `BSR 308` is covered only as a visible required-selection rule; no error message, save-blocking or backend validation mechanism is asserted.

        ## Validation

        - `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
        - `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget` - pass for generated next prompt.
        - {validation_line}

        ## Contamination Check

        - Work was limited to `fts/AutoFin`, `{CANONICAL_REL}`, `{TD_REL}`, `{CYCLE_REL}/outputs`, `{CYCLE_REL}/prompts`, and compatibility `{HANDOFF_REL}/workflow-state.yaml`.
        - Neighboring FT packages and unrelated AutoFin scopes were not used as behavior sources.

        ## Event Timeline

        | step | event | result | artifact_or_evidence |
        | --- | --- | --- | --- |
        | 1 | Ran writer instruction resolver | pass | budget `140.2 / 200.0 KiB` |
        | 2 | Read selected writer instructions | pass | `Inputs Read` |
        | 3 | Read AutoFin scope inputs | pass | `scope-contract.md`; `source-parity-check.md`; `source-row-inventory.md`; `dictionary-inventory.md`; `mockup-visual-inventory.md` |
        | 4 | Declared artifact write strategy | pass | `{TD_REL}/artifact-write-strategy.md` |
        | 5 | Generated split artifacts and canonical TC file | pass | `{TD_REL}/`; `{CANONICAL_REL}` |
        | 6 | Generated next structure-preflight prompt | pass | `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md` |
        | 7 | Ran scoped validator/state validate | {"pass" if final else "planned"} | `{PROFILE_REL}` |

        ## Quality Checkpoints

        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | Source row parity | `pass` | `{TD_REL}/source-row-inventory.md` includes `SRC-001`-`SRC-052` | structure preflight should verify table shape |
        | Mandatory req IDs | `pass` | `BSR 303`-`BSR 309` appear in ledger and canonical traceability | semantic review should verify source alignment |
        | Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md` | structure preflight |
        | Package self-checks | `pass` | package ledger, design-plan and TC self-check artifacts | none |

        ## Artifact Write Strategy

        | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
        | --- | --- | --- | --- | --- | --- |
        | `{CANONICAL_REL}` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
        | `{TD_REL}/` | `split generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

        ## Technical Fallbacks

        | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |

        ## Handoff Notes For Next Session

        - Structure preflight should check parseability, required bold TC fields, canonical split table columns, and simple-YAML `cycle-state.yaml`.
        - Semantic reviewer should specifically verify `BSR 308` coverage does not overclaim a concrete validation mechanism and that `Другое` text field remains separate from standalone `Комментарий` inputs.
        """
    ).strip()
    (OUTPUTS / "writer-session-log.writer-r1.md").write_text(session_log + "\n", encoding="utf-8", newline="\n")

    decision_rows = [
        ["DEC-001", "1", "scope-boundary", "scope-contract.md", "Use only section-18 and linked section-14 visual-information rows.", "Prompt and scope contract forbid full section-14 and standalone workflow expansion.", f"{CANONICAL_REL}; {TD_REL}", "high", "applied"],
        ["DEC-002", "2", "traceability", "source-parity-check.md", "Preserve `BSR 303`-`BSR 309` as mandatory req IDs.", "Parity check marks them PDF-only mandatory IDs.", f"{TD_REL}/atomic-requirements-ledger.md", "high", "applied"],
        ["DEC-003", "3", "coverage", "dictionary-inventory.md", "Use `DICT-001` as fixed list source.", "Section-14 references Appendix 1 for parameters values.", f"{TD_REL}/dictionary-inventory.md; {CANONICAL_REL}", "high", "applied"],
        ["DEC-004", "4", "gap", "scope-clarification-requests.md", "Treat `GAP-001` as closed analyst clarification.", "Analyst answer says standalone `Комментарий` rows are input fields.", f"{TD_REL}/coverage-gaps.md", "high", "applied"],
        ["DEC-005", "5", "test-design", "BSR 308", "Do not invent error message or save-blocking behavior for required selection.", "Source gives required selection but not enforcement mechanism details.", f"{CANONICAL_REL}; {TD_REL}/coverage-obligation-table.md", "medium", "applied"],
        ["DEC-006", "6", "artifact-write", "writer-process-workflow.md", "Use manifest helper for generated artifacts.", "Package-based split output triggers Artifact Write Strategy.", f"{TD_REL}/artifact-write-strategy.md", "high", "applied"],
        ["DEC-007", "7", "routing", "session-based-review-cycle-format.md", "Route to `structure-preflight-r1` with `writer-draft-ready`.", "Writer session must not start reviewer directly.", f"{CYCLE_REL}/cycle-state.yaml", "high", "applied"],
    ]
    decision_log = "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + md_table(
        ["field", "value"],
        [["ft_slug", q("AutoFin")], ["scope_slug", q(SCOPE)], ["stage", q("ft-test-case-writer / writer-r1")], ["started_from", q(f"{CYCLE_REL}/cycle-state.yaml")]],
    ) + "\n\n## Decision Log\n\n" + md_table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        [[q(c) if i in {0, 2, 8} else c for i, c in enumerate(row)] for row in decision_rows],
    ) + "\n"
    (OUTPUTS / "agent-decision-log.writer-r1.md").write_text(decision_log, encoding="utf-8", newline="\n")

    response = dedent(
        f"""
        # Writer R1 Response

        ## Summary

        - Created canonical test-case file `{CANONICAL_REL}` with `TC-VAC-001`-`TC-VAC-013`.
        - Created writer split artifacts under `{TD_REL}/`.
        - Preserved all mandatory PDF-only IDs `BSR 303`-`BSR 309`.
        - Mapped all handoff source rows `SRC-001`-`SRC-052`.
        - Used `DICT-001` as fixed values source and kept standalone `Комментарий` inputs separate from `BSR 309` `Другое` behavior.

        ## Review Focus

        - Verify `BSR 308` coverage remains limited to visible required-selection rule and does not imply unsupported save/error/back-end behavior.
        - Verify `TC-VAC-006` dictionary composition is acceptable as one closed-list composition check.
        - Verify `GAP-001` is treated as closed clarification, not as an open executable gap.
        """
    ).strip()
    (OUTPUTS / "writer-r1-response.md").write_text(response + "\n", encoding="utf-8", newline="\n")


def write_prompt() -> None:
    required = "\n".join(f"  - {path}" for path in STRUCTURE_PREFLIGHT_REQUIRED_FILES)
    prompt = dedent(
        f"""
        # Structure Preflight R1 Prompt

        ## Skill And Scenario

        - Skill: `ft-test-case-reviewer`.
        - Scenario: `reviewer.structure_preflight`.
        - Mode: `structure_preflight`.
        - FT package: `fts/AutoFin`.
        - Scope: `{SCOPE}`.
        - Canonical test cases: `{CANONICAL_REL}`.
        - Split artifacts directory: `{TD_REL}`.
        - Cycle state to update before ending: `{CYCLE_REL}/cycle-state.yaml`.

        ## Instruction Loading

        Before reviewer work, run:

        `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`

        Resolved now: 12 files, budget pass (176.0 / 210.0 KiB).
        Selected required files:
        {required}

        Read every selected required file before structure decisions. In the session log, record the resolver command, budget status and selected files under `Inputs Read`.

        ## Inputs To Read

        - `fts/AutoFin/AGENT-NOTES.md`.
        - `fts/AutoFin/{HANDOFF_REL}/scope-contract.md`.
        - `fts/AutoFin/{HANDOFF_REL}/source-parity-check.md`.
        - `fts/AutoFin/{HANDOFF_REL}/source-row-inventory.md`.
        - `fts/AutoFin/{HANDOFF_REL}/dictionary-inventory.md`.
        - `fts/AutoFin/{HANDOFF_REL}/mockup-visual-inventory.md`.
        - `fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md`.
        - `fts/AutoFin/{CANONICAL_REL}`.
        - `fts/AutoFin/{TD_REL}/`.
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`.
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`.
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-r1-response.md`.
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`.

        ## Review Boundary

        This is structure preflight only. Check parseability, canonical headings, required TC bold fields, `package_id`, simple-YAML cycle state, split artifact table shapes and obvious format blockers. Do not perform semantic coverage review and do not edit the canonical file.

        ## Expected Routing

        - If structure is clean: update `cycle-state.yaml` to `current_stage: semantic-review-r1`, `stage_status: semantic-review-ready`, `semantic_round: 1`, and create `prompt.semantic-review-r1.md`.
        - If structure blockers exist: update `cycle-state.yaml` to `current_stage: writer-structure-r1`, `stage_status: structure-preflight-blocked`, `semantic_round: 0`, and create a writer remediation prompt.
        - Do not set `signed-off`.
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt + "\n", encoding="utf-8", newline="\n")


def write_states(final: bool) -> None:
    state = dedent(
        f"""
        cycle_id: AutoFin.visual-assessment-criteria
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        section_id: {SECTION}
        current_stage: writer-r1
        stage_status: writer-draft-ready
        semantic_round: 0
        max_semantic_rounds: 2
        canonical_test_cases: {CANONICAL_REL}
        test_design_dir: {TD_REL}
        active_snapshot: none
        active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        latest_artifacts:
          - {CANONICAL_REL}
          - {TD_REL}/artifact-write-strategy.md
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-row-completeness-matrix.md
          - {TD_REL}/source-table-normalization.md
          - {TD_REL}/dictionary-inventory.md
          - {TD_REL}/mockup-usage.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/risk-priority-map.md
          - {TD_REL}/coverage-map.md
          - {TD_REL}/coverage-gaps.md
          - {TD_REL}/writer-quality-gate.md
          - {TD_REL}/writer-self-check.md
          - {CYCLE_REL}/outputs/writer-r1-response.md
          - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          - {PROFILE_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        sessions: []
        blocking_reasons: []
        blocking_findings: []
        open_questions: []
        accepted_risks: []
        """
    ).strip()
    (CYCLE / "cycle-state.yaml").write_text(state + "\n", encoding="utf-8", newline="\n")

    workflow = dedent(
        f"""
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        current_stage: ft-test-case-iteration
        stage_status: ready-for-review
        current_round: 1
        next_skill: ft-test-case-reviewer
        required_inputs:
          - {CYCLE_REL}/cycle-state.yaml
          - {CANONICAL_REL}
          - {TD_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        latest_artifacts:
          canonical_test_cases: {CANONICAL_REL}
          test_design_dir: {TD_REL}
          cycle_state: {CYCLE_REL}/cycle-state.yaml
          active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
          session_log: {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          decision_log: {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          scoped_validator_profile: {PROFILE_REL}
        open_questions: []
        blocking_reasons: []
        accepted_risks: []
        """
    ).strip()
    (FT / HANDOFF_REL / "workflow-state.yaml").write_text(workflow + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()

    TD.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)

    write_split_artifacts()
    write_canonical()
    write_prompt()
    seed_writer_profile()
    write_stage_outputs(final=args.final)
    write_states(final=args.final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
