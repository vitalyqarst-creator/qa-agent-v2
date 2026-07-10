# Сквозной архитектурный аудит prepared test-case pipeline

## Scope

Проверен путь `source evidence → prepared obligations → writer → deterministic gates → reviewer → promotion` для оптимизированного `simple-field-property` режима. Baseline helper проверил `59` agent-layer checks: findings `0`, stale items `0`. Ручной follow-up ограничен семантическими и trust-boundary инвариантами, которые helper не способен доказать по структуре файлов.

## Findings

### ARCH-PREP-001 — error / P0 — blocking gaps могли пройти до accepted/promotion

- Категория: `scripts`.
- Evidence: `PreparedGap.blocking` сохранялся в package, но fast-path eligibility и structured reviewer acceptance не учитывали этот флаг; `gap-preserved` считался terminal pass для любого gap.
- Риск: пакет с нерешённым blocking gap мог получить `accepted` и затем `signed-off`.
- Recommended move: не допускать package с blocking gaps в fast path.
- Remediation: исправлено в package version `3`; builder отклоняет `simple-field-property` package до запуска writer.
- Paths: `test_case_agent/review_cycle/prepared_package.py`, `tests/test_prepared_stage_package.py`.

### ARCH-PREP-002 — error / P0 — fast path не требовал обязательную пару DOCX/XHTML

- Категория: `scripts`.
- Evidence: source registry проверял только непустоту и hashes; пакет мог содержать единственный произвольный source role.
- Риск: writer/reviewer могли получить compact evidence без обязательного authoritative DOCX или machine-readable XHTML.
- Recommended move: проверять роли и расширения в immutable package contract.
- Remediation: version `3` требует `.docx` с role `source-of-truth` и `.xhtml`/`.html` с role `machine-readable`.
- Paths: `test_case_agent/review_cycle/prepared_package.py`, `tests/test_prepared_stage_package.py`.

### ARCH-PREP-003 — error / P1 — dictionary claim мог стать testable без dictionary inventory

- Категория: `scripts`.
- Evidence: `dictionary_refs` был необязательным и не входил в проверку evidence refs. Именно это позволило `ATOM-PREP-001/002` объединить происхождение значений из справочника с кратностью выбора, хотя draft проверял только кратность.
- Риск: nominal traceability завышает фактическое покрытие.
- Recommended move: testable dictionary/reference-list claim должен ссылаться на точный `DICT-*`; иначе claim сохраняется отдельным gap.
- Remediation: version `3` отклоняет dictionary-backed testable obligation без `dictionary_refs` и проверяет наличие exact `DICT-*` в selected evidence.
- Paths: `test_case_agent/review_cycle/prepared_package.py`, `references/agent/prepared-stage-package-format.md`.

### ARCH-PREP-004 — error / P1 — source/evidence refs проверялись подстрокой

- Категория: `scripts`.
- Evidence: `SRC-1` считался найденным внутри `SRC-10`; selector использовал такое же substring matching.
- Риск: obligation мог быть ошибочно привязан к другой строке evidence.
- Recommended move: stable refs проверять token-exact boundaries.
- Remediation: добавлены exact reference matching для validation и selectors.
- Paths: `test_case_agent/review_cycle/prepared_package.py`, `tests/test_prepared_stage_package.py`.

### ARCH-PREP-005 — warning / P1 — orphan gaps не попадали в reviewer obligation set

- Категория: `scripts`.
- Evidence: `coverage_gaps` мог содержать `GAP-*`, на который не ссылался ни один obligation; reviewer проверяет obligations, а не отдельный полный gap set.
- Риск: gap сохранялся в package digest, но выпадал из semantic verdict.
- Recommended move: каждый declared gap должен быть связан хотя бы с одним obligation.
- Remediation: version `3` отклоняет orphan gaps.
- Paths: `test_case_agent/review_cycle/prepared_package.py`, `tests/test_prepared_stage_package.py`.

### ARCH-PREP-006 — warning / P1 — runtime documentation drift

- Категория: `references`.
- Evidence: prepared package format всё ещё указывал reviewer hard timeout `120 s`, idle `45 s` и package version `2`, хотя live runner использует hard deadline `90 s` без короткого idle cutoff.
- Риск: новый запуск мог быть настроен по устаревшему canonical reference.
- Recommended move: синхронизировать package version и budgets в одном canonical reference/index.
- Remediation: references и instruction contract index обновлены для version `3`.
- Paths: `references/agent/prepared-stage-package-format.md`, `references/agent/review-cycle-stage-contract-v2.md`, `references/agent/instruction-contract-index.md`.

