# FT2 OF11 Clean Run Regression

## Цель

Проверить на чистом пакете `fts/ft-2-OF_11`, что агент применяет актуальные workflow/gate rules из локальных `skills/` и `references/` без дополнительных подсказок пользователя.

Этот eval связывает несколько отдельных regression gates:

- `source-selection-handoff-regression.md`;
- `scope-analyzer-handoff-regression.md`;
- `mockup-visual-inventory-regression.md`;
- `source-row-inventory-and-oracle-regression.md`;
- `writer-quality-gate-regression.md`;
- `chunked-writing-no-compact-draft-regression.md`;
- `package-by-package-all-scopes-regression.md`.

## Clean-Run Rule

Prompts для агента не должны напрямую перечислять новые quality guardrails. Нельзя подсказывать:

- создать `source-row-inventory.md`;
- сверить writer-side inventory с handoff inventory;
- открыть mockup и создать `mockup-visual-inventory.md`;
- сохранить PDF-only `GSR` codes;
- запретить generic steps или generic expected results;
- использовать Writer Quality Gate.

Допустимо явно ограничивать только:

- рабочий пакет: `fts/ft-2-OF_11`;
- запрет использовать соседние `fts/ft-2-OF*`;
- одну выполняемую стадию;
- команду validator с `--root fts/ft-2-OF_11`.

Если агент проходит eval только после явного напоминания конкретного gate, eval считается проваленным.

## Scenario

Запустить staged workflow на чистом пакете `fts/ft-2-OF_11`:

1. `ft-source-locator`;
2. `ft-scope-analyzer` в режиме `agent-proposed-scope`;
3. confirmed `ft-scope-analyzer` для candidate scope `ui-main-info`;
4. single `ft-test-case-writer` writer-pass по confirmed scope.

Reviewer/iteration не запускать до завершения writer-pass и validator check.

## Prompt Script

Эти prompts являются частью eval. Их можно отправлять агенту последовательно. Они намеренно не перечисляют quality guardrails из `Clean-Run Rule`.

### Prompt 1: Source Locator

```text
Перейди в `C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-transfer`.

Выполни только стадию `ft-source-locator` для пакета `fts\ft-2-OF_11`.

Задача:
- определить основной ФТ, PDF-версию, support-файлы, mockups и package-specific context;
- создать только source-locator handoff artifacts;
- обновить `workflow-state.yaml` для следующей стадии;
- не выполнять scope analysis;
- не создавать `scope-contract.md`;
- не создавать `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`;
- не писать тест-кейсы;
- не запускать reviewer или iteration.

Ограничение чистой проверки:
- работай только внутри `fts\ft-2-OF_11`;
- не открывай и не используй соседние пакеты `fts\ft-2-OF`, `fts\ft-2-OF_2`, `fts\ft-2-OF_3`, `fts\ft-2-OF_4`, `fts\ft-2-OF_5`, `fts\ft-2-OF_6`, `fts\ft-2-OF_7`, `fts\ft-2-OF_8`, `fts\ft-2-OF_9`, `fts\ft-2-OF_10`;
- если проверяешь валидатором, запускай его строго с `--root fts\ft-2-OF_11`.

В конце дай список созданных файлов и результат validator.
```

### Prompt 2: Scope Selection

```text
Продолжи workflow только для `fts\ft-2-OF_11`.

Выполни только `ft-scope-analyzer` в режиме `agent-proposed-scope`.

Используй текущий `workflow-state.yaml` и source-locator handoff artifacts.

Задача:
- предложить candidate scope-ы;
- создать только scope-selection artifacts;
- оставить workflow в состоянии ожидания выбора одного scope пользователем;
- не создавать confirmed `scope-contract.md`;
- не создавать writer handoff;
- не писать тест-кейсы;
- не запускать reviewer или iteration.

Ограничение чистой проверки:
- работай только внутри `fts\ft-2-OF_11`;
- не открывай и не используй соседние `fts\ft-2-OF*`;
- validator запускай строго с `--root fts\ft-2-OF_11`.

В конце дай список candidate scope-ов, созданных файлов и результат validator.
```

### Prompt 3: Confirm `ui-main-info`

```text
Продолжи workflow только для `fts\ft-2-OF_11`.

Подтверди candidate scope `ui-main-info` из текущих scope-selection artifacts и выполни только стадию `ft-scope-analyzer` для confirmed scope.

Используй текущий `workflow-state.yaml`, `scope-options.md` и `scope-selection-prompts.md`.

Задача:
- создать confirmed handoff artifacts для `ui-main-info`;
- обновить `workflow-state.yaml` для следующего этапа;
- не писать тест-кейсы;
- не запускать writer, reviewer или iteration.

Ограничение чистой проверки:
- работай только внутри `fts\ft-2-OF_11`;
- не открывай и не используй соседние `fts\ft-2-OF*`;
- validator запускай строго с `--root fts\ft-2-OF_11`.

В конце дай список созданных файлов и результат validator.
```

### Prompt 4: Writer Pass

