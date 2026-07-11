# AutoFin source-boundary clarification

## Статус предыдущего blocker

`evals/prepared-cross-scope-validation/20260711/blocker-report.md` остаётся immutable evidence автоматического запуска, но не является blocker для продолжения текущего AutoFin prototype.

Автоматизация выбрала `fts/ft-2-OF_17`, потому что её prompt требовал numeric/validation scope и не закреплял единственный разрешённый FT package. Это расширило фактический scope без пользовательского разрешения.

## Каноническая граница продолжения

- FT package: `fts/AutoFin`.
- DOCX source of truth: `fts/AutoFin/source/FT4AutoFinFinal.docx`.
- Machine-readable source: `fts/AutoFin/source/FT4AutoFinFinal.xhtml`.
- Structural cross-check: `fts/AutoFin/source/FT4AutoFinFinal.pdf`.
- Package-specific context: `fts/AutoFin/AGENT-NOTES.md`.
- Neighboring `fts/*` packages are forbidden as scope/source substitutes.

## Решение

Compiler принимает ожидаемый `ft_slug` явно, требует workflow-linked `source-selection.md` и блокирует source/output/attempt paths за пределами ожидаемого FT package. Если нужный класс scope отсутствует внутри AutoFin, результатом должен быть `not-applicable` или явный input blocker, а не переход к соседнему пакету.
