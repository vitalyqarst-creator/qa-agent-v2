# Production Global Rules

Этот файл — самодостаточная production-проекция глобальных правил полного
репозитория. Production bundle загружает её через
`production-instruction-loading.md`; корневой `AGENTS.md` полного development-
репозитория в bundle не входит.

## Источники и границы

- DOCX — source of truth, matching XHTML обязателен для machine-readable
  extraction. Без XHTML scope блокируется как `blocked-input`.
- PDF используется только для structural/visual cross-check; support и mockups
  не создают бизнес-правила.
- После выбора FT-пакета обязательный package-local `AGENT-NOTES.md`, если он
  существует.
- Не выдумывай поведение, поля, значения и интеграции. Неоднозначность оформляй
  как coverage gap с точным source locator.
- Справочник или фиксированный перечень извлекай полностью; конкретные
  тестовые данные должны быть source-backed и воспроизводимыми.

## Качество результата

- Один тест-кейс проверяет одну обязанность и имеет один основной ожидаемый
  результат; независимые atomic statements не склеиваются.
- Сохраняй точные requirement codes и полную трассировку к source assertions и
  obligations.
- Результат должен быть пригоден для ручного выполнения. Не выдавай UI-
  calibration candidate за исполнимый production-кейс.
- Старые test cases, benchmark/history и произвольные незарегистрированные файлы
  не являются model input.
- Reviewer получает буквальные элементы всего подтверждённого scope, включая
  строки без obligations, полный релевантный dictionary slice и только
  зарегистрированные hash-bound mockup images; evidence нельзя молча усекать.
- До reviewer runtime должен доказать bounded semantic parity каждого
  XHTML-backed literal элемента с уникальным DOCX occurrence и, при
  зарегистрированном PDF, с текстом конкретной PDF-страницы или минимального
  code-bounded диапазона страниц. DOCX occurrences сохраняют document order;
  все строки/ячейки одного XHTML table остаются в одном DOCX table, разные
  XHTML tables не склеиваются, а hash-bound section headings доказываются в
  предшествующем DOCX region. Для строк таблицы, которые PDF extractor
  разбивает между соседними страницами, допустимо разделить один cell-fragment
  на точные prefix/suffix-continuations: anchors ячеек сохраняют исходный порядок,
  все occurrences уникальны и не пересекаются, но suffix предыдущей страницы не
  обязан предшествовать anchors следующих колонок в extraction stream. Это
  semantic/structural cross-check, а не доказательство геометрии PDF-таблицы.
  Короткая ячейка, склеенная PDF extractor с соседями, допустима только если её
  raw substring точно заполняет пустой промежуток между доказанным окончанием
  предыдущего и началом следующего cell fragment; общее отключение token
  boundaries запрещено.
  Requirement codes внутри scope
  guard сверяются отдельно и с полными token boundaries; одинаковые коды не
  заменяют semantic row/boundary parity. Обычный accepted source receipt не
  заменяет parity.
- Полный зарегистрированный coverage-gap artifact и supporting cross-row
  bindings входят в pack буквально. Несовпадение gap IDs с registry блокирует
  запуск; temporary handling и downstream do-not-test правила обязательны.
- Primary coverage mapping сохраняет одного владельца на TC. Sibling obligation,
  реально использованный в setup, action или cleanup, публикуется отдельно как
  role-tagged design-support chain; finding обязан указать точный binding role.
- `reference-only` не означает `external-dynamic`: dependency provenance должен
  однозначно связывать `DICT-*` с `DEP-*`. Version/effective date извлекаются из
  квалифицированного source только при точной однозначной декларации; конфликт
  или неструктурированная декларация блокирует pack. SHA-256 source/content
  bindings фиксируются всегда.
- Fixture values закрытого справочника без отдельного fixture artifact допустимы
  только как точное подмножество полного qualified value set: каждое значение
  должно иметь exact-token binding хотя бы к одной зарегистрированной source row.
  External-dynamic/DaData fixture отдельно связывает dictionary/fixture identity,
  response snapshot, исходный verification receipt и lifecycle catalog row;
  reviewer получает точные request/expected response, а runtime не выполняет
  routine live revalidation.

## Исполнение

- Перед shell-командами используй сохранённый environment probe либо
  `scripts/probe_environment.py`; соблюдай UTF-8 policy и не предполагай shell.
- Этот downstream bundle не выполняет discovery и source qualification. До
  запуска ему передают независимо принятый manifest v4, compiler-v3 obligations,
  hash-bound semantic projection и зарегистрированную границу scope.
- Загружай только scenario `iteration.deterministic_production` из
  `production-instruction-loading.md`.
- `ft-agent run` работает только с закрытым schema-v2 config и новым immutable
  output directory. Canonical, source files и workflow state не изменяются.
- Допустимые успешные terminal statuses: `accepted-shadow` для полностью
  исполнимого набора и `accepted-with-calibration-pending`, если reviewer честно
  подтвердил calibration-кандидаты как `calibration-pending`. Второй статус
  всегда `promotion_eligible=false`; publication не входит в production run.
