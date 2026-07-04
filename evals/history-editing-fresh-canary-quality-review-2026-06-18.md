# Fresh canary quality review: section-40 history editing

Дата: 2026-06-18

## Объект проверки

- FT: `fts/ft-2-OF_17`
- Scope: `section-40`, форма "История редактирования анкеты"
- Review cycle: `fts/ft-2-OF_17/work/review-cycles/history-editing-fresh-canary/`
- Canonical test cases: `fts/ft-2-OF_17/test-cases/section-40-history-editing-fresh-canary.md`
- Split test design: `fts/ft-2-OF_17/work/test-design/section-40-history-editing-fresh-canary/`
- Runner command: `.venv\Scripts\python.exe scripts\codex_review_cycle_runner.py run-until-terminal --state fts\ft-2-OF_17\work\review-cycles\history-editing-fresh-canary\cycle-state.yaml --session-timeout-seconds 1800`

## Итоговый вердикт

Fresh canary полезен: writer создал связный набор тест-кейсов и полный комплект split-артефактов, но результат нельзя считать готовым к полноценному массовому написанию тест-кейсов без исправлений в gate/runner workflow.

Основная проблема не в покрытии требований, а в надежности автоматического перехода между стадиями: writer успел создать артефакты, но сессия превысила `1800s`, cycle остался в `blocked-input`, а `Writer Quality Gate` заявил `pass` по несуществующему future-profile.

## Метрики результата

- `TC`: 8 (`TC-HEFC-001`..`TC-HEFC-008`)
- Покрытые атомы: 12 (`ATOM-001`..`ATOM-012`)
- Явные gaps: 1 (`GAP-001`, accepted non-blocking PDF extraction/parity risk)
- Canonical test-case artifact: 19,699 bytes
- Split artifacts: 20 файлов в `work/test-design/section-40-history-editing-fresh-canary/`

## Что стало лучше

1. Writer не смешал новый canary со старым signed-off набором `history-editing-canary`.
2. Scope удержан в границах `section-40`; PDF-only IDs не придуманы.
3. Требования разложены на `SRC-*` и `ATOM-*`; нет компрессии "один раздел = один тест".
4. Основные проверки атомарные: row creation, unified list, default sorting, row count, add/delete old-new cells, close action, table columns.
5. `GAP-001` не скрывает исполнимую UI-проверку, а вынесен как traceability/source extraction risk.

## Блокирующие проблемы

### 1. Runner timeout оставляет цикл в `blocked-input`

`writer-r1-completion.yaml`:

- `turn_status: timeout`
- `session_status: failed`
- `state_advanced: true`
- `stage_status_after: blocked-input`
- `duration_ms: 1856000`

При этом writer фактически создал canonical test cases, split artifacts, response, session log и validator profile. Текущая модель timeout recovery не дает безопасно продолжить цепочку и требует ручной диагностики.

Рекомендация: до массового writing либо увеличить timeout для writer-stage выше фактических 1856 секунд, либо сделать отдельный post-timeout recovery режим, который не продвигает стадию без чистого scoped-validator profile, но явно классифицирует состояние как `timeout-with-artifacts`.

### 2. Writer Quality Gate ссылается на несуществующий future-profile

Validator после устранения ложного `Source Row Inventory` warning оставляет один warning:

```text
writer-quality-gate-scoped-validator-profile-invalid
row-26: profile path not found: outputs/scoped-validator-profile.structure-preflight-r1.json
```

Проблема в строке `scoped-validator-findings` файла `writer-quality-gate.md`: writer пометил gate как `pass`, но сослался на будущий `structure-preflight-r1` profile вместо фактического `outputs/scoped-validator-profile.writer-r1.json`.

Рекомендация: writer-stage не должен ставить `pass` по validator gate, если нет существующего profile текущей стадии с `unresolved_warning_error_count=0`. Ссылка на будущую стадию должна быть блокирующим дефектом, а не `pass`.

### 3. Writer session log противоречит фактическому validator profile

Writer log утверждает, что warnings были remediated before state advancement. Фактический `scoped-validator-profile.writer-r1.json` содержал 2 unresolved warnings до parser-fix и 1 реальный warning после parser-fix.

Рекомендация: запретить writer-у формулировку "validator-clean" без машинно проверенного profile текущей стадии.

## Неблокирующие проблемы качества

### 1. Split artifacts имеют дублирующие заголовки

Например `source-row-inventory.md` начинается с:

```markdown
# Source Row Inventory

## Source Row Inventory
```

Это не потеря данных, но формат грязный. Validator был доработан, чтобы не выдавать ложный warning при таком wrapper-е, но writer должен генерировать один канонический heading.

### 2. Passability пока зависит от подготовленных fixture-данных

Тест-кейсы понятны и ручно исполнимы при наличии подготовленной карточки УЗ, но не полностью самодостаточны:

- используются fixture-примеры вроде `Фамилия`, `Барисов -> Борисов`, `Значение 1 -> Значение 2`;
- preconditions требуют уже сохраненных событий редактирования через штатный flow;
- нет ссылки на конкретный reusable fixture catalog или setup procedure.

Это допустимо для FT-first baseline, но перед `automation-ready` нужен отдельный UI/data-prep этап.

## Исправление validator, выполненное во время проверки

Был найден ложный warning `source-row-inventory-misses-normalized-source-row`: таблица Source Row Inventory была в split-файле, но parser выбирал пустую секцию из-за соседних заголовков `# Source Row Inventory` и `## Source Row Inventory`.

Внесено исправление в `scripts/validate_agent_artifacts.py`: validator схлопывает соседние одноименные `#`/`##` headings перед извлечением split-секции. Добавлен регрессионный тест в `tests/test_agent_artifact_validator.py`.

Проверка:

- `python -m unittest tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_split_test_design_artifacts_are_used_as_canonical_context` - passed
- повторная scoped validation fresh canary - остался только `writer-quality-gate-scoped-validator-profile-invalid`
- полный `python -m unittest tests.test_agent_artifact_validator` не уложился в 300 секунд в этом прогоне
- `python scripts/run_tests.py --suite artifact-validator --shard-count 7 --shard-index 1..7` - passed, 265/265 tests

## Рекомендуемый следующий порядок работ

1. Исправить writer quality-gate contract: текущая стадия должна ссылаться только на существующий current-stage scoped-validator profile.
2. Добавить regression test на запрет future-stage validator profile в `Writer Quality Gate`.
3. Нормализовать writer output template для split artifacts: один heading на файл, без `# X` + `## X`.
4. Определиться с timeout policy для writer-stage: либо поднять timeout для полноценных writer canary runs, либо добавить `timeout-with-artifacts` recovery.
5. После этих исправлений повторить fresh canary и довести chain до structure-preflight/reviewer, а не останавливаться на writer-r1.

## Follow-up fixes applied

Выполнено после отчета:

- validator теперь явно отклоняет `Writer Quality Gate`, если `scoped-validator-findings = pass` ссылается на reviewer/future-stage profile, например `outputs/scoped-validator-profile.structure-preflight-r1.json`;
- добавлен regression test на future-stage scoped validator profile;
- validator теперь предупреждает о некорректной форме split artifact, если файл содержит соседние дубли заголовков вида `# Source Row Inventory` + `## Source Row Inventory`; writer/output и quality-gate references обновлены тем же контрактом;
- runner timeout recovery теперь пишет artifact recovery diagnostics в `outputs/<stage>-timeout-recovery.md` и добавляет причину, почему artifact recovery не продолжил цепочку;
- timeout policy подтверждена: stage default для writer sessions уже `3600s`, а проблемный `1800s` был ручным override для canary-прогона.
