# Use-case использования FT Test Case Agent для написания тест-кейсов

Версия: 1.0

Документ описывает типовой процесс работы пользователя с FT Test Case Agent: от подготовки папки с функциональными требованиями до получения согласованного набора тест-кейсов и, при необходимости, automation-ready версии. Это сценарная инструкция, а не замена каноническим правилам проекта. Детальные форматы и политики остаются в `AGENTS.md`, `skills/` и `references/`.

## Цель

Показать последовательность действий пользователя и ответов агента при создании тест-кейсов по одному FT-пакету (папке внутри `qa-agent/fts/`, где хранятся материалы по одному функциональному требованию или группе связанных требований).

Рекомендуемый production-ready путь:

```text
ft-source-locator -> ft-scope-analyzer -> ft-test-case-iteration -> ft-ui-automation-prep
```

Где:

- `ft-source-locator` (режим агента для поиска и подтверждения нужного FT-пакета, основного файла ФТ, support-файлов и макетов);
- `ft-scope-analyzer` (режим агента для определения scope - границ анализа: конкретного раздела, блока, сценария или набора требований);
- `ft-test-case-iteration` (режим полного writer-reviewer цикла: написание тест-кейсов, review, исправление findings и повторный review при необходимости);
- `ft-ui-automation-prep` (режим подготовки отдельной automation-ready версии после reviewer sign-off и проверки в реальном UI).

## Входная структура FT-пакета

Пример FT-пакета:

```text
qa-agent/
  fts/
    ft-2-obshchaya-funkcionalnost/
      source/
        FT-2-obshchaya-funkcionalnost.docx
        FT-2-obshchaya-funkcionalnost.pdf
      support/
        ...
      mockups/
        ...
      AGENT-NOTES.md
```

Назначение папок:

- `source` (папка с основным текстом ФТ в `.docx` и/или `.pdf`);
- `support` (папка со вспомогательными документами: справочниками, приложениями, пояснениями);
- `mockups` (папка с макетами экранов и форм; макеты помогают интерпретировать ФТ, но не заменяют текст требований);
- `AGENT-NOTES.md` (необязательный файл с package-specific контекстом, который агент обязан учитывать после выбора FT-пакета).

## Основные термины

| Термин | Расшифровка |
|---|---|
| FT-пакет | Папка внутри `qa-agent/fts/`, где хранятся материалы по одному ФТ. |
| ФТ | Функциональные требования. Канонический источник поведения системы. |
| scope | Границы анализа: конкретный раздел, блок, сценарий или набор требований, по которому пишутся тест-кейсы. |
| candidate scope | Предложенный агентом вариант scope, который пользователь должен выбрать или уточнить. |
| handoff | Передача контекста между этапами через файлы, чтобы следующий этап можно было запустить без истории чата. |
| artifact / артефакт | Созданный или обновленный файл результата: например `source-selection.md`, `scope-contract.md`, файл тест-кейсов. |
| coverage gaps | Пробелы покрытия, неоднозначности или вопросы по требованиям, которые нельзя закрывать догадками. |
| review-cycle | Session-based цикл проверки: writer пишет или исправляет тест-кейсы, reviewer проверяет покрытие, структуру и test design в отдельных сессиях. |
| signed-off | Статус, при котором review-cycle завершен без блокирующих findings. |
| automation-ready | Отдельная версия тест-кейсов, подготовленная после UI-проверки для дальнейшей автоматизации. |

## Сценарий работы

