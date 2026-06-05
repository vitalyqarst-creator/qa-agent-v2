# Session Log Format

`Session log` - постоянный audit artifact для ключевых стадий агента. Он фиксирует решения и риски, а не полный transcript команд.

## Назначение

Session log нужен, чтобы последующий review или анализ качества не зависел от истории чата и скриншотов промежуточных сообщений.

Если стадия принимает несколько промежуточных решений, session log не должен разрастаться в пошаговый transcript. В этом случае веди отдельный `agent-decision-log.md` по `references/agent/agent-decision-log-format.md`, а в `Key Decisions` оставляй только сводку и ссылку на decision log.

Лог обязателен для новых запусков стадий:

- `ft-source-locator`;
- `ft-scope-analyzer`;
- `ft-test-case-writer`;
- `ft-test-case-reviewer`;
- `ft-test-case-iteration`.

## Расположение

Храни лог в текущей stage-handoff папке:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/<stage>-session-log.md
```

Рекомендуемые имена:

- `source-locator-session-log.md`;
- `scope-analyzer-session-log.md`;
- `writer-session-log.md`;
- `reviewer-session-log.round-1.md`;
- `reviewer-session-log.round-2.md`;
- `iteration-session-log.md`.

Если стадия работает внутри session-based review-cycle, лог должен быть связан из `cycle-state.yaml` или совместимого `workflow-state.yaml` текущего scope через `latest_artifacts`.

## Workflow Link

`workflow-state.yaml` должен ссылаться на лог:

```yaml
latest_artifacts:
  session_log: work/stage-handoffs/NN-<scope-slug>/writer-session-log.md
```

Лог должен соответствовать stage из `current_stage`: по ожидаемому имени файла или по `Session Metadata` / `skill`. Например, `ft-source-locator` должен ссылаться на `source-locator-session-log.md` или на лог с `skill = ft-source-locator`, writer - на `writer-session-log.md` или лог с `skill = ft-test-case-writer`, reviewer - на `reviewer-session-log.*.md` или лог с `skill = ft-test-case-reviewer`.

Допустимы более конкретные ключи, если нужен round/stage context:

```yaml
latest_artifacts:
  writer_session_log: work/stage-handoffs/NN-<scope-slug>/writer-session-log.md
  reviewer_round_1_session_log: work/stage-handoffs/NN-<scope-slug>/reviewer-session-log.round-1.md
```

## Required Sections

Используй точные заголовки. Эти секции являются базовым форматом и проверяются `--session-log-policy strict`:

```md
# <Stage> Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `initial_draft` |
| ft_slug | `<ft-slug>` |
| scope_slug | `<scope-slug>` |
| started_from | `workflow-state.yaml` |
| status_after | `ready-for-review` |

## Inputs Read

- `<path>` - зачем прочитан.

## Inputs Not Used

- `<path or package>` - почему не использовался.
- `none` - если ограничений не было.

## Key Decisions

- `<decision>` - причина и affected artifact/package.

## Risks And Fallbacks

- `<risk/fallback>` - impact и handling.
- `none` - если рисков и fallback не было.

## Validation

- `<command or check>` - result.

## Contamination Check

- `<what was excluded>` - result.
```

## Audit Sections

Для новых clean eval runs, writer/reviewer diagnostics и любых запусков, где важен последующий анализ качества, добавляй также audit-секции. Они проверяются `--session-log-policy audit`:

```md
## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Created session log before stage work | Log file exists before reading source artifacts | `<path>` |
| 2 | Read workflow and handoff inputs | Scope and package boundaries confirmed | `workflow-state.yaml`; `scope-contract.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass/fail/not-applicable | `<section/table/check>` | `<rewrite/review focus/none>` |
| Self-check near misses | pass/fail/not-applicable | `<what almost failed or was manually judged>` | `<action taken>` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |

## Handoff Notes For Next Session

- `<specific issue, uncertainty, or reviewer focus>` - why it matters.
- `none` - only if there are no open doubts, no manual judgments, and no recommended reviewer focus.
```

Audit-секции не заменяют findings, writer response или review summary. Они нужны для восстановления хода решений: где агент столкнулся с техническим ограничением, что перепроверял вручную, какие сомнительные места оставил следующей стадии и почему.

## UTF-8 / Console Handling

Для русскоязычных ФТ и Markdown-артефактов не используй обычный PowerShell stdout как источник истины, если есть риск mojibake. Перед чтением русских файлов через shell выставляй UTF-8 preamble:

```powershell
chcp 65001 > $null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

Даже с preamble важные source artifacts перечитывай через явную кодировку:

- PowerShell: `Get-Content <path> -Encoding UTF8`;
- Python: `Path(path).read_text(encoding="utf-8")`;
- запись Markdown/JSON: `encoding="utf-8"` и file-based helper вместо длинной command line.

Если консольный вывод исказил кириллицу, это technical fallback. В `Technical Fallbacks` обязательно укажи:

- affected command/source/artifact;
- что источник был перечитан через явный UTF-8 file/script path;
- что mojibake/distorted stdout был отброшен и не использовался как evidence для анализа, трассировки, expected result или decisions.

Если этого нет, audit validator выдает `session-log-encoding-fallback-source-fidelity-missing`.

## What To Log

Логируй:

- входные артефакты, которые реально читались;
- временную последовательность ключевых событий: создание лога, чтение inputs, source extraction, fallback, запись артефактов, self-check, validation;
- явно неиспользованные соседние пакеты, старые версии и baseline artifacts;
- для clean diagnostic/eval runs: точную границу разрешенного FT-пакета и подтверждение, что соседние `fts/<ft-slug>*` не открывались, не сравнивались и не использовались;
- source quality risks: oversized blocks, encoding issues, DOCX/PDF parity risks;
- technical fallback: command length limit, failed patch, chunked writing, helper script use;
- scope/package decisions;
- quality gates, включая failed/passed `Writer Quality Gate`, near-misses и ручные semantic decisions, которые validator не может доказать;
- validation commands and result;
- contamination check для clean eval runs.

Не логируй:

- полный вывод каждой команды;
- длинные куски ФТ;
- секреты, токены, приватные credentials;
- самооценочные фразы без evidence.

## Technical Fallback Disclosure

## Artifact Write Strategy Disclosure

For audit runs that create large, package-based, table-heavy, or generated Markdown artifacts, add `## Artifact Write Strategy` before the write happens.

