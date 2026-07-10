# Design: `codex exec` backend для review cycle

## Статус и границы

Реализован минимальный отдельный runner `scripts/codex_exec_review_cycle_runner.py`. Существующий SDK runner не изменён и остаётся основным fallback/debug path. Exec backend пока prototype: live CLI contract не подтверждён capability probe, поэтому переключать default backend нельзя.

## Поток состояния

```text
cycle-state.yaml + runner-events.ndjson
  -> explicit source/handoff files
  -> writer stage process
  -> draft + stdout/stderr/events + writer status
  -> deterministic draft validation
  -> reviewer stage process (configured read-only)
  -> reviewer stdout/events -> validated review contract -> findings file
  -> accepted terminal state in cycle-state.yaml
  -> runner-only atomic promotion (если явно разрешена)
```

`codex exec` и его final message не являются source of truth. Runner записывает каждое решение в `cycle-state.yaml`, status JSON и `runner-events.ndjson`. Повторный writer process автоматически не запускается.

Prototype не переиспользует runner-owned artifacts из прежней попытки. Каждый process использует Stage Contract v2 и отдельный `attempts/<stage-id>/attempt-001/`; наличие старого attempt-root блокирует запуск до subprocess. Поэтому старый draft не может ошибочно удовлетворить expected-output check нового writer process.

## Stage contracts

Writer получает только явно переданные instruction, source и handoff paths. Runner создаёт неизменяемый `stage-input.json`; prompt и draft находятся в writer attempt-root, а единственный stage-write root — `stage-output/`. Writer не промотирует artifact и не должен менять `test-cases/`.

Reviewer получает те же source/handoff paths, writer draft и validator report. Команда строится с отдельным reviewer sandbox value, без output-last-message file. Reviewer возвращает в final stdout/message один JSON contract:

```json
{"decision":"accepted|changes-required","findings_markdown":"# Review findings\n..."}
```

Runner извлекает final agent message из JSONL events, если JSON flag подтверждён, либо использует plain stdout. Затем runner сам пишет findings в reviewer `runner-output/`; reviewer manifest не содержит allowed write roots. Для каждого успешного stage JSON events обязаны раскрыть новый backend session/thread id, иначе stage блокируется контрактом.

Фактические captures, hashes и outcome фиксируются в неизменяемом `stage-result.json`. Result сверяется с input digest, declared outputs и ранее использованными backend session ids до перехода состояния.

## CLI capability contract

Имена `sandbox`, `working directory`, JSON/JSONL и output-last-message flags конфигурируются, а не предполагаются. `cli_contract_verified=false` блокирует запуск до создания subprocess. Это намеренное ограничение: текущий probe не смог исполнить `codex exec --help`, поэтому hard-coded live flags создавали бы ложное ощущение sandbox enforcement.

## Deterministic validation

После появления draft runner вызывает `ProjectDraftStructureValidator`. Он повторно использует существующий deterministic Markdown structure evaluator из SDK runner, не запускает SDK и не меняет test-design/validator rules. Validator report сохраняется в writer attempt `runner-output/validator.json`.

Ограничение: этот gate проверяет структуру исполнимых TC, но не заменяет полный `validate_agent_artifacts.py` и semantic reviewer. До выбора exec backend по умолчанию нужен staging-compatible full validator adapter, который проверяет work draft без преждевременного помещения в production `test-cases/`.

## Timeout и recovery

- Timeout без writer draft: `blocked-timeout`.
- Timeout с writer draft: продолжение возможно только как `completed-with-progress`, если deterministic validator прошёл; решение фиксируется до reviewer start.
- Reviewer timeout: всегда `blocked-timeout`; partial review не считается sign-off.
- Non-zero exit: `blocked-process-exit` с путями stdout/stderr/events.
- Missing/invalid output: `blocked-missing-output` или `blocked-invalid-output`.
- Automatic retry отсутствует. Следующий процесс требует явного recovery decision вне этого prototype.
- Повторное использование cycle directory со stale runner outputs блокируется до запуска process.

## Production safety и promotion

Runner хеширует всё дерево `fts/<ft>/test-cases/**/*.md` до writer и сравнивает его после writer и reviewer. Любое изменение до runner promotion даёт `blocked-forbidden-production-change`. Read-only sandbox остаётся первичным enforcement, hash comparison — detection/defense-in-depth.

После writer validation runner фиксирует SHA-256 draft. Изменение или удаление draft во время read-only reviewer stage даёт `blocked-forbidden-input-change`; promotion повторно сверяет тот же hash до и после atomic copy. Это связывает validator/reviewer evidence с фактически продвигаемыми байтами.

Promotion выключена по умолчанию. При явном разрешении она возможна только после:

1. writer output существует;
2. deterministic validator прошёл;
3. reviewer завершился с exit code `0`;
4. reviewer contract валиден и имеет `decision=accepted`;
5. `cycle-state.yaml` записан как `accepted-awaiting-promotion`;
6. production snapshot не изменился;
7. существующий final не перезаписывается без отдельного разрешения.

Runner копирует draft во временный файл, сверяет SHA-256 и атомарно заменяет final path. После этого state становится `signed-off`. Crash между atomic copy и final state update остаётся recovery risk prototype; production validator должен трактовать такой artifact как unsigned до reconciliation.

## Почему отдельный runner

SDK runner содержит зрелую state machine и сложную recovery-логику. Добавление `--backend exec` в него повысило бы regression risk и связало бы prototype с session/thread lifecycle. Отдельный runner позволяет тестировать process/artifact contracts изолированно и сохраняет SDK поведение без изменений.
