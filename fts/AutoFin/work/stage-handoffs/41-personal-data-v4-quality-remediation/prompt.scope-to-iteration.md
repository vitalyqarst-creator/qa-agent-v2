# Следующий этап: регистрация fixtures и Personal Data V5

## Цель этапа

Продолжить `ft-test-case-iteration` для scope `application-card-client-personal-data`: закрыть `blocked-input` V4r1 безопасными стендовыми данными, добавить детерминированное разрешение fixture catalog до live и подтвердить результат в одном новом immutable V5 cycle без изменения FT-first baseline.

На отдельном ПК начать с актуальной удалённой ветки `audit/application-card-personal-data-iteration`, затем создать от неё отдельную ветку `audit/application-card-personal-data-v5-fixture-resolution`. Не переносить незакоммиченные локальные файлы с другого ПК.

## Входные артефакты

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/41-personal-data-v4-quality-remediation/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/41-personal-data-v4-quality-remediation/blocker-outcome-analysis.md`
- `fts/AutoFin/work/stage-handoffs/41-personal-data-v4-quality-remediation/fixture-registration-request.md`
- `fts/AutoFin/work/stage-handoffs/41-personal-data-v4-quality-remediation/stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/41-personal-data-v4-quality-remediation/compiler-inputs/application-card-client-personal-data/`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v4r1-20260713/cycle-state.yaml`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v4r1-20260713/attempts/writer-r1/attempt-001/runner-output/writer-result.json`
- `evals/candidates/2026-07-13-unresolved-fixture-id-prepared-package.md`
- `references/agent/fixture-catalog-format.md`

## Обязательные действия

1. Создать handoff `42-personal-data-fixture-registration` и persistent decision/session logs.
2. На тестовом стенде зарегистрировать `FIX-ACPD-SAVE-001` и `FIX-ACPD-DADATA-001` строго по `fixture-registration-request.md`.
3. Использовать только синтетические или официально разрешённые тестовые данные. Перед публикацией проверить отсутствие PII, cookie, token, session storage и реальных клиентских идентификаторов.
4. Создать канонический `fixture-catalog.md` по `references/agent/fixture-catalog-format.md`; каждый fixture должен раскрывать `setup_state`, `concrete_data`, `dependencies`, `cleanup` и linked TC.
5. Добавить в prepared compiler обязательное разрешение всех `fixture_id` в catalog. Отклонять до package write:
   - отсутствующий catalog или fixture;
   - generic/conditional `concrete_data`;
   - save/integration fixture без dependency/cleanup;
   - TC/fixture link mismatch.
6. Добавить bad/corrected eval для `unresolved-fixture-id` и focused tests. Подтвердить, что H41 inputs без catalog блокируются локально до live.
7. Скопировать H41 inputs в новый immutable H42/V5 snapshot, добавить catalog и менять только новый snapshot.
8. Собрать `application-card-client-personal-data-v5` с 42 atoms, 65 obligations, 47 уникальными seed `TC-ACPD-001..047`, `GAP-001..003`, `DICT-001` и matching manifest hashes.
9. Выполнить полный compiler/runner regression, scoped artifact validation, seed/hash/context preflight и dispatcher dry-run без SDK fallback.
10. Создать checkpoint commit. После него разрешён ровно один V5 live dispatcher. При любом новом blocker остановиться без retry.

## Не делать

- Не запускать, не возобновлять и не изменять V4 или V4r1.
- Не создавать draft вручную из V4r1 и не копировать старый signed-off catalog как доказательство актуальности стенда.
- Не использовать реальные клиентские данные и не коммитить restricted evidence или session-секреты.
- Не превращать отсутствие fixture в выдуманный expected result, UI-текст или механизм сохранения.
- Не менять `fts/AutoFin/test-cases/14-prepared-shadow-application-card-client-personal-data.md`; до reviewer sign-off файл должен отсутствовать.
- Не изменять пользовательские `evals/sdk-turn-diagnostics/**` и `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`.
- Не запускать reviewer, если writer не создал полный draft и не прошёл все deterministic gates.

## Ожидаемые выходы

- `fts/AutoFin/work/stage-handoffs/42-personal-data-fixture-registration/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-fixture-registration/agent-decision-log.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-fixture-registration/iteration-session-log.md`
- `fts/AutoFin/work/stage-handoffs/42-personal-data-fixture-registration/fixture-catalog.md`
- sanitized fixture-registration evidence/index без PII и секретов либо явный `blocked-input`
- bad/corrected fixture-resolution eval и regression tests
- новый immutable V5 package/cycle и performance evidence
- reviewer findings/sign-off только если writer и все pre-review gates прошли
- checkpoint-коммиты и push отдельной ветки

## Gate завершения

Этап успешен только если обе fixtures воспроизводимы по опубликованному безопасному catalog, unresolved/generic fixture детерминированно блокируется до live, V5 проходит все preflight gates, единственный live writer создаёт полный исполнимый draft, reviewer возвращает zero blocking findings/`accepted`, terminal state равен `accepted-not-promoted`, production shadow отсутствует, а V1–V4r1 и FT-first baseline неизменны.

Если безопасные конкретные данные получить нельзя, корректный итог — `blocked-input` с точным перечнем недостающих значений; live V5 в таком случае не запускать.