### ARCH-PREP-007 — warning / P2 residual — общая semantic atomarity остаётся reviewer-driven

- Категория: `skill-content`.
- Evidence: глобальный contract уже требует split независимых pass/fail claims, но произвольную составную фразу без dictionary markers нельзя надёжно классифицировать deterministic parser-ом. Исторический scope handoff назвал три составные source rows тремя atomic statements.
- Риск: новый тип составного claim может пройти syntax gates и быть обнаружен только post-writer reviewer.
- Recommended move: до production rollout добавить независимый obligation-design attestation, связанный с obligation digest, либо обязательный source-property/TDDT artifact для fast-path package preparation. Не заменять это набором языковых heuristics по союзам `и/and`.
- Remediation: не включено в P0/P1 patch; version `3` закрывает доказанные deterministic failure classes, а semantic reviewer остаётся обязательным terminal gate.
- Paths: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`, `references/qa/test-design-review-rubric.md`.

### ARCH-PREP-008 — error / P0 live blocker — prompt требует replace отсутствующего output

- Категория: `scripts`.
- Evidence: benchmark cycle 1 сохранил `apply_patch verification failed` для отсутствующего `stage-output/draft.md`; runner создаёт seed только в `runner-input/draft-seed.md`, а profile/prompt говорит replace seed at output path.
- Риск: корректно запущенный writer может выбрать update вместо create, потерять почти весь first-artifact budget и быть остановлен до первого draft.
- Recommended move: явно закрепить, что output изначально отсутствует и должен создаваться первым `Add File`/atomic write; seed остаётся отдельным immutable template. Не создавать runner-owned output-заглушку.
- Remediation: исправлено в следующей узкой итерации. Runtime profile и generated prompt теперь явно фиксируют absent initial output, stage ownership и обязательный первый `Add File`/atomic create; regression проверяет, что seed существует отдельно, а output отсутствует до входа writer executor.
- Paths: `references/agent/prepared-writer-runtime-profile.md`, `scripts/codex_exec_review_cycle_runner.py`, `fts/AutoFin/work/review-cycles/codex-exec-prepared-architecture-benchmark-01-20260710/benchmark-blocker-report.md`.

### ARCH-PREP-009 — warning / P1 live blocker — first-artifact SLO пересекается с нормальным latency tail

- Категория: `scripts`.
- Evidence: после исправления create contract canary создал draft на `51.844 s`, benchmark 1 — на `79.015 s`, а benchmark 2 был остановлен на `90.079 s` без update/file-state ошибки. Writer успел выполнить probe и объявить следующий `Add File`, но draft ещё формировался.
- Риск: корректный run блокируется как input/process failure из-за малого запаса между наблюдаемым верхним latency tail и абсолютным deadline `90 s`.
- Recommended move: отдельным bounded experiment увеличить first-artifact deadline до `120 s`, сохранив hard timeout `180 s`, post-write idle `60 s` и stage ownership.
- Remediation: отложено по live stop-condition; benchmark 3 не запускался.
- Paths: `scripts/codex_exec_review_cycle_runner.py`, `evals/prepared-create-benchmark/20260710/benchmark-report.md`.

## Duplication map

- Confirmed duplicates: отсутствуют.
- Possible duplicates baseline helper оставлены без изменений: они относятся к обязательным коротким reminders в нескольких phase skills и не связаны с prepared-pipeline blocker.

## Stale items

- Устаревшие package v1/v2 artifacts не переписываются и остаются читаемым immutable evidence.
- Fast-path eligibility перенесена на version `3`; старые package версии не должны повторно запускаться как новые prepared cycles.

## Remediation plan

1. Create-vs-update remediation и regression завершены; immutable canary принят с promotion off.
2. Перезапущенный benchmark дал один accepted run и один `blocked-first-artifact-deadline`; третий run отменён по stop-condition.
3. Следующей узкой итерацией проверить deadline `120 s` при неизменных hard timeout `180 s` и post-write idle `60 s`.
4. После успешного canary заново выполнить три независимых benchmark cycles.
5. Сохранить residual P2 как отдельную архитектурную задачу после стабильного benchmark.
