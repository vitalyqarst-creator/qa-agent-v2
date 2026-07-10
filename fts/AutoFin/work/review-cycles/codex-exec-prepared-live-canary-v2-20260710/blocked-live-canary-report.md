# Отчёт о блокировке prepared-package live canary v2

## Итог

- Статус цикла: `blocked-command-budget`.
- Writer session: `019f4bdc-b08d-7ba1-b9de-b4e33383c7bb`.
- Reviewer session: `019f4bde-7dfa-7ca0-92f2-4425af7cb4b3`.
- Writer и reviewer запускались в отдельных ephemeral-сессиях.
- Writer создал draft, прошедший deterministic gates.
- Reviewer не сформировал итоговый review contract: частичный результат корректно отклонён runner-ом.
- Promotion был выключен; production-файл `test-cases/3-iteration-smoke-widget-selection-types.md` не создан.
- Существующие production test cases не изменялись.

## Writer fast path

| показатель | результат |
| --- | ---: |
| prepared package v2 | `15099 bytes`, `4` файла |
| input artifacts по stage metrics | `52471 bytes`, `8` файлов |
| first output | `0.640 s` |
| first meaningful artifact | `79.015 s` при deadline `90 s` |
| полная длительность | `118.156 s` |
| command executions | `5 / 8` |
| test cases в draft | `3` |
| testable obligations | `3 / 3` покрыты |
| seed gate | `passed` |
| structure validator | `passed` |
| obligation gate | `passed` |
| evidence-access gate | `passed`, запрещённых чтений нет |

Writer использовал inline scope-local evidence, изменил runner-owned seed и не перечитывал полный skill, references, package или исходные DOCX/XHTML/PDF. Значит, eligibility contract, compact runtime profile, evidence slicing, first-artifact deadline и contamination guard подтвердились в реальном `codex exec`.

## Реальный blocker

Reviewer был остановлен через `51.438 s` со статусом `blocked-command-budget`: runner зарегистрировал `9` command executions при бюджете `8`. До остановки reviewer:

1. выполнил environment probe;
2. прочитал полный `skills/ft-test-case-reviewer/SKILL.md`;
3. повторно прочитал этот skill двумя диапазонами строк;
4. выполнил несколько поисков по `instruction-loading-manifest.md`.

Reviewer не перешёл к чтению prepared evidence, writer draft и deterministic gate reports. Следовательно, проблема не в качестве draft, auth, CLI, sandbox, source package, idle timeout или JSON schema. Prepared reviewer scenario всё ещё допускает тяжёлую общую процедуру загрузки инструкций и не имеет изолированного inline runtime contract, сопоставимого с writer fast path.

## Решение об остановке

Benchmark из трёх прогонов не выполнялся. Повторные запуски сейчас измеряли бы уже подтверждённый дефект reviewer entrypoint и расходовали бы время без новой информации.

Следующая итерация должна сначала:

1. изолировать `reviewer.session_prepared_semantic` коротким runtime profile без чтения полного reviewer skill и instruction manifest;
2. передавать reviewer-у inline draft, atomic obligations, selected evidence и краткие результаты deterministic gates;
3. запретить повторное чтение полных source/skill/reference файлов тем же evidence-access gate;
4. добавить reviewer first-artifact deadline и регрессионные тесты на отсутствие тяжёлого bootstrap;
5. повторить один canary с прежними лимитами и только после его завершения запускать benchmark `3` прогонов.
