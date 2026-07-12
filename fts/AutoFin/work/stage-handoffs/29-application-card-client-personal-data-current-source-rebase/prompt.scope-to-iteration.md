# Handoff Prompt

## Цель этапа

Запустить новый current-source writer/reviewer loop для personal-data scope в режиме `rebuild-from-scope` с безопасным delta reuse historical 15-case candidate baseline.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/workflow-state.yaml`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/mockup-visual-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-gap-review.md`
- `test-cases/14-application-card-client-personal-data.md`
- `AGENT-NOTES.md`

## Обязательные действия

- Работать package-by-package: `WP-01`, затем `WP-02`; каждому `ATOM-*` и `TC-*` назначить `package_id`.
- Для каждого package выполнить ledger, Package Test Design Plan и TC self-check gates.
- Сначала построить current XHTML-based Source Row Completeness Matrix и Source Table Normalization, затем atomic ledger.
- Использовать `scripts/write_artifact_sections.py --manifest`; не писать large artifacts one-shot.
- Сохранить все `BSR 47–77`; старые `BSR 39–69` mappings запрещены.
- Historical 15 cases сравнить с новым ledger: reuse/rewrite/delete/add только с явным delta rationale.
- Каждый `SO-NEG-*` и `SO-REQ-*` отобразить в отдельный candidate TC с UI-calibration statuses.
- Не утверждать DaData/ABS backend effect без observable artifact.

## Не делать

- Не расширять scope до распознавания документов или паспорта.
- Не принимать исторический sign-off как текущий verdict.
- Не придумывать exact validation messages/reactions.
- Не объединять valid/invalid или разные main expected results.

## Ожидаемые выходы

- Обновлённый canonical file и полный split test-design package.
- Отдельные writer/reviewer sessions, matrices, findings, snapshots и session/decision logs.
- Terminal `signed-off`, `round-cap-reached` или реальный `blocked-input`.

## Gate завершения

Current FT4 rows и `BSR 47–77` полностью трассируются, candidates сохранены, reviewer подтвердил semantic/format closure, validator scoped profile чист.
