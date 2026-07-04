# Writer Cross-Artifact Sync And Format Regression

## Цель

Проверить, что writer не может передать набор на reviewer, если canonical TC и split test-design artifacts формально существуют, но текущий scope содержит структурные дубли или рассинхронизацию ссылок между артефактами.

Этот eval фиксирует урок из `fts/ft-2-OF_16` / `ui-employment-canary-v7-waiver-gate-regression`: writer-r1 сгенерировал canonical TC со смешанной схемой полей, а writer-r2 мог заявить исправление, не синхронизировав все current-scope ссылки в ledger, matrix, TDDT, plan и canonical TC. Финальный результат дошел до `round-cap-reached`, а reviewer оставил блокеры `FINDING-006` и `FINDING-007` по cross-artifact traceability link inconsistencies.

## Входной Сценарий

- FT package: `fts/ft-2-OF_16`.
- Cycle: `ui-employment-canary-v7-waiver-gate-regression`.
- Current scope artifacts:
  - `test-cases/2-1-1-1-1-2-ui-employment-canary-v7-waiver-gate-regression.md`;
  - `work/test-design/2-1-1-1-1-2-ui-employment-canary-v7-waiver-gate-regression/`;
  - `work/review-cycles/ui-employment-canary-v7-waiver-gate-regression/outputs/`.

## Must-Catch Rules

Validator или runner lifecycle gate должен блокировать writer-ready handoff, если в current scope есть хотя бы один из сигналов:

- один `TC-*` одновременно использует metadata table `| Поле | Значение |` и bold metadata fields `**Название:**`, `**Тип:**`, `**Приоритет:**`, `**Трассировка:**`, `**package_id:**`;
- один `TC-*` одновременно использует runtime heading `### Тестовые данные`, `### Шаги`, `### Итоговый ожидаемый результат` и дублирующее inline/bold поле `**Тестовые данные:**`, `**Шаги:**`, `**Итоговый ожидаемый результат:**`;
- writer response утверждает `fixed`, но canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan или coverage artifacts всё еще ссылаются на разные `TC-*` / `ATOM-*` / `GAP-*` для одной current-scope обязанности;
- current-scope validator warning/error находится в canonical TC, active test-design dir или cycle outputs, но writer переводит состояние в `writer-draft-ready` или `semantic-review-ready`;
- reviewer ставит `validator_checked: yes` / `blocking_findings_absent: yes`, не разобрав current-scope validator warning/error как blocking, valid false-positive, valid source gap или accepted nonblocking risk.

## Exclusions

Gate не должен блокировать writer-ready или terminal sign-off из-за:

- historical snapshots under `versions/`;
- scratch artifacts under `_artifact_write/`;
- unrelated scopes in neighboring `work/test-design/*` or `test-cases/*`;
- `info` findings without warning/error severity.

## Pass Criteria

Eval считается успешным, если:

- mixed-schema duplicate TC получает `test-case-mixed-schema-duplicate-fields`;
- duplicated runtime field получает `test-case-runtime-field-duplicated`;
- `scripts/codex_review_cycle_runner.py validate` rejects `writer-draft-ready` / `semantic-review-ready` when these current-scope findings are present;
- targeted tests include:
  - `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_mixed_test_case_schema_duplicates_warn`;
  - `tests.test_codex_review_cycle_runner.CodexReviewCycleRunnerTests.test_writer_ready_gate_rejects_current_scope_blocking_validator_warning`;
- `instruction-contract-index.md` links this eval from the Writer Quality Gate or Reviewer Output contract row.

## Fail Criteria

Eval провален, если:

- mixed schema TC проходит validator без warning;
- writer-ready handoff остается валидным при current-scope blocking validator finding;
- reviewer terminal `signed-off` проходит с unwaived current-scope warning/error;
- writer может закрыть cross-artifact sync finding только текстом `fixed`, не обновив affected artifacts.

## Regression Lesson

Проблема v7 была не в размере scope и не в том, что writer сделал один плохой TC. Системная проблема была в отсутствии lifecycle stop: дефект был виден в артефактах, но процесс позволял двигаться дальше. Поэтому правило должно жить одновременно в validator, runner gate и eval, а не только в prompt-инструкции.
