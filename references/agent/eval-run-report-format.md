# Eval Run Report Format

## Назначение

Этот формат фиксирует результат ручного или автоматизированного запуска eval-кейса.

Используй его, когда eval проверяет поведение agent skill-а, но в проекте нет runnable LLM-runner-а или запуск выполняется вручную по skill-инструкциям.

## Расположение

Сохраняй отчеты в:

```text
evals/runs/YYYY-MM-DD-<eval-slug>.md
```

## Обязательные секции

### Metadata

- `run_id`
- `run_date`
- `eval_file`
- `eval_case`
- `mode`: `manual | automated | simulated`
- `reviewed_skill`
- `runner`
- `source_instructions`
- `repository_state`

### Input

Укажи, какой блок eval-а был передан reviewer-у или использован для ручного review:

- `requirement_source`
- `writer_artifacts_under_review`
- `expected_reviewer_output`

Можно ссылаться на строки eval-файла вместо копирования всего текста.

### Actual Reviewer Output

Зафиксируй фактический или ручной reviewer output.

Для structured finding используй поля:

- `id`
- `review_mode`
- `severity`
- `category`
- `coverage_dimension`
- `test_case_id`
- `traceability_ref`
- `source_ref`
- `problem`
- `evidence`
- `required_change`

### Evaluation Result

Укажи:

- `status`: `pass | fail | inconclusive`
- `matched_expected_output`: `yes | no | partial`
- `pass_criteria_met`
- `fail_criteria_hit`

### Residual Risk

Укажи ограничения результата:

- была ли это реальная runtime-проверка агента или ручная симуляция;
- какие инструкции были использованы;
- какие части поведения не проверялись;
- что нужно сделать для более сильной проверки.

## Правила

- Не смешивай eval report с исправлением eval-кейса или тест-кейсов.
- Если runner отсутствует, явно укажи `mode: manual` и `runner: human reviewer using skill instructions`.
- Если output получен из чата с агентом, сохраняй существенный structured output, а не только краткий пересказ.
- Если eval провален, report должен содержать конкретную причину failure и следующий remediation step.
- Если eval пройден вручную, не утверждай, что runtime LLM-agent прошел eval; формулируй как `manual reviewer pass`.
