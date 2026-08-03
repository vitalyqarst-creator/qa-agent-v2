# Audit Output Format

## Severity

- `error` - нарушение канонической структуры agent-layer или отсутствие обязательного элемента.
- `warning` - риск деградации архитектуры, который пока не ломает базовую структуру.
- `info` - наблюдение, которое полезно для сопровождения, но не требует немедленного исправления.

## Finding Categories

- `agents-policy`
- `skills-structure`
- `skill-content`
- `references`
- `scripts`
- `duplication`
- `dispatch-map`
- `stale-items`

## JSON Shape

Верхний уровень JSON-отчета должен содержать:

- `summary`
- `findings`
- `duplication_map`
- `stale_items`
- `instruction_budgets`
- `checks`

Если формируется человекочитаемое описание audit findings или значений текстовых полей внутри JSON-отчета, оно должно быть на русском языке. Служебные ключи JSON сохраняются в каноническом виде, указанном в этом формате.

`summary` должен включать:

- `skills_count`
- `findings_count`
- `errors_count`
- `warnings_count`
- `info_count`

Каждый объект в `findings` должен включать:

- `id`
- `severity`
- `category`
- `title`
- `details`
- `evidence`
- `recommended_move`
- `paths`

`duplication_map` хранит confirmed и possible duplicates с указанием источников и canonical target.

`stale_items` хранит references, skills, sections или scripts, которые больше не участвуют в актуальной agent-architecture.

`instruction_budgets` хранит budget rows по сценариям из `references/agent/instruction-loading-manifest.md`:

- `scenario`
- `files_count`
- `total_kib`
- `limit_kib`
- `status`

`checks` хранит результаты отдельных автоматических проверок с полями:

- `name`
- `status`
- `details`
- `paths`

## Recommended Move

- Формулируй `recommended_move` как конкретное следующее действие.
- Ссылайся на каноническое место хранения знания, если перенос или дедупликация являются частью исправления.
- Не предлагай автоматическое исправление там, где нужна продуктовая или архитектурная развилка.
