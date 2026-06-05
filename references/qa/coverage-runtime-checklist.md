# Coverage Runtime Checklist

Этот reference задает короткий runtime checklist покрытия. Полный `coverage-checklist.md` остается deep reference для специализированных dimensions и reviewer analysis.

## Runtime Dimensions

Перед написанием `TC-*` проверь, применимы ли к scope:

- visibility / availability;
- requiredness;
- editability;
- default value;
- list or dictionary composition;
- positive acceptance;
- negative rejection;
- boundary / length / numeric classes;
- exact length and allowed-symbol classes;
- conditional branches and dependencies;
- state transition or navigation;
- persistence after save/reopen;
- calculation oracle;
- integration/API/async/internal effects;
- repeated blocks, tables, files or documents;
- generated document content mapping;
- role/status/security/NFR dimensions.

## Runtime Rules

- Добавляй baseline case только если expected behavior следует из ФТ или разрешенных package materials.
- Если dimension применим, но oracle не описан, фиксируй `GAP-*` / `unclear`.
- Не закрывай internal/integration/API/async/persistence behavior UI-only test case без наблюдаемого artifact.
- Для условной видимости проверяй positive branch и inverse branch, если inverse behavior следует из требования; иначе фиксируй gap.
- Для closed list проверяй expected values and absence of extra values только если закрытость следует из source.
- Для numeric/date/length/mask rules подгружай deep coverage reference по соответствующему scenario.
- Для numeric-only, exact length, repeatable/action-created blocks, checkbox-list и generated documents используй `Coverage Obligation Table` и не ограничивайся одним generic TC.
- Для 3+ независимых факторов с несколькими значениями рассмотрение pairwise/combinatorial coverage обязательно; выбери `2-way | 3-way | t-way`, докажи coverage strength или фиксируй gap.
- Для reusable baseline и negative transition используй concrete fixture или `fixture-catalog.md`.
- Для applicable dimensions фиксируй coverage metrics; отсутствие метрики считается незакрытой design work.

## Deep Coverage Triggers

Подгружай полный `coverage-checklist.md` или специализированный deep reference, если scope содержит:

- numeric, amount, mask, exact length or allowed-symbol constraints;
- date/time windows, timezone, business date or boundary inclusivity;
- integration/API/server-side validation;
- async/race/retry behavior;
- security/roles/permissions;
- complex decision table;
- pairwise/combinatorial factors;
- file upload/download or generated documents;
- repeatable blocks or action-created optional blocks;
- checkbox-list / multi-select behavior;
- performance/reliability/compatibility/usability/accessibility expectations;
- reviewer/validator finding about missed coverage dimension.
