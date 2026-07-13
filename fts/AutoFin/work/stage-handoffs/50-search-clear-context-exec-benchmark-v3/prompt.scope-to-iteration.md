# Search Clear Context V4 Runtime Contract Remediation

## Цель Этапа

В новой immutable V4 iteration устранить рассинхрон package v6 и embedded writer runtime contract, доказать это deterministic tests и только после новой checkpoint/authorization boundary выполнить один fresh exec writer/reviewer run.

## Входные Артефакты

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/live-result.v2.json`
- `fts/AutoFin/work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/live-result.v3.json`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/live-blocker-analysis.md`
- `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/performance-analysis.v3.md`
- `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v3-20260713/attempts/writer-r1/attempt-001/prompt.md`
- `references/agent/prepared-writer-runtime-profile.md`
- `scripts/codex_exec_review_cycle_runner.py`

## Обязательные Действия

1. Сделать canonical `PACKAGE_VERSION` единственным numeric source для runtime eligibility; убрать hard-coded version `5` из writer profile.
2. Централизовать common package metadata projection, чтобы writer/reviewer payload не собирали дублирующиеся dict независимо.
3. Включить exact `package_digest` в embedded writer и reviewer metadata. Runner должен ранее проверить digest при загрузке package; fresh agent не должен пересчитывать его по неполному prompt.
4. Уточнить eligibility профиля: требовать runner-validated current package metadata и non-empty SHA-256 digest, не дублировать версию текстом.
5. Добавить cross-contract regressions:
   - generated writer payload содержит current `package_version` и exact `package_digest`;
   - generated reviewer payload содержит те же identity fields;
   - stale numeric allowlist в runtime profile выявляется до live;
   - invalid/missing digest не доходит до exec attempt.
6. Сохранить V3 state-change regressions и повторить полные целевые suites.
7. Скомпилировать новый immutable V4 package/cycle; V3 package и attempt не изменять.
8. Validate-only должен подтвердить v6 identity/digest, state-change `4/4`, oracle `4/4`, context/output capacities и отсутствие attempts.
9. После чистого checkpoint push создать отдельную authorization и выполнить ровно один V4 dispatcher invocation.
10. Зафиксировать writer/reviewer verdict, session isolation, latency/tokens, baseline hashes и terminal status без promotion.

## Не Делать

- Не retry/resume/rebind V3 и не редактировать его immutable attempt.
- Не понижать новый package до v5 ради совместимости.
- Не использовать V2 draft как requirement evidence и не обходить eligibility через prompt-only уговоры.
- Не запускать SDK fallback, assisted mode, second dispatcher или promotion.
- Не изменять FT-first baseline и production test cases.

## Gate Завершения

Этап завершён, когда stale v5 profile/missing digest больше не могут пройти pre-live, V4 package проходит все deterministic gates, один authorised dispatcher завершён без retry/fallback, reviewer verdict зафиксирован, а protected baselines и promotion target не изменены.