Required table:

```md
## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `source-normalization-diagnostic.md` | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest sections.json` | `yes` |
```

Use `scripts/write_artifact_sections.py` as the canonical helper for large/generated artifacts. `scripts/update_markdown_section.py` is acceptable only for small targeted section edits, not as the primary writer for large generated artifacts.

If a log mentions `source-row-inventory.md`, `source-normalization-diagnostic.md`, canonical `test-cases/*.md`, traceability matrix artifacts, large/package-based artifacts, or generated artifacts but has no `Artifact Write Strategy`, audit validator warns with `session-log-artifact-write-strategy-missing`.

If Windows command-line limit, PowerShell here-string, one-shot write, or inline giant command appears as the failed initial method, audit validator warns with `session-log-forbidden-initial-one-shot-write`; this must block clean eval runs with `--fail-on warning`.

Любой технический fallback должен быть отражен дважды:

- в `Event Timeline` как событие с причиной и результатом;
- в `Technical Fallbacks` как структурированная строка.

К техническим fallback относятся: лимит Windows command line, слишком длинный PowerShell argument/here-string, failed `apply_patch`, patch-size/context limit, переход на `chunked artifact writing`, генерация helper script, запись через временный файл, fallback на Python/Node из-за encoding или размера.

Для writer-а большого/package-based canonical file или split test-design artifacts лимит Windows command line, слишком длинный PowerShell argument/here-string, one-shot PowerShell Markdown write или inline giant command являются не штатным fallback, а нарушением `Artifact Write Strategy` preflight. Такой `TF-*` должен быть залогирован, но clean validator в audit mode выдаст warning `session-log-forbidden-initial-one-shot-write`.

Encoding fallback допустим только если он сохраняет source fidelity: failed method может быть `PowerShell console output read`, но fallback method должен быть явным UTF-8 перечитыванием файла/источника, а `quality_risk` или `follow_up` должны прямо говорить, что испорченный stdout не использовался как evidence. Иначе clean validator в audit mode выдаст warning `session-log-encoding-fallback-source-fidelity-missing`.

Для каждой строки fallback укажи:

- `fallback_id` - стабильный ID, например `TF-001`;
- `trigger` - наблюдаемая причина: error, limit, failed command, encoding issue;
- `failed_method` - что именно не сработало;
- `fallback_method` - чем заменено;
- `helper_artifact_path` - путь к helper script/temp content file, либо `n/a`, если helper artifact не создавался;
- `retained` - `yes`, если helper artifact сохранен для анализа, `no`, если удален, `n/a`, если не применимо;
- `quality_risk` - риск для качества результата, например `template drift`, `partial write`, `compact draft risk`, `none`;
- `follow_up` - что должен проверить reviewer или следующая стадия.

Запрещено писать только `none`, если в ходе работы был technical fallback. Если helper script создавался, но удален, укажи исходный path/name и `retained = no`.

## Validator Policy

В compatible mode отсутствие session log у stage workflow фиксируется как `info`, чтобы не создавать legacy noise.

Для обычных новых scope/eval runs используй strict mode:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy strict
```

Для диагностических прогонов, где нужно анализировать почему агент принял решения, используй audit mode:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy audit
```

Strict mode должен предупреждать, если:

- stage workflow не ссылается на `*session-log*.md`;
- session log не содержит required sections;
- required sections пустые.

Audit mode дополнительно предупреждает, если:

- нет `Event Timeline`;
- нет `Quality Checkpoints`;
- нет `Technical Fallbacks`;
- нет `Handoff Notes For Next Session`;
- audit-секции пустые или заполнены только заголовками.
- `ft-source-locator` log не называет выбранный `fts/<ft-slug>` и исключенные neighboring/baseline packages в `Inputs Not Used` / `Contamination Check`.
- `workflow-state.yaml` ссылается на session log другого stage.
- writer session log фиксирует initial one-shot PowerShell / here-string / inline giant command для большого canonical artifact.
- encoding fallback не доказывает, что source был перечитан UTF-8 способом и испорченный stdout не использовался как evidence.
- рядом с writer handoff есть `writer-process-diagnostic.md` с `verdict: fail`, `process_readiness: contaminated` или `validator_gap_suspected: yes`, но `workflow-state.yaml` всё еще переводит stage в `ready-for-review`.
- для writer handoff существует несколько `writer-process-diagnostic*.md`, но нет ровно одного active diagnostic с `active_for_current_workflow: yes`, `diagnostic_target` которого совпадает с active canonical test-case file.
