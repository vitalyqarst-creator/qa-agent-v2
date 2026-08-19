from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.runtime_io import configure_utf8_stdio
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio


FORBIDDEN_PATHS = (
    "evals",
    "release",
    "test_case_agent",
    "references/agent",
    "references/qa",
    "skills/ft-test-case-iteration",
    "skills/ft-ui-automation-prep",
    "skills/agent-architecture-auditor",
)
REQUIRED_PATHS = (
    "AGENTS.md",
    "skills/ft-source-locator/SKILL.md",
    "skills/ft-scope-analyzer/SKILL.md",
    "skills/ft-test-case-writer/SKILL.md",
    "skills/ft-test-case-reviewer/SKILL.md",
    "references/runtime/test-data-fixtures.md",
    "references/runtime/source-selection.md",
    "references/runtime/scope-analysis.md",
    "references/runtime/test-design-profiles.md",
    "references/runtime/test-design-matrix.md",
    "references/runtime/test-case-runtime.md",
    "references/runtime/review-record.md",
    "references/runtime/session-topology.md",
    "scripts/create_ft_package.py",
    "scripts/cleanup_runtime_temp.py",
    "scripts/render_runtime_pdf.py",
    "scripts/runtime_cleanliness.py",
    "scripts/runtime_state.py",
    "scripts/runtime_workflow_state.py",
    "scripts/capture_dadata_fixture.py",
    "scripts/validate_fixture_catalog.py",
    "scripts/validate_runtime_test_data.py",
    "scripts/validate_runtime_source.py",
    "scripts/validate_runtime_tc.py",
    "scripts/validate_runtime_matrix.py",
    "scripts/validate_runtime_scope.py",
    "scripts/runtime_traceability.py",
    "scripts/validate_runtime_review.py",
    "scripts/runtime_review_dispatch.py",
    "scripts/runtime_review_delta.py",
    "scripts/runtime_session_registry.py",
)

REQUIRED_REFERENCE_CONSUMERS = {
    "AGENTS.md": (
        "references/runtime/test-design-profiles.md",
        "references/runtime/review-record.md",
        "references/runtime/session-topology.md",
    ),
    "skills/ft-source-locator/SKILL.md": (
        "references/runtime/session-topology.md",
        "references/runtime/source-selection.md",
    ),
    "skills/ft-scope-analyzer/SKILL.md": (
        "references/runtime/scope-analysis.md",
    ),
    "skills/ft-test-case-writer/SKILL.md": (
        "references/runtime/test-design-profiles.md",
        "references/runtime/review-record.md",
        "references/runtime/scope-analysis.md",
        "references/runtime/session-topology.md",
    ),
    "skills/ft-test-case-reviewer/SKILL.md": (
        "references/runtime/test-data-fixtures.md",
        "references/runtime/test-design-profiles.md",
        "references/runtime/review-record.md",
        "references/runtime/scope-analysis.md",
        "references/runtime/session-topology.md",
    ),
}

REQUIRED_POLICY_MARKERS = {
    "AGENTS.md": (
        "Senior QA-инженер",
        "work/scope-clarification-requests.md",
        "нейтральным транспортным конвертом",
        "новый route не означает повторный source locator",
        "одним содержательным проходом по умолчанию",
        "отдельной верхнеуровневой Codex-сесси",
    ),
    "skills/ft-source-locator/SKILL.md": (
        "не загружай целиком объёмные справочники",
        "scripts/cleanup_runtime_temp.py",
        "scripts/render_runtime_pdf.py",
        "не читай реализацию validator-а",
        "`AGENT-NOTES.md` является входом пользователя",
    ),
    "skills/ft-scope-analyzer/SKILL.md": (
        "source-row-inventory.md",
        "Проверку согласованности",
        "--print-contract",
        "нерелевантные визуальные входы не перечисляй",
        "**Ответ БА:** _Введите ответ здесь._",
        "Один содержательный проход — default",
    ),
    "skills/ft-test-case-writer/SKILL.md": (
        "доступны writer-у только для чтения",
        "work/practical/<scope>/test-design-matrix.md",
        "blocked-data-preparation",
        "validate_runtime_test_data.py",
    ),
    "skills/ft-test-case-reviewer/SKILL.md": (
        "Отсутствие стендовой записи",
        "готовность исполнения",
        "механическое включение всего родительского фрагмента",
        "шаг представления",
    ),
    "references/runtime/scope-analysis.md": (
        "### Строки таблицы",
        "### Визуальная сверка",
        "Неприменимые аспекты пропускаются",
        "| Родительская обязанность |",
    ),
    "references/runtime/test-data-fixtures.md": (
        "| Границы и классы |",
        "Шаг представления:",
        "Источник наследуется транзитивно",
        "data-materialization.json",
    ),
    "references/runtime/test-design-matrix.md": (
        "| Готовность |",
        "нет-бизнес-результата",
        "workflow-state.yaml",
    ),
    "references/runtime/session-topology.md": (
        'environment: {type: "local"}',
        "Начальный semantic prompt непосредственно в `create_thread` запрещён",
        "`waitingOnApproval`",
        "обоих обязательных файлов `source-selection.md` и `workflow-state.yaml`",
        "полностью читает role-skill",
        "skills/ft-test-case-reviewer/SKILL.md",
        "Модель и уровень рассуждений",
    ),
    "references/runtime/source-selection.md": (
        "scripts/render_runtime_pdf.py",
        "не требует ручного вызова Poppler",
        "`AGENT-NOTES.md` — пользовательский вход",
    ),
}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in FORBIDDEN_PATHS:
        if (root / relative_path).exists():
            errors.append(f"forbidden runtime artifact exists: {relative_path}")
    for relative_path in REQUIRED_PATHS:
        if not (root / relative_path).is_file():
            errors.append(f"missing runtime artifact: {relative_path}")
    for relative_path, required_references in REQUIRED_REFERENCE_CONSUMERS.items():
        path = root / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for reference in required_references:
            if reference not in content:
                errors.append(f"runtime consumer {relative_path} does not load {reference}")
    for relative_path, markers in REQUIRED_POLICY_MARKERS.items():
        path = root / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(f"runtime policy {relative_path} is missing required marker {marker!r}")
    matrix_reference = root / "references/runtime/test-design-matrix.md"
    if matrix_reference.is_file() and "dadata" in matrix_reference.read_text(encoding="utf-8").casefold():
        errors.append("generic test-design matrix reference contains provider-specific DaData rule")
    return errors


def main() -> int:
    configure_utf8_stdio()
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
