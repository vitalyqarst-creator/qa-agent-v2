# Формат `scope-clarification-requests.md`

`scope-clarification-requests.md` — conditional companion-артефакт к gaps
текущего scope для вопросов пользователю или аналитику и фиксации ответов по
конкретным coverage gaps.

## Назначение

- дать пользователю явное место для ответов на вопросы из `scope-coverage-gaps.md`;
- сохранить связь каждого вопроса с конкретным `GAP-*`;
- показать краткую привязку вопроса к конкретному утверждению ФТ без необходимости открывать полный gaps-файл;
- не смешивать стабильную карту gaps с интерактивными ответами;
- не превращать ответы пользователя в неявную замену текста ФТ.

## Расположение

Для `practical-v0.9`:

- `fts/<domain>/<ft>/work/practical-v0.9/<scope-slug>/scope-clarification-requests.md`
  — companion к `scope-obligations.json` текущего scope;
- `fts/<domain>/<ft>/support/<scope-slug>-approved-clarifications.md`
  — утверждённый ответ, повторно используемый как hash-bound evidence только
  для связанных `GAP-*`/`OBL-*`. Его путь и SHA-256 записываются в
  `scope-obligations.json`; пакетный `source-package-manifest.json` не
  изменяется, чтобы не делать stale не связанные scope.

Для legacy route:

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-clarification-requests.md`
  — рабочий companion к gaps текущего handoff;
- `fts/<ft-slug>/support/<source-version>/<scope-slug>-approved-clarifications.md`
  — переиспользуемый package/source input для новых clean runs, если в
  файле остались только записи `answered` с production-ready
  authority/type и стабильными `CLR-*`.

Package-level файл не является workflow state и не заменяет gaps текущего
run. В source registry его всегда регистрируют с `role = approved-clarification`
и `manifest_binding = approved-clarification`, а не как обычный support.

## Когда создавать

Для `practical-v0.9` создавай файл в том же запуске, если в
`scope-obligations.json` есть хотя бы один `GAP-*` с
`requires_business_answer: true`. Для каждого такого gap должна быть ровно
одна карточка `CLR-*`, связанная заголовком `### CLR-* — GAP-*`. Gaps о UI,
наблюдаемости, подготовке данных и границах будущего scope не становятся
вопросами к БА, пока для них не требуется продуктовое решение.

Для legacy route:

- создавай файл всегда, если в `scope-coverage-gaps.md` есть хотя бы один `GAP-*`;
- для каждого gap с `Needs User Input: yes` добавляй минимум одну карточку в `Clarification Requests`;
- если по gap ответ пользователя не нужен, не добавляй карточку-вопрос, но перечисли такой gap в `Gaps Without Requests` с причиной;
- если gaps нет, файл можно не создавать.
- не создавай вопрос БА для тестовой учетной записи, объекта, записи, fixture или роли с уже определенными source правами, которую подготовит тестировщик/автоматизатор: укажи точные свойства подготовки в `needs-test-data` у зависимых TC.

## Классификация неизвестности в practical route

Перед созданием `CLR-*` классифицируй каждую неизвестность в
`scope-brief.md` одним из четырёх типов:

| Тип | Где фиксировать | Когда уместен |
| --- | --- | --- |
| `ba-business-ambiguity` | Эта карточка `CLR-*` | В уже входящем в scope тексте ФТ не определено продуктовое правило или разрешены несколько несовместимых трактовок. |
| `ui-calibration` | `scope-brief.md`, candidate UI point | Бизнес-правило известно, но для исполнения нужно наблюдаемое поведение интерфейса: экран, элемент, сообщение, подсветка, порядок действий. |
| `external-scope-boundary` | `scope-brief.md`, границы scope | ФТ ссылается на будущий или внешний документ, не входящий в переданный пакет. Это не вопрос БА по текущему scope. |
| `test-data-setup` | `scope-brief.md`, `Зависимости от тестовых данных` | Не хватает учётной записи, роли с уже заданными правами, объекта, состояния, fixture или другого условия подготовки. |

В `scope-clarification-requests.md` допускаются только карточки с
`request_kind: ba-business-ambiguity`. Не создавай `CLR-*` для выбора экрана,
видимого UI-признака, способа подготовки тестовых данных или содержания
будущего ФТ. Эти записи не требуют решения БА и не должны раздувать список
вопросов.