```text
Продолжи workflow только для `fts\ft-2-OF_11`, confirmed scope `ui-main-info`.

Выполни только writer-pass по текущему `workflow-state.yaml` и handoff artifacts.

Задача:
- создать canonical test-case file для `ui-main-info`;
- создать writer session log;
- создать handoff prompt к reviewer;
- обновить `workflow-state.yaml`;
- не запускать reviewer;
- не запускать iteration;
- не ставить `signed-off`.

Ограничение чистой проверки:
- работай только внутри `fts\ft-2-OF_11`;
- не открывай и не используй соседние `fts\ft-2-OF*`;
- validator запускай строго с `--root fts\ft-2-OF_11`.

В конце дай список созданных файлов, количество `ATOM-*`, количество `TC-*`, статус workflow и результат validator.
```

## Stage 1 Pass Criteria: Source Locator

- Созданы только source-locator handoff artifacts.
- Есть `source-selection.md` с required sections и canonical `selection_status`.
- `workflow-state.yaml` связан с `source-selection.md`.
- Есть `source-locator-session-log.md` с audit sections.
- Нет `scope-contract.md`, `prompt.scope-to-writer.md`, `prompt.scope-to-iteration.md`.
- Нет test-case files.
- Validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_11 --json --fail-on warning --session-log-policy audit
```

## Stage 2 Pass Criteria: Agent-Proposed Scope

- Созданы только `scope-options.md`, `scope-selection-prompts.md`, `scope-analyzer-session-log.md`, обновленный `workflow-state.yaml`.
- Workflow ждет выбор одного candidate scope: `stage_status: blocked-input`.
- Нет confirmed `scope-contract.md`.
- Нет writer/reviewer artifacts.
- Нет test-case files.
- Validator проходит с тем же `--root fts\ft-2-OF_11`.

## Stage 3 Pass Criteria: Confirmed `ui-main-info`

- Создан confirmed handoff для `ui-main-info`.
- Есть `scope-contract.md`, `scope-coverage-gaps.md`, `scope-execution-options.md`, `workflow-state.yaml`.
- При наличии DOCX+PDF есть `source-parity-check.md`.
- Если parity содержит table/row parity, есть `source-row-inventory.md`.
- Если scope ссылается на mockup/screen image, есть `mockup-visual-inventory.md` с `opened = yes` и `not_used_as_requirement_source = yes`.
- `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md` содержит resolving ссылки на required inputs.
- Writer/reviewer/test-case artifacts еще не созданы.
- Validator проходит с тем же `--root fts\ft-2-OF_11`.

## Stage 4 Pass Criteria: Writer Pass

- Создан canonical test-case file только для confirmed `ui-main-info`.
- Создан `writer-session-log.md`.
- Создан `prompt.writer-to-reviewer.round-1.md`.
- `workflow-state.yaml` указывает `current_stage: ft-test-case-writer`, `stage_status: ready-for-review`, `next_skill: ft-test-case-reviewer`.
- `workflow-state.yaml` не содержит `signed-off`.
- Canonical file содержит:
  - `Artifact Write Strategy`;
  - `Source Row Inventory`, если source/table flow применим;
  - `Source Table Normalization`, если source/table flow применим;
  - `Atomic Requirements Ledger`;
  - `Package Test Design Plan`;
  - `Test-design Applicability Matrix`;
  - `Dependency Matrix`, если есть зависимости;
  - `Risk / Priority Map`;
  - `Writer Quality Gate`;
  - `Writer Self-Check`.
- Writer-side `Source Row Inventory` сохраняет every in-scope/unclear `source_row_id` из handoff `source-row-inventory.md`.
- Validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_11 --json --fail-on warning --session-log-policy audit
```

## Fail Criteria

Eval провален, если на любом этапе:

- агент использует соседние `fts/ft-2-OF*` как baseline или пример;
- source-locator создает scope/writer artifacts;
- scope selection сразу пишет confirmed `scope-contract.md` без выбора одного candidate scope;
- confirmed scope handoff не создает conditional artifacts, которые требуются локальными инструкциями;
- writer создает test cases без required handoff artifacts;
- writer ставит `ready-for-review`, но validator показывает warning/error;
- writer-side inventory теряет source rows из handoff inventory;
- writer пишет compact/summary draft после technical limit;
- writer создает generic TC steps/expected results и при этом считает Writer Quality Gate passed;
- workflow ставит `signed-off` до reviewer.

## Required Evidence To Save

- Список созданных/измененных файлов после каждого stage.
- Validator JSON или краткая summary после каждого stage.
- Session log для каждого stage.
- Если stage падает, сохранить exact finding ids validator-а.
- После writer-pass сохранить counts: `ATOM-*`, `TC-*`, `GAP-*`, source rows in handoff inventory, source rows in writer inventory.

Для read-only сбора evidence после каждого stage можно использовать helper:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json
```

Для markdown-фрагмента в run report:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --markdown
```

