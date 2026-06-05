# Decision Log Regression

## Цель

Проверить, что ключевые стадии агента сохраняют промежуточные решения в файловом `agent-decision-log.md`, а не только в `session-log` или сообщениях чата.

## Сценарий

Запустить новую stage-handoff стадию:

- `ft-source-locator`;
- `ft-scope-analyzer`;
- `ft-test-case-writer`;
- `ft-test-case-reviewer`;
- `ft-test-case-iteration`.

Стадия должна создать `agent-decision-log.md` в текущей handoff-папке и связать его из `workflow-state.yaml`.

## Pass Criteria

- `workflow-state.yaml` содержит ссылку на `agent-decision-log.md` в `latest_artifacts.decision_log`.
- `agent-decision-log.md` существует и содержит секцию `Decision Log`.
- Таблица содержит колонки `decision_id`, `step`, `decision_type`, `input_or_trigger`, `decision`, `rationale`, `artifact_or_output`, `risk_or_confidence`.
- Каждое решение имеет стабильный ID вида `DEC-001` или `DL-001`.
- Лог фиксирует source/scope/gap/test-design/routing decisions, если они были.
- Лог не содержит hidden chain-of-thought и не является transcript команд.
- Validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --decision-log-policy strict
```

## Fail Criteria

- Решения есть только в чате или только в `Key Decisions` session log.
- `workflow-state.yaml` не ссылается на decision log.
- Decision log содержит только общие фразы без input/decision/rationale/risk.
- Decision log подменяет rationale скрытыми рассуждениями или длинным transcript команд.

## Regression Lesson

`session-log` оказался недостаточно granular: он дает сводку стадии, но не гарантирует восстановимость промежуточных решений вроде почему строка стала `gap`, почему источник исключен или почему workflow направлен на reviewer. `agent-decision-log.md` должен быть отдельным проверяемым audit artifact.