## Обязательные секции

- `## Контекст`
- `## Как Заполнять`
- `## Clarification Requests`
- `## Gaps Without Requests`
- `## Правила Использования Ответов`

## Обязательные поля записи

- `clarification_id`
- `gap_id`
- `request_kind`
- `scope_slug`
- `requirement_codes`
- `related_ft_reference`
- `related_obligation_ids`
- `source_quote`
- `question`
- `needed_for`
- `blocking`
- `requested_from`
- `authority`
- `user_response`
- `response_status`
- `response_type`
- `updated_at`

## Правила полей

- `clarification_id` — стабильный уникальный `CLR-*`; одна точная версия ответа
  имеет один id.
- `gap_id` — идентификатор из `scope-coverage-gaps.md`, например `GAP-001`.
- `request_kind` = `ba-business-ambiguity` — обязательная классификация
  карточки в practical route. Другие типы неизвестности фиксируются в
  `scope-brief.md` и не становятся вопросом БА.
- `scope_slug` — точный scope, для которого получен ответ.
- `requirement_codes` — один или несколько точных кодов требований через `;`.
- `related_ft_reference` — краткая ссылка на утверждение ФТ: раздел, `GSR`, таблица/строка, поле/условие, `ATOM-*` или страница PDF.
- `related_obligation_ids` — связанные `OBL-*` для `practical-v0.9`; в legacy
  route допускается `-`, если обязательства ещё не материализованы.
- `source_quote` — конкретный текст из ФТ/source, который вызвал вопрос.
  Если вопрос возник из нескольких строк, укажи короткие цитаты с кодами
  требований. Это должен быть текст источника, а не пересказ агента.
- `question` — конкретный вопрос на русском языке, на который можно ответить
  без чтения всей истории чата. Не используй внутренние агентские термины
  вроде `exact`, `observable`, `branch`, `fixture`, `production-ready`, если
  это не буквальная цитата из источника. До вопроса проверь DOCX/XHTML/PDF и
  support текущего пакета; спрашивай о продуктовом решении, а не о тестовой
  подготовке.
- `needed_for` — что станет возможным после ответа: полное покрытие требования, снятие ambiguity, уточнение тестовых данных.
- `blocking` = `yes | no`; должно соответствовать impact gap-а.
- `requested_from` = `user | analyst | product-owner | developer | unknown`.
- `authority` = `user | analyst | product-owner`; это фактический источник
  полученного ответа. Нельзя записывать пользователя как analyst/product-owner.
- `user_response` — текст ответа из блока `Ответ БА`. До заполнения оставляй `-`.
- `response_status` = `unanswered | answered | superseded | rejected`;
  служебное поле, заполняется агентом после получения ответа.
- `response_type` = `not-provided | working-assumption | user-confirmed |
  analyst-confirmed | product-confirmed | rejected`; служебное поле,
  заполняется агентом.
- `updated_at` — дата обновления в формате `YYYY-MM-DD` или `-`; служебное
  поле, заполняется агентом.

Production-ready semantics разрешено строить только из записи со
`response_status = answered` и согласованной парой authority/type:
`user/user-confirmed`, `analyst/analyst-confirmed` или
`product-owner/product-confirmed`. `working-assumption`, `rejected`,
`superseded`, `unanswered` и `not-provided` не являются утверждённым evidence.

## Использование утвержденного ответа в practical-v0.9

После получения ответа агент не подменяет им ФТ и не помечает gap закрытым
одним редактированием этого файла. Он должен:

1. создать или обновить `support/<scope-slug>-approved-clarifications.md`;
2. в `scope-obligations.json` установить у связанного gap `status: resolved`,
   `resolution: approved-clarification:CLR-*`,
   `approved_clarification_path` и `approved_clarification_sha256`;
3. обновить только связанные `OBL-*`, а затем их строки matrix и TC, если они
   уже существуют.

Если ответ не подтвержден или противоречит основному ФТ, gap остается `open`;
его нельзя использовать как источник новой ожидаемой реакции системы.

## Достаточность и детализация вопроса

