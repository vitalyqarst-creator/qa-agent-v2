# Scope Decomposition Policy

Этот документ задает каноническое правило декомпозиции большого или полного ФТ на scope-ы перед writer/reviewer loop.

## Цель

- не передавать writer-у слишком широкий и неоднородный scope;
- сделать scope единицей session-based review-cycle и canonical test-case file;
- отделить внешние scope-ы от внутренних рабочих пакетов writer-а.

## Основное Правило

Если пользователь просит работать с большим ФТ, всем ФТ или несколькими разделами ФТ, `ft-scope-analyzer` сначала должен сформировать карту внешних candidate scope-ов.

Внешние scope-ы выделяются:

1. по разделам ФТ;
2. по подразделам, если раздел объемный или неоднородный;
3. по самостоятельным функциональным блокам внутри подраздела, если один подраздел смешивает разные test-design domains.

Только после выбора или подтверждения одного внешнего scope агент создает `scope-contract.md` для этого scope и, при необходимости, разбивает его на `Внутренние Рабочие Пакеты`.

## Внешний Scope

Внешний scope — это единица процесса:

- отдельный `scope_slug`;
- отдельная numbered handoff-папка `NN-<scope-slug>/`;
- отдельный canonical test-case file `test-cases/<section-id>-<scope-slug>.md`;
- отдельный session-based review-cycle каталог `work/review-cycles/<scope-slug>/`.

Внешний scope должен быть достаточно узким, чтобы writer мог построить atomic ledger, test-design matrix, тест-кейсы и self-check без смешивания независимых доменов.

## Внутренний Рабочий Пакет

Внутренний рабочий пакет — это рабочий план внутри уже подтвержденного внешнего scope.

Он не является заменой внешнего scope и не создает отдельный canonical test-case file сам по себе.

Используй внутренние рабочие пакеты для группировки внутри scope, например:

- свойства полей формы;
- действия раздела;
- зависимости полей;
- валидации;
- интеграционные эффекты;
- статусные ветки;
- таблицы/история;
- печатные формы;
- файлы.

## Когда Нужен `agent-proposed-scope`

Используй `agent-proposed-scope`, если:

- пользователь просит `все ФТ`, `все разделы`, `полный набор`, `весь документ`;
- выбранный раздел содержит несколько разных test-design domains;
- раздел содержит и UI-поля, и действия, и интеграции, и статусы, и печатные формы;
- source block слишком большой для надежного writer-pass;
- expected review-cycle по одному scope будет трудно довести до sign-off.

В этом режиме результатом должны быть `scope-options.md`, `scope-selection-prompts.md` и `workflow-state.yaml` в контейнере `00-<container-slug>/`.

Не создавай `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`, пока не выбран один candidate scope.

## Когда Допустим Единый Внешний Scope

Единый внешний scope допустим только если выполняется хотя бы одно условие:

- ФТ или выбранный раздел небольшой и однородный;
- все требования относятся к одному test-design domain;
- пользователь явно подтвердил, что хочет один широкий scope после предупреждения о рисках.

Если широкий scope все же подтвержден, `scope-contract.md` должен содержать:

- `Complexity decision: single_scope_with_internal_packages`;
- обоснование, почему внешний split не выбран;
- внутренние рабочие пакеты;
- blocking `coverage gaps`, если отдельные домены нельзя честно покрыть в одном writer-pass.

## Запрещенный Паттерн

Не создавай внешний scope вида `all-sections`, `all-sections-without-bp`, `whole-ft` или аналогичный как стандартный старт для большого ФТ.

Такой scope допустим только как явно подтвержденное исключение. По умолчанию это дефект scope analysis, потому что:

- смешивает независимые функциональные области;
- затрудняет traceability;
- повышает риск фальшивого покрытия gaps;
- делает review-cycle слишком крупным для качественного sign-off.

## Рекомендуемый Порядок

1. `ft-source-locator` выбирает FT-пакет и источники.
2. `ft-scope-analyzer` в режиме `agent-proposed-scope` строит карту внешних scope-ов.
3. Пользователь выбирает один candidate scope или подтверждает рекомендованный первый scope.
4. `ft-scope-analyzer` в режиме `manual-scope` создает `scope-contract.md` для выбранного scope.
5. Внутри `scope-contract.md` добавляются внутренние рабочие пакеты, если выбранный scope неоднородный.
6. Только после этого стартует writer или writer/reviewer iteration.

## Критерии Разбиения

При выборе внешних scope-ов учитывай:

- структуру разделов и подразделов ФТ;
- независимость пользовательского сценария;
- отдельные UI-разделы или формы;
- отдельные статусные модели;
- отдельные интеграционные процессы;
- отдельные печатные формы;
- отдельные таблицы/истории/реестры;
- различие test-design domains;
- объем исходного блока и надежность парсинга.

## Минимальная Карта Scope-ов

Для каждого candidate scope в `scope-options.md` должны быть указаны:

- `Scope Order`;
- `Scope Slug`;
- `Stage Handoff Dir`;
- `Title`;
- `Source Path`;
- что входит;
- что не входит;
- почему это отдельный scope;
- примерная сложность;
- риски / coverage gaps;
- рекомендуемый следующий шаг.

## Связанные References

- `references/agent/scope-options-format.md`
- `references/agent/scope-contract-format.md`
- `references/agent/stage-handoff-model.md`
- `references/agent/workflow-state-format.md`
- `references/agent/writer-output-format.md`
