# Personal Data V8 Reviewer Contract Remediation

## Цель этапа

Продолжить `ft-test-case-iteration` для `application-card-client-personal-data` из H44 terminal state: устранить reviewer-contract, metadata и dictionary-evidence пробелы в новом immutable H45/V8 без изменения FT-first baseline.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/live-result.v7.json`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/cycle-state.yaml`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/writer-r1/attempt-001/runner-output/repair-splice.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/attempts/reviewer-r1/attempt-001/runner-output/stdout.txt`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/prepared-input/application-card-client-personal-data-v7/stage-package.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/prepared-input/application-card-client-personal-data-v7/atomic-obligations.json`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v7-20260713/prepared-input/application-card-client-personal-data-v7/source-evidence.md`

## Обязательные действия

1. Не повторять и не возобновлять V7; создать новый immutable H45/V8 boundary.
2. Ограничить generic reviewer schema status-specific verdict-ами. Пакет только с testable obligations должен schema-level принимать только `covered`, `missing`, `incorrect`; parser check сохранить как defense in depth.
3. Добавить regression для смешанного testable/gap пакета и для V7 failure `OBL-025 -> invented-coverage` до live.
4. Добавить deterministic package-id consistency gate и runner-owned metadata migration с отдельным proof неизменности test semantics.
5. Передавать dictionary values в явной structured reviewer projection. Regression должен доказывать, что `Мужчина` и `Женщина` из `DICT-001` не объявляются отсутствующими evidence.
6. Source-backed проверкой подтвердить или отклонить диагностические `F-001/F-003/F-004/F-005`; `F-002` не считать подтверждённым. Сформировать bounded hash-bound repair plan только из подтверждённых TC.
7. Выполнить focused tests, validate-only, production-boundary checks, artifact validator и exec dry-run.
8. До checkpoint/push live запрещён. После отдельной авторизации допускается ровно один V8 dispatcher; любой live blocker терминален.

## Ограничения

- Не retry/resume V7 и не менять transport после blocker.
- Не использовать V6/V7 draft или отклонённый reviewer output как requirement evidence; это только immutable generated diagnostic/repair input.
- Не изменять `fts/AutoFin/test-cases/14-application-card-client-personal-data.md`.
- Не продвигать и не перезаписывать production shadow без отдельного promotion decision.
- Не использовать стенд, runtime DaData, прежние drafts или соседние scopes как requirement evidence.
- Не трогать пользовательские untracked diagnostics и `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`.

## Ожидаемый результат

До live: проверенный H45/V8 package, schema/evidence/metadata regressions, bounded repair plan и отдельный authorization checkpoint. После единственного разрешённого live: либо reviewer-accepted unsigned draft без автоматического promotion, либо точный terminal blocker. FT-first baseline во всех случаях неизменён.

## Gate завершения

V8 не допускается к live, пока schema-level verdict restriction, metadata consistency/migration, dictionary projection и source-backed repair preflight не прошли regression. После авторизации любой process, contract, repair, splice, full-set gate, reviewer или production-boundary blocker сразу завершает итерацию без повтора.
