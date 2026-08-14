# Writer Runtime Contract

Это краткий контракт изолированной writer-фазы. Обычный новый scope ведёт
`ft-practical-route` v0.9; этот документ не создаёт альтернативный маршрут.

## Допуск к работе

Writer начинает только при выбранных FT package и scope, доступных DOCX/XHTML,
учтённом `AGENT-NOTES.md` и актуальном `workflow-state.json`. Для v0.9:

- matrix пишется до TC и проходит independent matrix review;
- canonical TC пишутся только после matrix `approved`;
- final TC review всегда отдельный `codex-thread` с manifest и controller-owned
  session attestation;
- у matrix и TC отдельные budgets: максимум одна content revision и один
  re-review на фазу.

Недостающий источник, противоречие или неподтверждённый business rule —
`blocked-input`/GAP, а не допущение writer-а.

## Выход

Writer меняет только свою matrix либо canonical TC, допустимые links в
`workflow-state.json` и текущие scope artifacts. Не создаёт self-check, stage
summary, receipt, benchmark, sharding или новый review loop.

## Качество

- Один TC: один поток, основная проверка и наблюдаемый результат.
- Трассируй source anchor и коды требований; `OBL-*`/`SCN-*` остаются в
  metadata, а не становятся действиями пользователя.
- Runtime-текст на русском; данные конкретны и исполнимы.
- `flow_kind`, а не ID контекста, определяет create/edit lifecycle rules.
- Параметризуй лишь значения, проверяемые одним действием с одинаковым oracle.
- Не включай в production TC параметры среды, учётные записи, секреты,
  `SETUP-*` или фиктивные данные интеграций.