Чтобы получить только следующий допустимый prompt для текущего clean-run checkpoint:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --next-prompt
```

Helper output includes `clean_run_assessment` with `stage`, `status`, `next_expected_prompt`, and concrete failure reasons. Use it as the first-pass stage classification after every prompt; independent review is still required for semantic TC quality.

Для автоматической проверки checkpoint-а можно требовать конкретный stage/status:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json --expect-stage not-started --expect-status pending
```

После `Prompt 1` ожидается:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json --expect-stage source-locator --expect-status pass
```

После `Prompt 2` ожидается:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json --expect-stage agent-proposed-scope --expect-status pass
```

После `Prompt 3` ожидается:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json --expect-stage confirmed-scope --expect-status pass
```

После `Prompt 4` ожидается:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json --expect-stage writer-pass --expect-status pass
```

## Run Report Template

После фактического clean run сохрани отчет в:

```text
evals/runs/YYYY-MM-DD-ft2-of11-clean-run-regression.md
```

Шаблон можно сгенерировать из текущего evidence:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --run-report-template --output evals/runs/YYYY-MM-DD-ft2-of11-clean-run-regression.md
```

Если helper недоступен, используй ручной шаблон ниже:

```md
# Eval Run Report: ft2-of11-clean-run-regression

## Metadata

- run_id: `YYYY-MM-DD-ft2-of11-clean-run-regression`
- run_date: `YYYY-MM-DD`
- eval_file: `evals/ft2-of11-clean-run-regression.md`
- eval_case: `fts/ft-2-OF_11 / ui-main-info`
- mode: `manual`
- reviewed_skill: `ft-source-locator`, `ft-scope-analyzer`, `ft-test-case-writer`
- runner: `external Codex agent session`
- source_instructions: `AGENTS.md`, `skills/*/SKILL.md`, `references/agent/*`, `references/qa/*`
- repository_state: `<short summary before run>`

## Prompt Inputs Used

| stage | prompt_source | prompt_modified | notes |
| --- | --- | --- | --- |
| source-locator | `Prompt 1` from eval | `no` | `...` |
| scope-selection | `Prompt 2` from eval | `no` | `...` |
| confirmed-scope | `Prompt 3` from eval | `no` | `...` |
| writer-pass | `Prompt 4` from eval | `no` | `...` |

If `prompt_modified = yes`, explain why. If a modification reminded the agent of a forbidden Clean-Run Rule, mark the eval `fail`.

## Stage Results

| stage | status | artifacts_created | validator_command | validator_result | finding_ids |
| --- | --- | --- | --- | --- | --- |
| source-locator | `pass/fail` | `...` | `python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_11 --json --fail-on warning --session-log-policy audit` | `...` | `...` |
| scope-selection | `pass/fail` | `...` | same | `...` | `...` |
| confirmed-scope | `pass/fail` | `...` | same | `...` | `...` |
| writer-pass | `pass/fail` | `...` | same | `...` | `...` |

## Source / Mockup / Inventory Evidence

| check | expected | actual | status | evidence |
| --- | --- | --- | --- | --- |
| source-selection content gate | required sections and `selection_status` | `...` | `pass/fail` | `...` |
| source-parity-check | present for DOCX+PDF | `...` | `pass/fail` | `...` |
| mockup-visual-inventory | present/opened for UI mockup scope | `...` | `pass/fail` | `...` |
| handoff source-row-inventory | present for row-level/table parity | `...` | `pass/fail` | `...` |
| writer source-row carry-over | writer inventory preserves handoff in-scope/unclear rows | `...` | `pass/fail` | `...` |

## Writer Output Metrics

Use:

```powershell
python scripts\collect_clean_run_evidence.py --root fts\ft-2-OF_11 --json
```

- canonical_test_case_file: `...`
- atom_count: `...`
- tc_count: `...`
- gap_count: `...`
- handoff_source_row_count: `...`
- writer_source_row_count: `...`
- missing_handoff_source_rows_in_writer: `...`
- clean_run_assessment.stage: `...`
- clean_run_assessment.status: `pass/fail/pending/inconclusive`
- clean_run_assessment.reasons: `...`
- writer_quality_gate_status: `pass/fail/missing`
- artifact_write_strategy_status: `pass/fail/missing`
- generic_tc_smell_findings: `...`

## Evaluation Result

- status: `pass | fail | inconclusive`
- matched_expected_output: `yes | no | partial`
- pass_criteria_met:
  - `...`
- fail_criteria_hit:
  - `...`

## Residual Risk

- Was this a real external agent run or a manual simulation: `...`
- Did the run use only the prompts from this eval: `yes/no`
- Did the agent read local skills/references without direct reminders: `yes/no/unclear`
- What semantic TC quality remains unverified before independent review: `...`
- Next remediation step if failed: `...`
```

## Regression Lesson

Цель clean run не в том, чтобы получить хорошие TC любой ценой. Цель - проверить, встроены ли правила качества в агентную архитектуру. Если пользователь вынужден напоминать `source-row-inventory`, mockup usage, GSR carry-over или no-generic-steps, значит правила все еще не стали воспроизводимым поведением агента.
