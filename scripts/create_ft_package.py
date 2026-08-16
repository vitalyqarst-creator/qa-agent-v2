from __future__ import annotations

import argparse
from pathlib import Path


PACKAGE_DIRS = ("source", "support", "mockups", "work", "test-cases")
NOTES = """# Контекст FT-пакета

## Исходные материалы

- Основное ФТ (DOCX): _добавить файл в `source/`_
- Машиночитаемая версия ФТ (XHTML): _добавить файл в `source/`_
- PDF для визуальной сверки: _добавить файл в `source/`_

## Дополнительные входы

- Справочники и утверждённые ответы БА: `support/`.
- Макеты: `mockups/`.
- Figma: при наличии указать ссылку и релевантные страницы/фреймы ниже. Figma уточняет UI, но не заменяет ФТ.

## Данные

Указать здесь доступные источники тестовых данных: локальные fixtures, provider интеграции, публичный справочник или синтетический генератор. Не добавлять credentials.
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


def main() -> int:
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
