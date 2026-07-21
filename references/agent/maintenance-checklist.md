# Maintenance Checklist

Используй этот checklist при аудите agent-layer.

## Структура

- Все активные skill-и перечислены в `skills/README.md`.
- Количество активных skill-ов остается в диапазоне 4-7.
- У каждого skill-а есть `SKILL.md` и `agents/openai.yaml`.

## Размещение знаний

- `AGENTS.md` не содержит step-by-step workflow конкретных фаз.
- Shared правила вынесены в `references/agent/` и `references/qa/`.
- Внутри `skills/` нет локальных копий shared references без необходимости.

## Дублирование

- Одинаковые policy-тексты не повторяются в нескольких местах.
- QA format / coverage / traceability rules имеют один канонический источник.
- Скрипты не содержат скрытых доменных правил, не отраженных в references или code API.

## Связность

- Каждый skill ссылается на нужные канонические references.
- Нет сиротских references, на которые никто не ссылается.
- `skills/README.md` совпадает с реальным набором активных skill-ов.
- `references/agent/instruction-loading-manifest.md` содержит актуальные scenario budgets, а `scripts/resolve_instruction_context.py` возвращает только нужные runtime references для выбранного сценария.
- Новый production/promotion-capable workflow использует compiler contract v3, полный source assertion manifest и независимый exact-digest receipt; marker-only/legacy package не допускается к promotion.

## Ревью agent instructions

- Измененные материалы соответствуют `references/agent/instruction-authoring-policy.md`.
- Для каждого затронутого instruction-loading scenario проверен фактически загружаемый набор файлов, а не неограниченный контекст репозитория.
- В ограниченном контексте нет отсутствующих, неоднозначных или противоречивых указаний, способных изменить поведение целевого агента.
- Избыточные пояснения и чрезмерно конкретные правила удалены; одинаковая семантика сведена к одному правилу на самом высоком точном переиспользуемом уровне.
- После смысловой проверки повторно запущены применимые architecture, agent-layer и budget gates.

## Runtime Environment And Encoding

- Shell/UTF-8 правила имеют один canonical source: `references/agent/runtime-environment-encoding-policy.md`, краткое обязательное правило остается в `AGENTS.md`.
- Перед изменениями source extraction, writer/reviewer generators, command examples или Cyrillic-sensitive workflows запускай `python scripts/probe_environment.py` либо фиксируй эквивалентный probe.
- PowerShell-инструкции не используют Bash heredoc `python <<'PY'`; Bash-инструкции явно выставляют UTF-8 environment; unknown-shell инструкции используют ASCII-only команды или UTF-8 helper files.
- Production `fts/**/test-cases/*.md` не содержит PowerShell/heredoc/stdout encoding/mojibake/extractor debug diagnostics.
- Коды требований используются как anchors; русскоязычный текст ФТ должен быть прочитан через UTF-8-safe source/helper.

## Проверки

После изменения `AGENTS.md`, `skills/`, `references/agent/`, `references/qa/`, `README.md` или agent-layer scripts запускай:

```powershell
python scripts/probe_environment.py
python scripts/run_tests.py --suite architecture
python scripts/run_tests.py --suite agent-layer
python scripts/resolve_instruction_context.py --scenario writer.initial_draft.simple --budget-report --fail-on-budget
python scripts/resolve_instruction_context.py --scenario writer.initial_draft.table --budget-report --fail-on-budget
python scripts/resolve_instruction_context.py --scenario writer.remediation.validator_failure --budget-report --fail-on-budget
python scripts/resolve_instruction_context.py --scenario reviewer.session_prepared_source_assertion --budget-report --fail-on-budget
```

Перед завершением крупной правки pipeline-артефактов дополнительно запускай:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning
```

Для новых `signed-off` / `round-cap-reached` handoff states включай strict final aliases:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning --final-alias-policy strict
```

Если добавляешь новый FT-пакет, заменяешь основной source DOCX или меняешь source parsing, запускай strict source-quality policy:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning --source-quality-policy strict
```

Для существующих legacy source DOCX сверяй strict-warning с зафиксированным решением:

```powershell
references/agent/source-quality-strict-warning-review-2026-05-25.md
```

Для финальной проверки всего Python/test слоя используй:

```powershell
python scripts/run_tests.py
```


