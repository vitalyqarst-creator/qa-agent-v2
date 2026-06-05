# Test Design Review Format

`Test Design Review` - обязательный split artifact `work/test-design/<scope-slug>/test-design-review.md` для `initial_draft`, если создается `Package Test Design Plan`.

Цель artifact-а: заставить writer критически проверить test-design до передачи набора reviewer-у. Это не заменяет финальный `ft-test-case-reviewer`: reviewer все равно проверяет `TC-*`, traceability и expected results независимо.

## Когда Создавать

- После `Package Test Design Plan` и `Package Design Plan Self-Check`.
- До финального `Writer Quality Gate`, `writer-self-check` и `stage_status: ready-for-review`.
- В `revision_from_findings`, если findings меняют `Test Design Decision Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, coverage gaps, equivalence/boundary classes, conditional branches, action flows или internal/integration coverage.

## Обязательные Входы

Writer обязан читать и сверять:

- `source-table-normalization.md`;
- `dictionary-inventory.md`, если source/support содержит справочники, теги или fixed lists;
- `test-design-decision-table.md`;
- `coverage-obligation-table.md`, если scope содержит property types с обязательными coverage classes;
- `atomic-requirements-ledger.md`;
- `package-test-design-plan.md`;
- `coverage-metrics.md`;
- `fixture-catalog.md`, если используются reusable baselines или negative transition fixtures;
- `risk-priority-map.md`, если scope содержит high-risk atoms/dimensions;
- `test-design-defect-taxonomy.md`;
- `coverage-gaps.md`;
- `test-design-applicability-matrix.md`, `dependency-matrix.md`, `risk-priority-map.md`, если они применимы или уже созданы.

Review нельзя делать только по `package-test-design-plan.md`: часть дефектов рождается раньше, например неверная классификация `metadata_only`, потерянный `GAP-*`, пропущенные obligation classes для `numeric-format` / `amount-tags`, смешанные property classes или fake internal coverage.

Отдельно проверяй допустимость gaps. `GAP-*` не является безопасным вариантом по умолчанию: если source-backed часть требования наблюдаема в UI/API artifact, включая отображаемое значение после повторного открытия объекта/раздела, review должен требовать executable coverage для этой части и оставлять gap только на реально заблокированную часть.

## Язык Артефакта

Человекочитаемые поля `evidence` и `required_action` пиши на русском языке, если пользователь явно не запросил другой язык. Технические имена колонок, `review_item`, `status`, `severity`, `blocks_ready_for_review`, `WP-*`, `ATOM-*`, `PD-*`, `GAP-*`, `TC-*` и имена файлов остаются в каноническом виде.

## Минимальный Формат

```md
## Test Design Review

| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- | --- |
| `decision-table-classification` | `pass` | `info` | `all` | Решения TDDT согласованы со ссылками ledger/plan/TC. | - | `no` |
| `numeric-length-boundaries` | `fail` | `warning` | `WP-01` | `PD-014` покрывает точные 4 цифры и буквы, но не покрывает длины N-1/N+1 только из цифр. | Добавить короткий/длинный digit-only классы или связанный `GAP-*`. | `yes` |
| `unsupported-ui-mechanism` | `fail` | `error` | `WP-01` | `TC-...` ожидает, что буква не появится в поле, но ФТ задает только допустимый класс символов. | Заменить expected result на подтвержденное принятие/отклонение класса символов или оформить `GAP-*`. | `yes` |
```

## Колонки

- `review_item`: канонический пункт из обязательного списка ниже.
- `status`: `pass | fail | blocked | needs-rewrite`.
- `severity`: `error | warning | info`.
- `affected_package`: `WP-*` или `all`.
- `evidence`: конкретное evidence по строкам/id артефактов, например `TDD-026`, `ATOM-049`, `PD-014`, `GAP-005`, `TC-...`.
- `required_action`: точное действие по переписыванию, добавлению класса/ветки или явное действие с `GAP-*`. Используй `-` только для `status = pass`.
- `blocks_ready_for_review`: `yes | no`.

## Обязательные Пункты Review

- `decision-table-classification`: решения TDDT корректно классифицируют каждое нормализованное свойство как executable, gap/unclear, metadata-only, scenario-only или out-of-scope.
- `ledger-plan-alignment`: каждый применимый atom в ledger имеет покрытие в plan, а строки plan не противоречат статусу покрытия в ledger.
- `coverage-class-completeness`: plan раскладывает правила validation, equivalence, boundary, dependency и action на конкретные positive/negative/boundary/branch проверки или `GAP-*`.
- `coverage-metrics-completeness`: каждая applicable dimension имеет counted obligations/classes/branches/transitions, covered count и gap/unclear count.
- `fixture-specificity`: reusable baselines и negative transition fixtures раскрыты в `fixture-catalog.md` или полностью в TC/test data.
- `risk-model-completeness`: high-risk atoms имеют `impact x likelihood`, priority и residual risk decision.
- `numeric-length-boundaries`: правила точного количества цифр/длины включают принимаемую точную длину и отклоняемые короткий/длинный digit-only классы, если недостающие классы не вынесены в трассируемый gap.
- `unsupported-ui-mechanism`: TC/plan не ожидают механизм UI-обработки, текст ошибки, disabled-state, автоочистку, автоформатирование или фильтрацию ввода без прямого source evidence.
- `mask-format-coverage`: `format-mask` / `default-mask` проверяются отдельными obligation classes и TC с наблюдаемым oracle по шаблону/маске, а не только numeric-only значением.
- `dictionary-closed-set`: справочники и фиксированные перечни из ФТ/support workbook извлечены в `dictionary-inventory.md`, downstream artifacts ссылаются на `DICT-*`, значения проверяются как отображение ожидаемых active values и отсутствие лишних значений либо оформляются как `GAP-*` / `unclear`, если закрытость перечня не подтверждена.
- `conditional-branches`: правила условной visibility/requiredness/dependency/action включают true/applicable и false/inverse ветки или `GAP-*`.
- `negative-fixture-isolation`: негативные проверки переходов/кнопок задают валидное состояние всех остальных обязательных полей, чтобы failure attribution относился к проверяемому полю/условию.
- `applicability-linked-tc-semantics`: каждая applicable строка `Test-design Applicability Matrix` с linked `TC-*` семантически покрыта этим TC: его данные, шаги и expected result действительно упражняют указанную dimension.
- `gap-specificity`: gap-строки называют недостающее поведение и зависимость от источника, а не только общий текст вроде `Зафиксировать непроверяемое поведение`.
- `gap-admissibility`: каждый `gap_unclear` / `GAP-*` доказывает, что в нем не спрятаны source-backed подсказки, сообщения, красная подсветка, видимость, действия, переходы, маски, справочники, теги, date-window boundaries, отображаемое сохраненное/несохраненное значение после повторного открытия объекта/раздела или другие проверяемые UI/API outcomes.
- `internal-observability`: internal/API/RabbitMQ/model/persistence/async поведение покрывается только при наличии именованного observable artifact; иначе оно остается `GAP-*`/`unclear`.
- `metadata-only-exclusion`: structural/value-type/metadata-only строки не создают pseudo-TC и либо исключены с rationale в TDDT, либо явно помечены как non-executable.
- `tc-mapping-atomicity`: одна executable строка plan соответствует одному `TC-*`/`GAP-*`, кроме явно выделенных scenario/recovery строк, которые не заменяют атомарное покрытие.
- `ready-for-tc-writing`: итоговое решение по package: `pass` допустим только когда affected package может идти к TC writing/review без известных blocking test-design defects.

## Блокирующие Правила

Ставь `status = fail | blocked | needs-rewrite` и `blocks_ready_for_review = yes`, если:

- любой обязательный review item не выполнен;
- `Coverage Obligation Table` отсутствует или не содержит обязательные классы для `numeric-format` / `amount-tags`, когда такие property types есть в `Source Table Normalization`;
- `Coverage Obligation Table` отсутствует или не содержит обязательные классы для `format-mask` / `default-mask`, когда такие property types есть в `Source Table Normalization`;
- `Coverage Obligation Table` отсутствует или не содержит обязательные классы для `exact-length`, action-created block, repeatable block, checkbox-list или generated document output, когда такие property types есть в source/plan;
- `coverage-metrics.md` отсутствует или не содержит applicable dimension из matrix;
- `fixture-catalog.md` отсутствует при reusable/generic baseline или negative transition fixture, если baseline не раскрыт полностью в TC;
- `risk-priority-map.md` отсутствует или не содержит `impact x likelihood` для high-risk atoms;
- covered atom не имеет реальной executable строки plan или TC mapping;
- правило точного количества цифр/длины не имеет короткого/длинного digit-only класса и нет `GAP-*`, объясняющего отсутствие;
- TC ожидает неподтвержденную UI-механику вместо source-backed поведения;
- справочник или фиксированный перечень из source/support workbook не извлечен в `dictionary-inventory.md`, не покрыт как closed-set и не вынесен в `GAP-*` / `unclear`;
- негативная проверка перехода не задает valid fixture для остальных обязательных полей;
- applicable row в `Test-design Applicability Matrix` связан с `TC-*`, который проверяет другую dimension;
- правило с повторяющимися цифрами, min/max, date boundary, condition branch или action branch имеет только happy path, хотя inverse/negative/boundary ветка выводится из источника;
- `gap` rows настолько общие, что reviewer не может понять, какое конкретное source behavior осталось непокрытым;
- `gap_unclear` или `metadata_only` используется для требования с source-backed observable result: подсказкой, сообщением, красной подсветкой, подтверждением, переходом, маской, справочником/тегами, date-window boundary или отображаемым значением после повторного открытия объекта/раздела;
- gap смешивает проверяемую UI-часть и реально заблокированную часть, например отсутствующую DaData/API fixture, product catalog value, backend status или test clock;
- TDDT говорит `metadata_only` или `gap_unclear`, но ledger/plan/TC дальше помечает тот же atom как covered;
- internal/API/backend/model behavior помечено covered без observable evidence.

Writer не должен ставить `ready-for-review`, пока любая строка имеет `blocks_ready_for_review = yes` и `status` не равен `pass`.

## Связь С Writer Quality Gate

`Writer Quality Gate` должен включать строку `test-design-review`. Эта строка может быть `pass` только когда `test-design-review.md` существует, содержит все обязательные review items и не имеет blocking failed rows.

## Не Дублировать

Не копируй в этот artifact полные source tables. Ссылайся на row ids и required actions. Канонические детали остаются в `Source Table Normalization`, `Test Design Decision Table`, `Coverage Obligation Table`, `Atomic Requirements Ledger`, `Package Test Design Plan` и `Coverage Gaps`.
