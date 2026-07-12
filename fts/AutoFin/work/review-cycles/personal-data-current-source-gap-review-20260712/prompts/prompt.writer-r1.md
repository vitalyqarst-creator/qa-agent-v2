# Writer current-source rebase

Scope gap review passed. Выполни writer-r1 в режиме `rebuild-from-scope` с delta reuse historical candidate baseline.

## Входные артефакты

- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/prompt.scope-to-iteration.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md`
- `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/scope-gap-review-findings.md`
- `test-cases/14-application-card-client-personal-data.md`

## Обязательные действия

- Следуй полному contract в `prompt.scope-to-iteration.md`.
- Перестрой design artifacts по FT4 XHTML rows и `BSR 47–77`; historical cases — только delta baseline.
- Материализуй все `SO-NEG-*` и `SO-REQ-*` как отдельные calibration candidate TC.
- Работай последовательно `WP-01`, затем `WP-02` и используй artifact manifest writing.

## Не делать

- Не использовать `AutoFinPreFinal.*` и historical BSR mappings как requirement evidence.
- Не придумывать exact validation/integration oracle.

## Ожидаемые выходы

- Current-source canonical draft, complete split design artifacts, writer self-check и reviewer handoff.

## Gate завершения

Все 11 source rows, `BSR 47–77`, 42 planned atoms и 20 calibration obligations имеют проверяемую трассировку.