| Шаг | Действие пользователя | Ответ / действие агента | Созданные или обновленные артефакты |
|---:|---|---|---|
| 0 | Пользователь создал в `qa-agent/fts/` папку по конкретному ФТ, например `ft-2-obshchaya-funkcionalnost`. | Агент пока не запускается. Это подготовка FT-пакета. | `fts/ft-2-obshchaya-funkcionalnost/` |
| 1 | Внутри FT-пакета пользователь создал папки `source`, `support`, при необходимости `mockups`. В `source` добавил ФТ в `.docx` и `.pdf`; в `support` - вспомогательные документы; в `mockups` - макеты форм. | Агент позже проверит, что основной текст ФТ лежит в `source`, а макеты используются только как вспомогательный источник. Если макеты лежат в `support`, агент может их учесть, но рекомендуемая структура - отдельная папка `mockups`. | `source/*.docx`, `source/*.pdf`, `support/*`, `mockups/*` |
| 2 | Пользователь пишет: `Найди FT-пакет ft-2-obshchaya-funkcionalnost, определи основное ФТ и подготовь handoff к анализу scope.` | Агент запускает `ft-source-locator` (режим поиска и подтверждения нужного FT-пакета, основного ФТ, support-файлов и макетов). | Пока идет анализ входных файлов; итоговые артефакты создаются на следующем шаге. |
| 3 | Пользователь ожидает подтверждения, что агент выбрал правильный FT-пакет. | Агент сообщает выбранный FT-пакет, основной документ ФТ, наличие PDF-версии для сверки структуры, найденные support/mockups и наличие `AGENT-NOTES.md`. Если выбор неоднозначен, агент фиксирует кандидатов и причины неопределенности. | `work/stage-handoffs/00-<scope-or-container>/source-selection.md`, `work/stage-handoffs/00-<scope-or-container>/workflow-state.yaml` |
| 4 | Пользователь пишет: `Предложи, какими частями лучше покрывать это ФТ тест-кейсами.` | Агент запускает `ft-scope-analyzer` в режиме `agent-proposed-scope`: сначала предлагает внешние scope-ы по разделам/подразделам ФТ согласно `scope-decomposition-policy.md`. Тест-кейсы на этом шаге не пишутся. | `scope-options.md`, `scope-selection-prompts.md`, обновленный `workflow-state.yaml` |
| 5 | Пользователь выбирает один candidate scope (предложенный вариант границ анализа), например `раздел 2.1 Общая функциональность`. | Агент принимает выбор, но не начинает писать тест-кейсы до фиксации scope contract (контракта границ анализа). | Обычно создается только ответ в чате с подтверждением выбранного scope. |
| 6 | Пользователь пишет: `Зафиксируй выбранный scope и подготовь входы для написания тест-кейсов с review-cycle.` | Агент запускает `ft-scope-analyzer` в режиме `manual-scope` (режим, где пользователь уже указал scope, а агент проверяет и фиксирует его границы). Агент не расширяет scope без явного решения пользователя. | `scope-contract.md`, `scope-coverage-gaps.md`, `prompt.scope-to-writer.md`, `prompt.scope-to-iteration.md`, обновленный `workflow-state.yaml` |
| 7 | Пользователь просматривает `coverage gaps` (пробелы покрытия и неоднозначности требований), если агент их нашел. | Агент объясняет, какие конкретные утверждения ФТ затронуты каждым gap-ом, чего не хватает для тестирования и какие вопросы нужно уточнить у аналитика или владельца продукта. Агент не додумывает поведение системы. | `scope-coverage-gaps.md`, `scope-clarification-requests.md`, если gaps есть |
| 8 | Если есть вопросы, пользователь или аналитик отвечает на них. Если вопросов нет, пользователь просит продолжить. | Агент использует только подтвержденные ответы. Ответы типа working assumption (рабочее предположение) не считаются равными тексту ФТ и должны быть явно помечены как assumption. | Обновленный `scope-clarification-requests.md`, если были gaps |
| 9 | Пользователь пишет: `Запусти полный цикл написания и review тест-кейсов по выбранному scope.` | Агент запускает `ft-test-case-iteration` (режим полного writer-reviewer цикла). На старте проверяет обязательные входы: `scope-contract.md`, gaps, prompt-файлы и `workflow-state.yaml`. | Обновленный `workflow-state.yaml`; далее создаются writer/reviewer артефакты |
| 10 | Пользователь ожидает первый набор тест-кейсов. | Writer-сессия строит atomic requirements ledger, затем пишет тест-кейсы. Один тест-кейс покрывает одну проверку и один основной ожидаемый результат. | `test-cases/<section-id>-<scope-slug>.md`, snapshot `work/review-cycles/<scope-slug>/versions/r1-writer-draft/`, prompt under `work/review-cycles/<scope-slug>/prompts/` |
| 11 | Пользователь ожидает review первого набора. | Reviewer-сессия проверяет трассировку к ФТ, атомарность, полноту покрытия, структуру и test design. Если есть проблемы, агент фиксирует findings и возвращает набор writer-у через `cycle-state.yaml`. | `work/review-cycles/<scope-slug>/outputs/round-1-findings.md`, `round-1-traceability-matrix.md`, `round-1-traceability-matrix.xlsx`, при необходимости prompt under `work/review-cycles/<scope-slug>/prompts/` |
| 12 | Если review нашел blocking findings, пользователь просит исправить их в рамках того же scope. | Writer-часть агента исправляет канонический файл тест-кейсов, не расширяя scope и не создавая конкурирующую основную версию. Затем фиксирует ответ на findings. | Обновленный `test-cases/<section-id>-<scope-slug>.md`, `round-1-writer-response.md`, snapshot `<scope-slug>.round-1-writer.md`, `prompt.writer-to-reviewer.round-2.md` |
| 13 | Пользователь ожидает повторный review. | Reviewer-часть агента выполняет второй review. Если блокирующих проблем нет, набор получает `signed-off`. Если после второго review остаются blocking findings или gaps, цикл завершается статусом `round-cap-reached` (достигнут лимит review rounds). | `round-2-findings.md`, `round-2-traceability-matrix.md`, `round-2-traceability-matrix.xlsx`, при sign-off - `prompt.reviewer-to-ui-prep.md` |
| 14 | Пользователь получает итог writer-reviewer цикла. | Runner и stage sessions обновляют `cycle-state.yaml`; агент сообщает итоговый статус: `signed-off` или `round-cap-reached`. | `work/review-cycles/<scope-slug>/cycle-state.yaml`, `codex-session-map.yaml`, terminal snapshot under `versions/` |
| 15 | Если нужен только ручной набор, пользователь завершает работу. Если нужна подготовка к автоматизации, пользователь пишет: `Подготовь automation-ready версию по signed-off набору. Runtime URL: ...` | Агент проверяет, что review-cycle завершен со статусом `signed-off`. Без `signed-off` запуск `ft-ui-automation-prep` некорректен: UI-проверка не заменяет review требований. | Проверяются `cycle-state.yaml`, `workflow-state.yaml`, `prompt.reviewer-to-ui-prep.md` |
| 16 | Пользователь предоставляет runtime URL, доступ к приложению и, при наличии, UI notes. | Агент запускает `ft-ui-automation-prep` (режим подготовки automation-ready версии после UI-проверки), проверяет `AGENT-NOTES.md` и `work/ui-automation-prep/UI-AGENT-NOTES.md`, если они есть. | Начальная версия `test-cases/automation-ready/<section-id>-<scope-slug>.md` |
| 17 | Пользователь ожидает UI-проверку. | Агент проходит signed-off кейсы в реальном UI через Playwright, собирает evidence (свидетельства проверки: screenshots, traces, logs) и фиксирует расхождения между ФТ и UI, если они есть. UI не становится новым источником требований. | `work/ui-automation-prep/<scope-slug>/ui-validation-report.md`, `ui-evidence-index.md`, `output/playwright/<scope-slug>/*` |
| 18 | Пользователь получает automation-ready результат. | Агент обновляет отдельную automation-ready версию. Baseline FT-first набор в `test-cases/` не перезаписывается. | `test-cases/automation-ready/<section-id>-<scope-slug>.md`, обновленный `workflow-state.yaml` |

