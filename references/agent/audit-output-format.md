# Audit Output Format: runtime-v1

## Severity

- `error` - нарушение канонической структуры agent-layer или отсутствие обязательного элемента.
- `warning` - риск деградации архитектуры, который пока не ломает базовую структуру.
- `info` - наблюдение, которое полезно для сопровождения, но не требует немедленного исправления.

## Finding Categories

- `profile`
- `runtime-structure`
- `skills-structure`
- `references`
- `stale-items`
- `tests`

## JSON Shape

Верхний уровень JSON-отчета должен содержать:

- `profile`
- `summary`
- `findings`
- `duplication_map`
- `stale_items`
- `instruction_contexts`
- `skipped_checks`
- `checks`

Если формируется человекочитаемое описание audit findings или значений текстовых полей внутри JSON-отчета, оно должно быть на русском языке. Служебные ключи JSON сохраняются в каноническом виде, указанном в этом формате.

`summary` должен включать:

- `valid`
- `skills_count`
- `checks_count`
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

`duplication_map` хранит точные нормализованные совпадения как `possible`. Они не становятся findings без ручной оценки.

`stale_items` хранит references, skills, sections или scripts, которые больше не участвуют в актуальной agent-architecture.

`instruction_contexts` хранит верхнюю оценку AGENTS + skill + транзитивно достижимых runtime references. Это не доказательство фактической загрузки каждого файла:

- `role`
- `files_count`
- `files`
- `total_bytes`
- `total_kib`
- `measurement = reachable-linked-upper-bound`
- `status`

Аудитор не вводит произвольный fail-threshold для размера контекста. Рост оценивается по динамике и реальному влиянию.

`skipped_checks` явно показывает, какие optional checks не запускались и почему.

`checks` хранит результаты отдельных автоматических проверок с полями:

- `id`
- `status`
- `details`
- `paths`

## Recommended Move

- Формулируй `recommended_move` как конкретное следующее действие.
- Ссылайся на каноническое место хранения знания, если перенос или дедупликация являются частью исправления.
- Не предлагай автоматическое исправление там, где нужна продуктовая или архитектурная развилка.
