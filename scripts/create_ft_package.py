from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.runtime_io import configure_utf8_stdio
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio


PACKAGE_DIRS = ("source", "support", "mockups", "work", "test-cases")
NOTES = """# Контекст FT-пакета

## Исходные материалы

- Канонический источник ФТ: _добавить один файл в `source/`_
- Нормализованное XHTML-представление: _source locator создаст из DOCX либо зарегистрирует нативный XHTML_
- Визуальный источник: _добавить PDF/рендер только если рисунки или сложная разметка несут смысл_

## Дополнительные входы

- Справочники и утверждённые ответы БА: `support/`.
- Макеты: `mockups/`.
- Figma: при наличии указать ссылку и релевантные страницы/фреймы ниже. Figma уточняет UI, но не заменяет ФТ.

## Данные

Указать здесь доступные источники тестовых данных: локальные fixtures, provider интеграции, публичный справочник или синтетический генератор. Не добавлять credentials.
"""
CLARIFICATION_REGISTER = """# Реестр вопросов к БА

Вопросы пока не сформированы.
"""


def create_package(destination: Path) -> None:
    destination = destination.resolve()
    if destination.exists():
        existing = list(destination.iterdir())
        if existing:
            raise ValueError(f"package destination must be new or empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for name in PACKAGE_DIRS:
        (destination / name).mkdir(exist_ok=True)
    notes = destination / "AGENT-NOTES.md"
    if not notes.exists():
        notes.write_text(NOTES, encoding="utf-8", newline="\n")
    clarification_register = destination / "work" / "scope-clarification-requests.md"
    if not clarification_register.exists():
        clarification_register.write_text(CLARIFICATION_REGISTER, encoding="utf-8", newline="\n")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Create an empty FT package without copying repository artifacts."
    )
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        create_package(args.destination)
    except ValueError as exc:
        parser.error(str(exc))
    print(args.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
