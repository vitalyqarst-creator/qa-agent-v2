# Personal Data V8 Reviewer Contract Remediation

## Цель этапа

Устранить V7 reviewer-contract blocker в новом immutable H45/V8: schema-level совместимость verdict, structured dictionary evidence, package-id consistency/migration и source-backed bounded repair без изменения FT-first baseline.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/live-result.v7.json`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/prepared-input/application-card-client-personal-data-v7/stage-package.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/reviewer-r1/attempt-001/runner-output/stdout.txt`
- `fts/AutoFin/work/stage-handoffs/45-personal-data-v8-reviewer-contract/workflow-state.yaml`

## Обязательные действия

1. Keep V7 immutable and implement status-bound generic reviewer schema with mixed-status regression.
2. Add structured dictionary evidence projection and prove `DICT-001` active values reach reviewer context.
3. Add deterministic package-id gate and runner-owned metadata migration with semantic-preservation proof.
4. Source-verify V7 diagnostics, exclude unsupported `F-002`, and build a bounded V8 repair plan only from confirmed TC defects.
5. Compile/validate immutable V8, run focused regression, artifact validation and verified exec dry-run.
6. Commit/push pre-live checkpoint, record separate authorization, then allow exactly one dispatcher.
7. Stop without retry/resume/fallback on any live blocker and record terminal evidence.

## Ограничения

- Не использовать V6/V7 generated drafts или rejected reviewer output как requirement source.
- Не изменять `fts/AutoFin/test-cases/14-application-card-client-personal-data.md`.
- Не создавать production shadow до reviewer sign-off и отдельного promotion decision.
- Не использовать стенд или runtime DaData для FT-first writing.
- Не трогать пользовательские untracked diagnostics и соседний addresses/contacts scope.

## Ожидаемый результат

Либо reviewer-accepted V8 unsigned draft без automatic promotion, либо точный новый terminal blocker. Во всех случаях baseline неизменён и V7 не возобновляется.

## Gate завершения

До live обязательны чистые schema/dictionary/metadata regressions, bounded repair validate-only, artifact validator, checkpoint/push и отдельная authorization. После авторизации любой blocker терминален без повтора.
