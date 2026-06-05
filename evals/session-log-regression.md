# Session Log Regression

## Цель

Проверить, что ключевые стадии агента сохраняют audit trail в файловом артефакте, а не только в промежуточных сообщениях чата.

## Сценарий

Запустить любую новую stage-handoff стадию:

- `ft-source-locator`;
- `ft-scope-analyzer`;
- `ft-test-case-writer`;
- `ft-test-case-reviewer`;
- `ft-test-case-iteration`.

Стадия должна создать `*session-log*.md` в текущей handoff-папке и связать его из `workflow-state.yaml` через `latest_artifacts`.

## Pass Criteria

- `workflow-state.yaml` содержит ссылку на `*session-log*.md`.
- Файл session log существует.
- Session log содержит required sections:
  - `Session Metadata`;
  - `Inputs Read`;
  - `Inputs Not Used`;
  - `Key Decisions`;
  - `Risks And Fallbacks`;
  - `Validation`;
  - `Contamination Check`.
- Для diagnostic/clean eval run session log содержит audit sections:
  - `Event Timeline`;
  - `Quality Checkpoints`;
  - `Technical Fallbacks`;
  - `Handoff Notes For Next Session`.
- `Inputs Not Used` фиксирует соседние пакеты/старые версии, если clean eval запрещает их использовать.
- Для `ft-source-locator` clean run лог фиксирует выбранный FT package boundary и contamination check до handoff к scope analyzer.
- Для каждой обязательной стадии `workflow-state.yaml` ссылается на session log того же stage: по ожидаемому имени файла или по `Session Metadata` / `skill`; ссылка на лог другого stage не засчитывается.
- Для `ft-source-locator` clean run `Inputs Not Used` / `Contamination Check` явно называют выбранный `fts/<ft-slug>` и excluded neighboring/sibling/baseline inputs, а не ограничиваются общей фразой `clean run passed`.
- `Risks And Fallbacks` фиксирует technical fallback: encoding, command length, patch limit, chunked writing.
- `Technical Fallbacks` содержит структурированную строку `TF-*` для каждого command length / failed patch / chunked writing / helper script / temp content file fallback; если fallback не было, содержит явную строку `none`.
- Для encoding/mojibake fallback `TF-*` указывает явный UTF-8 reread method и прямо фиксирует, что искаженный stdout/console output не использовался как evidence.
- `Quality Checkpoints` фиксирует writer/reviewer self-checks, failed/near-miss decisions и reviewer focus, если они были.
- Strict validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy strict
```

- Audit validator проходит для diagnostic runs:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy audit
```

## Fail Criteria

- Решения есть только в чате, но нет session log.
- `workflow-state.yaml` не ссылается на session log.
- `workflow-state.yaml` ссылается на session log другого stage.
- Session log содержит только общие фразы без inputs/decisions/validation.
- Агент заявляет clean run, но не фиксирует contamination check.
- `ft-source-locator` clean run содержит contamination check, но не называет выбранный `fts/<ft-slug>` и excluded sibling/baseline packages.
- Diagnostic run не содержит timeline или quality checkpoints, поэтому невозможно восстановить ход решений без чата.
- В `Event Timeline` или `Risks And Fallbacks` есть признаки technical fallback, но `Technical Fallbacks` заполнен как `none` или отсутствует.
- Encoding/mojibake fallback залогирован, но не доказывает, что source был перечитан через UTF-8 и distorted stdout был отброшен как evidence.

## Regression Lesson

Промежуточные сообщения агента полезны, но ненадежны как источник анализа: пользователь может их пропустить, они не версионируются и не передаются в следующую сессию. Поэтому session log должен быть постоянным handoff artifact.
