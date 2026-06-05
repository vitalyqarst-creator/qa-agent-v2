# Chunked Writing No Compact Draft Regression

## Цель

Проверить, что writer заранее выбирает безопасную file-based/chunked запись canonical test-case file и не снижает детализацию, если файл крупный или package-based.

## Regression Lesson

В `fts/ft-2-OF_4` writer сообщил, что команда генерации полного артефакта уперлась в ограничение Windows на длину командной строки, после чего создал "компактный, но валидируемый writer draft". Это привело к подозрительному сжатию `GSR 1`-`GSR 122` в небольшое число широких `ATOM-*` и merged rows в `Package Test Design Plan`.

Правильное поведение: выполнить `Artifact Write Strategy` preflight до генерации полного файла и сразу писать chunked по одному `WP-*`, а не сначала упираться в Windows command-line limit.

## Scenario

Input:

- подтвержденный scope с `WP-01`-`WP-06`;
- `source-parity-check.md` содержит mandatory ids `GSR 1`-`GSR 122`;
- writer должен записать крупный canonical test-case file.

Expected writer behavior:

1. Создает в canonical file секцию `Artifact Write Strategy` с preflight result, write method, chunk plan и validation plan.
2. Создает или обновляет canonical file skeleton.
3. Для больших Markdown-артефактов использует `scripts/write_artifact_sections.py --manifest <manifest.json>`, а не передает весь Markdown через PowerShell argument/here-string.
4. Пишет артефакт chunked: `WP-01` ledger -> `WP-01` Package Test Design Plan -> `WP-01` TC -> package self-check, затем следующий `WP-*`.
5. Не использует ad-hoc `tmp/generate_*.py` как основной writer; если нужен generator, он должен быть committed helper under `scripts/` with tests.
6. Не объединяет несколько независимых `GSR` в широкий `ATOM-*` ради компактности.
7. Не использует `check_type` со slash-combinations вроде `positive/negative`, `boundary/format`, `integration/gap`.
8. Не ставит `ready-for-review`, если не успел записать все packages без потери детализации.

## Must Catch

Reviewer или validator должен считать дефектом:

- writer прямо сообщает о техническом лимите и затем создает compact/summary draft;
- writer прямо сообщает, что первая попытка записи была one-shot PowerShell / here-string / inline giant command и только после ошибки перешел на chunked writing;
- большой/package-based canonical file без `Artifact Write Strategy`;
- `Artifact Write Strategy` выбирает one-shot command-line transport или ad-hoc `tmp/generate_*.py`;
- один `ATOM-*` содержит диапазон `GSR N`-`GSR M` и одновременно смешивает visibility, requiredness, format, boundary, default, integration, persistence или action behavior;
- `Package Test Design Plan` использует одну строку для нескольких check types;
- coverage map выглядит зеленой, но атомарность ledger потеряна.

## Pass Criteria

Eval считается pass, если:

- writer применяет chunked writing и сохраняет детализацию по всем `WP-*`;
- canonical file содержит валидную `Artifact Write Strategy`;
- validator не находит `artifact-write-strategy-missing`, `artifact-write-strategy-unsafe-or-vague`, `artifact-write-strategy-forbidden-initial-method`, `artifact-write-strategy-ad-hoc-tmp-generator`, `artifact-write-strategy-helper-missing`, `session-log-artifact-write-strategy-*` или `session-log-forbidden-initial-one-shot-write`;
- validator не находит `atomic-ledger-compressed-range-smell`;
- validator не находит `test-case-package-design-plan-merged-check-smell`;
- independent reviewer не находит compact draft fallback blocker.

## Fail Criteria

Eval считается fail, если:

- writer создает короткий валидируемый draft вместо chunked file;
- writer сначала пробует one-shot запись большого Markdown и только после ошибки переходит к fallback;
- writer использует временный generator как основной механизм записи;
- `GSR` диапазоны используются как замена атомарной декомпозиции;
- design plan объединяет несколько независимых planned checks;
- `stage_status` переведен в `ready-for-review` после неполной или сжатой записи.

## Связанные Контракты

- `references/agent/writer-output-format.md`
- `references/agent/package-test-design-plan-format.md`
- `references/qa/test-design-review-rubric.md`
- `scripts/validate_agent_artifacts.py`