Вопрос к БА должен быть самодостаточным: человек должен понять его без чтения
истории, gaps-файла или внутренних artifact-ов агента.

- Если один `GAP-*` затрагивает несколько независимых source assertions,
  requirement codes, полей, validation classes, triggers или expected oracles,
  не задавай один umbrella-вопрос вида «какой UI-отклик?».
- Делай отдельный `CLR-*` на каждый независимый вопрос. Если оставляешь одну
  карточку, `question` и `**Вопрос:**` обязаны содержать нумерованный checklist.
- Для каждого подпункта указывай source anchor, поле/условие и что неизвестно:
  trigger, значение, видимый UI/API/DB artifact, сообщение, блокировка,
  сохранение/несохранение или boundary.
- Не смешивай requiredness, negative validation, dictionary/fixture,
  integration, visibility/editability и cleanup semantics в один вопрос.
- При intake закрывай только явно отвеченные подпункты. Остаток остаётся
  residual `GAP-*` или получает новый `CLR-*`.
- Если один ответ применяется к нескольким подпунктам, сохрани coverage map в
  `scope-coverage-gaps.md` и `source-assertions.json`.

## Рекомендуемый шаблон

```md
## Контекст

- `scope_slug`: `...`
- Coverage gaps: `scope-coverage-gaps.md`

## Как Заполнять

- БА заполняет только блок `Ответ БА`.
- `response_status`, `response_type` и `updated_at` заполняет агент после получения ответа.
- Не удаляйте `clarification_id`, `gap_id`, scope, ссылки и вопрос.
- Если ответ заменен более новым, агент установит старой карточке `response_status = superseded` и добавит новую карточку с тем же `gap_id`.
- Если вопрос содержит нумерованные подпункты, ответьте по каждому подпункту отдельно; если по подпункту нет подтвержденной информации, напишите это явно.

## Clarification Requests

### CLR-001 — GAP-001

```yaml
clarification_id: CLR-001
gap_id: GAP-001
request_kind: ba-business-ambiguity
scope_slug: application-search
requirement_codes: GSR 1
related_ft_reference: GSR 1, поле ..., ATOM-001
related_obligation_ids: OBL-001
source_quote: GSR 1. Поле должно заполняться после сохранения.
question: Какое точное значение получает поле после сохранения?
needed_for: Полное покрытие GSR 1
blocking: no
requested_from: user
authority: user
response_status: unanswered
response_type: not-provided
updated_at: -
```

**Текст из ФТ:** GSR 1. Поле должно заполняться после сохранения.

**Вопрос:** Какое точное значение получает поле после сохранения?

**Что станет возможно после ответа:** Полное покрытие `GSR 1`.

#### Ответ БА (`user_response`)

```text
-
```

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| GAP-002 | `GSR 2`, условие `...` | Ответ пользователя не нужен: gap фиксирует ограничение тест-дизайна, writer должен не домысливать правило. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной ФТ.
- В source-first production workflow ответ сначала регистрируется в manifest v4
  как typed `clarifications[]`, hash-связывается через dedicated evidence role
  `approved-clarification` и привязывается к точным assertion clauses. Writer и
  reviewer получают его только из digest-bound compact projection, а не из
  свободного prose.
- Для использованного ответа соответствующий GAP остаётся в coverage-gaps
  artifact со `status = resolved` и точным
  `resolution = approved-clarification:<CLR-ID>`. В нём не остаётся активной
  ASSERT/ATOM/OBL execution chain.
- Один ответ, одновременно относящийся к нескольким кодам, остаётся одним
  `CLR-*`. Каждый assertion binding перечисляет только собственные локальные
  `requirement_codes`, а объединение всех bindings обязано в точности покрыть
  code set clarification.
- Изменение exact answer, authority, type, date, scope, gap, requirement codes
  или bytes файла делает manifest и независимый receipt stale.
- `working-assumption` можно использовать только как ограниченную рабочую гипотезу и обязательно отмечать в assumptions / coverage gaps.
- Если ответ противоречит основному ФТ, приоритет остается у основного ФТ; противоречие фиксируется как gap.
```

## Что не включать

- полный текст coverage gaps;
- reviewer findings;
- writer response;
- process-status этапа вместо `workflow-state.yaml`;
- ответы без привязки к `GAP-*`.
