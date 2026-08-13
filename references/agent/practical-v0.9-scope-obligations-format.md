# Формат `scope-obligations.json` practical v0.9

```json
{
  "schema_version": 1,
  "route_version": "practical-v0.9",
  "source_manifest_sha256": "<sha256 source-package-manifest.json>",
  "scope": {"id": "01", "slug": "9.1-menu", "title": "Меню"},
  "execution_setups": [
    {
      "id": "SETUP-ACTOR-001",
      "kind": "actor",
      "availability": "provided",
      "evidence": "Пользователь с доступом к модулю подготовлен в тестовом контуре."
    }
  ],
  "obligations": [
    {
      "id": "OBL-001",
      "source_anchor": "Раздел 9.1, Таблица 2, строка «Партнеры»",
      "statement": "В меню доступен пункт «Партнеры».",
      "risk_flags": [],
      "disposition": "active",
      "execution_contexts": [
        {
          "id": "CTX-OPEN-MENU",
          "label": "Открытие раздела из меню",
          "required_setup_kinds": ["actor"],
          "setup_ids": ["SETUP-ACTOR-001"]
        }
      ]
    }
  ],
  "clarifications": [
    {
      "id": "GAP-001",
      "gap_type": "ba-business-ambiguity",
      "source_anchor": "XHTML, раздел 9.1, Таблица 2, строка «Партнеры»",
      "source_statement": "В меню доступен пункт «Партнеры».",
      "description": "В источнике не определено условие доступности пункта.",
      "impact": "non-blocking",
      "affected_obligation_ids": ["OBL-001"],
      "question_to_analyst": "При каком условии пункт «Партнеры» должен быть доступен пользователю?",
      "requires_business_answer": true,
      "clarification_id": "CLR-001",
      "temporary_handling": "Не задавать условие доступа в тест-кейсе до ответа.",
      "status": "open"
    }
  ]
}
```

`statement` — точное, проверяемое русскоязычное утверждение ФТ. Здесь не фиксируются шаги, конкретные literals, предполагаемый UI oracle, matrix ID и TC ID: это принадлежит последующим этапам.

`visual_binding` — необязательная привязка уже видимого в изображении ФТ или
visual-only макете UI-контрола к обязательству. Если визуальный материал
разрешает только идентичность, подпись или расположение контрола, укажи
`source_anchor`, `element` и `location`; это уточняет воспроизводимые шаги
matrix/TC, но не создаёт бизнес-правило и не меняет ожидаемое поведение ФТ.

```json
{
  "source_anchor": "Рисунок 4 ФТ, правый верхний угол окна",
  "element": "кнопка с иконкой закрытия",
  "location": "правый верхний угол окна"
}
```

`execution_setups` — единый каталог предпосылок scope. Каждый `SETUP-*`
содержит `kind` (`actor`, `fixture`, `integration`, `initial-state`,
`environment` или `navigation`), `availability` (`provided` либо допустимый
статус исполнения) и воспроизводимое `evidence`. Каждый активный OBL обязан
содержать непустой `execution_contexts`. У `CTX-*` обязательны
русскоязычный `label`, `required_setup_kinds` (включая `actor`) и `setup_ids`.
Разные пользовательские потоки, например создание и редактирование, хранятся
разными контекстами и затем становятся отдельными строками matrix и TC.

Если в одном `CTX-*` недоступны несколько `SETUP-*`, первичный статус строки
определяется в порядке: `needs-future-clarification`, `blocked-observability`,
`needs-test-data`, `candidate-ui-calibration`. Следовательно, недоступный
актор, fixture, интеграция или исходное состояние не могут быть скрыты более
мягким статусом `candidate-ui-calibration`; все связанные `SETUP-*` всё равно
указываются в предпосылках matrix и TC.

Не сокращай смысл исходной нормы при нормализации: в `statement` сохраняй
контексты выполнения (`создание`, `редактирование` и т. п.), кванторы,
границы, условия и исключения. Если разные контексты или классы данных
порождают самостоятельный поток либо результат, создай отдельные `OBL-*`.

## Атомарность обязательств

Один `OBL-*` описывает ровно один предмет проверки и один основной наблюдаемый
результат. Если одно действие автозаполняет несколько полей, для каждого
целевого поля создай отдельный `OBL-*`: дефект автозаполнения одного поля не
должен быть скрыт общим обязательством. Для одного поля также разделяй
автозаполнение, ручной ввод/редактирование, валидацию и сохранение, если это
разные действия или результаты.

Исключение — значения одного закрытого списка одного элемента: их можно
оставить в одном `OBL-*`, только если исходное состояние, действие и ожидаемый
результат совпадают для каждого значения.

`risk_flags` используй только из: `status-transition`, `cross-field-rule`, `closed-dictionary`, `integration`, `authorization`, `exception-over-general-rule`, `mapping-table`, `temporal-rule`, `high-fan-out`, `high-risk`. Они запускают conditional matrix review.

## Gaps и вопросы к БА

