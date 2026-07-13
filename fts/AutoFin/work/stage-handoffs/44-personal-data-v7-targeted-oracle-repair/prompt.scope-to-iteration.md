# Personal Data V7 Targeted Oracle Repair

## Цель этапа

Завершить `ft-test-case-iteration` для `application-card-client-personal-data`: точечно исправить четыре V6 oracle-quality findings в новом immutable V7 без повторной генерации остальных TC и без изменения FT-first baseline.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/43-personal-data-v6-output-capacity/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v6-20260713/attempts/writer-r1/attempt-001/runner-output/quality-gate-bundle.json`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/pre-live-stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/targeted-repair-preflight.v7.json`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/dispatcher-config.v7.json`

## Обязательные действия

1. Проверить checkpoint/push, hashes V6 repair inputs, V7 package digest, oracle preflight, target set и отсутствие attempts.
2. Разрешить ровно один dispatcher с verified `exec`, без SDK fallback.
3. В writer вернуть только `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028`, `TC-ACPD-034`; runner должен доказать byte-preservation остальных 43 секций.
4. Запустить один fresh full-set reviewer только после всех deterministic gates.
5. Зафиксировать terminal result, hashes, sessions, performance и production boundaries.

## Ограничения

- Не retry/resume V6 или V7; не менять transport после blocker.
- Не использовать V6 draft как requirement evidence: это только hash-bound unsigned repair input.
- Не изменять `fts/AutoFin/test-cases/14-application-card-client-personal-data.md`.
- Не продвигать и не перезаписывать production shadow без отдельного promotion decision.
- Не использовать стенд, runtime DaData, V1–V5 drafts или соседние scopes как requirement evidence.
- Не трогать пользовательские untracked diagnostics и `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`.

## Ожидаемый результ

Либо `accepted-not-promoted` с одним repaired unsigned draft и reviewer `accepted`, либо точный новый terminal blocker. В обоих случаях FT-first baseline неизменён, promotion не выполняется автоматически.

## Gate завершения

Любой process, contract, repair, splice, full-set gate, reviewer или production-boundary blocker сразу завершает итерацию без повтора.