## Пример пользовательских запросов по этапам

### 1. Найти FT-пакет

```md
Найди FT-пакет `ft-2-obshchaya-funkcionalnost`, определи основное ФТ,
support-файлы и макеты. Подготовь handoff к scope analysis.
Если есть несколько кандидатов или не хватает PDF, зафиксируй это как ограничение.
```

### 2. Предложить scope

```md
FT-пакет: `fts/ft-2-obshchaya-funkcionalnost`
Этап: `ft-scope-analyzer`
Режим scope: `agent-proposed-scope`
Предложи разбиение ФТ на candidate scope для поэтапного покрытия тест-кейсами.
```

### 3. Зафиксировать выбранный scope

```md
FT-пакет: `fts/ft-2-obshchaya-funkcionalnost`
Этап: `ft-scope-analyzer`
Режим scope: `manual-scope`
Scope: раздел 2.1 Общая функциональность
Нужны `scope-contract.md`, `scope-coverage-gaps.md`,
`prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md`.
Scope не расширять.
```

### 4. Запустить writer-reviewer цикл

```md
Запусти `ft-test-case-iteration` для выбранного scope.
Нужен полный цикл writer -> reviewer -> writer -> reviewer.
Initial draft должен идти через atomic-ledger-first workflow.
Для traceability matrix создай Markdown и XLSX companion.
Обнови `workflow-state.yaml` и все handoff-артефакты.
```

### 5. Подготовить automation-ready версию

```md
Для scope `<scope-slug>` выполни `ft-ui-automation-prep`.
Проверь `workflow-state.yaml` и `prompt.reviewer-to-ui-prep.md`.
Runtime URL: `<url>`
Если есть `UI-AGENT-NOTES.md`, используй его.
Нужны automation-ready версия, UI report и evidence index.
```

## Ожидаемая структура результатов

После полного процесса в FT-пакете ожидается структура такого вида:

```text
fts/ft-2-obshchaya-funkcionalnost/
  source/
    FT-2-obshchaya-funkcionalnost.docx
    FT-2-obshchaya-funkcionalnost.pdf
  support/
  mockups/
  test-cases/
    <section-id>-<scope-slug>.md
    automation-ready/
      <section-id>-<scope-slug>.md
  work/
    stage-handoffs/
      00-<container-or-scope>/
        source-selection.md
        workflow-state.yaml
        scope-options.md
        scope-selection-prompts.md
        scope-contract.md
        scope-coverage-gaps.md
        scope-clarification-requests.md
        prompt.scope-to-writer.md
        prompt.scope-to-iteration.md
        prompt.reviewer-to-ui-prep.md
    review-cycles/
      <scope-slug>/
        cycle-state.yaml
        codex-session-map.yaml
        prompts/
        outputs/
        versions/
    ui-automation-prep/
      <scope-slug>/
        ui-validation-report.md
        ui-evidence-index.md
```

## Контрольные правила

- Не смешивать тест-кейсы разных FT-пакетов.
- Не писать тест-кейсы до фиксации scope.
- Не закрывать неоднозначности догадками: фиксировать их в `coverage gaps`.
- Приоритет имеет текст ФТ, а не макет.
- Каждый тест-кейс должен быть атомарным.
- Канонический файл тест-кейсов хранится в `test-cases/<section-id>-<scope-slug>.md`.
- Review-cycle ограничен двумя semantic review rounds.
- `automation-ready` версия создается отдельно и не перезаписывает baseline FT-first набор.