`clarifications` — компактный реестр `GAP-*` текущего scope. Это не отдельная
матрица покрытия и не workflow state. Каждый gap обязан содержать:

- `id` формата `GAP-*`;
- `gap_type`: `ba-business-ambiguity`, `missing-source-definition`,
  `source-terminology-discrepancy`, `ui-calibration`,
  `external-scope-boundary`, `test-data-setup`, `ba-decision-required` или
  `ba-decision-supersedes-ft`;
- `source_anchor`, `source_statement`, `description` и `temporary_handling`;
- `impact`: `blocking` или `non-blocking`;
- `affected_obligation_ids` с существующими `OBL-*`;
- `status`: `open` или `resolved`.

Если для gap требуется продуктовое решение (`requires_business_answer: true`),
в том же запуске обязательно создай соседний
`scope-clarification-requests.md`. Укажи `question_to_analyst` и
`clarification_id` формата `CLR-*`; файл должен содержать связанную карточку
`### CLR-* — GAP-*` по каноническому формату вопросов к БА.

Не создавай вопрос к БА для подготовки тестовых данных, UI-наблюдения или
внешней границы scope, если продуктовое правило уже понятно. Такие gaps всё
равно остаются в `clarifications` и определяют статус будущего TC.

Перед открытым `ui-calibration` обязательно проверь все релевантные
изображения самого ФТ (включая встроенный рисунок), PDF и visual-only макеты.
У такого `GAP-*` добавь `visual_evidence_check`:

```json
{
  "outcome": "runtime-only",
  "checked_sources": ["Рисунок 4 ФТ: кнопка закрытия в правом верхнем углу"],
  "remaining_uncertainty": "Фактическая реакция UI после нажатия требует прогона."
}
```

`outcome` принимает только `no-visual-source`, `insufficient`, `conflict` или
`runtime-only`. `checked_sources` всегда непустой: при отсутствии изображения
в нём явно укажи, какие DOCX/XHTML/PDF/макеты были проверены и что нужного
экрана в них нет. Если материал уже определяет идентичность, подпись или
расположение, не создавай для этого `ui-calibration`; перенеси его в
`visual_binding` связанного `OBL-*`. В `ui-calibration` остаётся только
неизвестный runtime-признак или конфликт источников.

Перед созданием обязательств сравни наименование выбранного раздела с
наименованиями ближайших таблиц и утверждений ФТ. Если они называют разные
объекты, добавь `source-terminology-discrepancy`; рабочий объект scope выбирай
по содержательным утверждениям и явно укажи временную трактовку.

Не создавай `CLR-*` только из-за различия заголовка: если все ближайшие
нормативные таблицы и утверждения однозначно описывают один объект и один
набор функций, это non-blocking расхождение редакции; установи
`requires_business_answer: false`. Вопрос БА нужен лишь тогда, когда содержательные утверждения задают
конкурирующие объекты, поля или сценарии и поэтому меняется состав проверок.

Для утверждённого **scope-local** ответа БА, который не отменяет норму ФТ, не
редактируй старый gap молча. Добавь
утверждённый файл в `support/`, свяжи его с gap полями
`approved_clarification_path` и `approved_clarification_sha256`, обнови только
связанные `OBL-*`, затем установи `status: resolved` и
`resolution: approved-clarification:CLR-*`. Ответ привязывается к scope, а не
к общему `source-package-manifest.json`: пакетный manifest остаётся
неизменяемым и не делает stale не связанные scope. Полный scope и уже принятые
review заново не запускаются, если изменились только связанные обязательства и
их downstream matrix/TC.

Если утверждённое решение БА прямо отменяет либо изменяет норму ФТ, применяй
package-level контракт из `practical-v0.9-ba-decision-registry-format.md`:
сохрани исходный OBL для трассировки, укажи
`disposition: "superseded-by-ba-decision"` и `ba_decision_id`, свяжи resolved
gap через `approved-ba-decision:BA-DEC-*`, но не включай отменённый OBL в
матрицу, TC и независимое review. Если такого решения нет, используй
`ba-decision-required` с `requires_business_answer: true`; отсутствие вопроса
к БА является ошибкой структуры.

## Источники и итог этапа

`source_anchor` должен называть фактический носитель требования: например,
`XHTML, раздел ...`, `DOCX, Таблица ...` или `PDF, стр. ...`. Не сообщай, что
код или текст «утрачен» в источнике, пока не проверены DOCX, XHTML и доступный
PDF. Если ограничение вызвано извлечением, укажи ограничение извлечения, а не
отсутствие требования в источнике.

До создания `workflow-state.json` допускается только stdout-проверка:

```text
python scripts/validate_practical_obligations.py --ft-package-root <package> --source-package-manifest <manifest> --scope-obligations <scope-obligations> --require-clean
```

В отчете этапа называй её «проверкой структуры обязательств». Каноническая
`scoped validation` маршрута выполняется только после появления
`workflow-state.json` и замороженной матрицы; не называй предварительную
проверку успешной валидацией всего маршрута.
