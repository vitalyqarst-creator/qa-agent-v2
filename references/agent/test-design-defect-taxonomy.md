# Test Design Defect Taxonomy

Этот reference фиксирует повторяющиеся классы дефектов test-design, которые агент обязан учитывать в следующих writer/reviewer итерациях. Если новый дефект не попадает в существующий класс, добавь новый класс сюда, затем синхронизируй validator, tests/evals и skill instructions.

## Обязательные Классы

| defect_class | Симптом | Обязательное действие |
| --- | --- | --- |
| `unsupported-ui-mechanism` | TC ожидает конкретную UI-механику, которой нет в ФТ или подтвержденных материалах: символ не появляется, поле само очищается, кнопка disabled, точный текст ошибки, автоформатирование. | Убрать неподтвержденную механику из expected result или оформить `GAP-*` / `unclear`. Для numeric-only проверять факт принятия/отклонения класса символов, а не способ фильтрации, если способ не задан источником. |
| `format-mask-not-covered-by-numeric` | Маска формата покрыта только проверкой “только цифры” или значением без видимого шаблона. | Для `format-mask` создать отдельный obligation `mask-pattern-applied`; для default mask - `default-mask-visible`. Expected result должен наблюдаемо проверять шаблон/маску. |
| `numeric-only-class-gap` | Правило `только цифры` покрыто одним смешанным невалидным вводом или только буквой, без пробела, спецсимвола, десятичного разделителя и знака. | Создать `numeric-format` obligations для valid digits, reject letters, reject spaces, reject special chars, reject decimal separator, reject sign; непроверяемые классы оформить как узкие `GAP-*`. |
| `exact-length-class-gap` | Правило точной длины покрывает только `N` и `N-1` либо общий invalid length, но не проверяет `N+1`. | Создать `exact-length` obligations `exact-length-accepted`, `shorter-rejected`, `longer-rejected`; не объединять `N-1` и `N+1`. |
| `dictionary-closed-set-missing` | Source/support workbook задает справочник или фиксированный перечень значений, но `dictionary-inventory.md` отсутствует/неполон либо plan/TC проверяет только одно значение или не проверяет отсутствие лишних значений. | Извлечь значения в `dictionary-inventory.md`, сослаться на `DICT-*`, проверить отображение значений из справочника и closed-set поведение. Если закрытость перечня не следует из ФТ, оформить `GAP-*` / `unclear`, а не додумывать. |
| `action-created-optionality-gap` | Обязательные поля внутри блока, создаваемого кнопкой `Добавить ...`, трактуются как обязательность самого добавления блока; no-action branch отсутствует. | Разделить action branch, requiredness created-block fields и optional no-action branch; если обязательность добавления не описана, оформить `GAP-*`. |
| `repeatable-block-lifecycle-gap` | Повторяемый блок покрыт только первым добавлением/удалением, без проверки второго независимого блока, удаления одного из нескольких или удаления последнего. | Создать repeatable-block lifecycle obligations и TC/GAP для first add, second independent add, delete one preserves others, delete last, re-add after delete. |
| `checkbox-list-obligation-gap` | Checkbox/multi-select list проверен только как справочник значений, но не проверены обязательность, один выбор, множественный выбор или снятие выбора. | Создать checkbox-list obligations; source-backed missing branches покрыть TC, спорные reset/preserve branches оформить `GAP-*`. |
| `print-form-content-mapping-gap` | TC проверяет факт формирования печатной формы/документа и объявляет покрытым соответствие данных без source-backed mapping. | Разделить `print-form-generated` и `print-form-content-mapping`; content mapping покрывать только по source или фиксировать `GAP-*`. |
| `negative-transition-without-valid-fixture` | Негативная проверка через переход/кнопку (`Следующий шаг`, `Продолжить`) не задает валидное состояние всех остальных обязательных полей. | Указать именованный valid fixture или явно перечислить, что остальные обязательные поля заполнены валидно; иначе failure attribution ненадежен. |
| `coverage-metrics-missing` | Applicable coverage dimension есть в matrix/plan, но writer не посчитал obligations/classes/branches/transitions и их covered/gap status. | Создать `coverage-metrics.md` или linked split artifact; не передавать на review dimensions без измеримого coverage state. |
| `risk-model-too-flat` | High-risk atom имеет priority без `impact x likelihood`, residual risk decision или явного rationale; low-frequency/high-impact case понижен. | Обновить `risk-priority-map.md` по `risk-priority-map-format.md`; high impact не понижать из-за редкости, residual risk держать как visible gap. |
| `applicability-linked-tc-drift` | `Test-design Applicability Matrix` помечает dimension как covered, но связанный `TC-*` фактически проверяет другую dimension. | Проверить семантику linked TC: title, steps, data и expected result должны реально упражнять dimension строки. Иначе linked TC заменить или создать `GAP-*`. |
| `false-gap` | TDDT/ledger/plan отправляет в `gap_unclear` или `GAP-*` требование, где source уже задает наблюдаемый UI/API outcome: подсказку, сообщение, красную подсветку, подтверждение, переход, маску, справочник/теги, date-window boundary или другой pass/fail oracle. | Переклассифицировать проверяемую часть в `standalone_tc` / `covered_by_existing_tc`; оставить `GAP-*` только на реально недостающую часть. |
| `overbroad-gap` | Один `GAP-*` смешивает проверяемую часть и блокер вроде отсутствующей fixture, справочника, product catalog, backend artifact, статуса или test clock. | Split на executable coverage и узкий gap с точным `blocked_part`; обновить TDDT, Coverage Obligation Table, ledger, plan и coverage gaps. |
| `metadata-only-behavior` | Source-backed поведение с видимым результатом помечено `metadata_only`, потому что writer принял строку за structural context. | Разделить metadata и behavior: metadata оставить non-executable, behavior направить в TC coverage или узкий `GAP-*`. |
| `date-window-gap` | Возрастные/датовые окна с указанными границами и подсказками, например паспортные 14/20/45 лет, целиком отправлены в gap. | Разложить окна на boundary/equivalence obligations; `GAP-*` допустим только для тестовых часов, фикстуры или спорной boundary convention. |
| `semantic-compression` | Один atom/plan row/TC закрывает несколько независимых обязанностей системы, которые могут pass/fail отдельно. | Разложить на отдельные rows/TC или явно оформить scenario/recovery rationale, который не заменяет атомарные проверки. |
| `traceability-placeholder` | `Ссылка на ФТ`, `Трассировка`, ledger или matrix содержит placeholder `-`, `N/A`, пустой id slot или fake id между настоящими ссылками. | Удалить фиктивный элемент и оставить только реальные `ATOM-*`, requirement code, `SRC-*`, section/table/page/source quote/`DICT-*`; если id отсутствует, явно трассировать к source location без placeholder. |
| `source-rule-oracle` | Expected result заменен фразой `по правилу из источника`, `по правилу видимости из источника`, `согласно источнику`, `согласно ФТ` или аналогом. | Заменить на конкретный observable oracle: поле отображается/скрыто, значение отображается/не сохраняется, переход открыт/заблокирован, список содержит конкретные значения. |
| `generic-editability` | Editability TC использует шаги `Активировать элемент` / `Изменить значение на тестовое значение`, два sample значения без выбора одного, или expected result без literal нового значения. | Указать исходное и новое значение, конкретное действие для типа контрола и expected result с новым отображаемым значением; persistence выделять отдельным TC. |
| `derived-obligation-contamination` | Test-design-derived check (`v2 obligation`, exploratory/risk-derived/regression check) записан как обычный source-backed `ATOM-*` без `source_or_rule_ref`, defect class, coverage dimension или reviewer finding. | Явно пометить derivation и связь с source-backed обязанностью либо вынести как non-baseline exploratory/risk-derived check; не выдавать derived check за новую строку ФТ. |
| `template-postcondition-noise` | Read-only/list-composition/visibility TC содержит шаблонное `Вернуть измененные данные...`, хотя steps не меняют данные. | Заменить на `Не требуются` или конкретное cleanup-действие, если TC действительно меняет состояние. |

## Feedback Loop

1. Зафиксируй дефект как `finding` с конкретным `defect_class`, source evidence и affected artifacts.
2. Обнови этот taxonomy, если класс новый или текущего описания недостаточно.
3. Добавь или расширь validator rule, если дефект можно надежно ловить статически.
4. Добавь regression test/eval candidate, построенный на реальном сбое.
5. Обнови writer/reviewer instructions только ссылкой на canonical reference, без дублирования длинных правил.
6. Прогони `python scripts/run_tests.py` и `python scripts/run_tests.py --suite architecture`.

## Severity

- `error`: дефект делает sign-off недостоверным: неподтвержденное поведение, пропущенная обязательная ветка, неверная связь matrix -> TC, отсутствие valid fixture для негативной transition-проверки.
- `warning`: дефект снижает полноту или диагностичность, но не делает уже написанный TC ложным сам по себе.
- `info`: улучшение структуры или явности, не влияющее на pass/fail.
