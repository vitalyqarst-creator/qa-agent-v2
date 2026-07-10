# Отчёт о блокировке prepared-package live smoke

## Итог

- Статус цикла: `blocked-idle-timeout`.
- Writer session: `019f4bba-0daf-74b2-bb82-5f8974c39bac`.
- Writer draft не создан.
- Reviewer не запускался.
- Promotion был выключен; production-файл `test-cases/3-iteration-smoke-widget-selection-types.md` не создан.
- Существующие production test cases не изменялись.

## Проверенные улучшения

| показатель | результат |
| --- | ---: |
| четыре prepared package файла | `27200 bytes` |
| input artifacts по stage metrics | `42152 bytes`, `6` файлов |
| прежний blocked smoke | около `38.8 MB` ссылочных артефактов |
| first output | `1.609 s` |
| длительность до остановки | `108.812 s` |
| command executions | `9 / 12` |
| полный DOCX/XHTML/PDF fallback | не использовался |
| чтение generated TC / canary evidence | не обнаружено |

Compact handoff и contamination guard сработали: writer не повторял source locator, extraction или PDF/DOCX-анализ и не обращался к полным источникам.

## Реальный blocker

После environment probe writer последовательно прочитал полный `ft-test-case-writer/SKILL.md`, `prepared-stage-package-format.md`, `writer-runtime-workflow.md` и четыре package-файла. Затем в течение `60 s` не появилось ни одного JSONL-события и не был записан минимальный draft. Runner завершил процесс по idle budget до общего лимита `180 s`.

Это не auth, CLI, sandbox, hash или command-budget failure. Остаточная проблема находится в порядке работы writer-а: даже при компактном source package он сначала загружает около `33 KiB` общих writer instructions и откладывает первую запись до завершения внутреннего проектирования.

## Следующая рекомендуемая итерация

Не увеличивать timeout как основной fix. Рекомендуемый следующий эксперимент:

1. Сжать основной `ft-test-case-writer/SKILL.md`, вынеся обычные/deep правила в references, и оставить в нём короткий prepared entrypoint.
2. Научить builder формировать scope-local evidence excerpts вместо полного конкатенирования `AGENT-NOTES.md` и handoff-файлов.
3. Добавить runner-owned draft skeleton с исходным hash и требованием meaningful change, чтобы первая запись происходила до semantic refinement.
4. Повторить один live smoke с теми же `180/60/12` budgets; увеличение idle budget рассматривать только как отдельный контролируемый эксперимент.

Benchmark нескольких прогонов не выполнялся: условие остановки на реальном live blocker сработало.
