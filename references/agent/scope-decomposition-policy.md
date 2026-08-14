# Scope Decomposition Policy

Этот документ задаёт правило декомпозиции большого ФТ на внешние scope перед
запуском practical route v0.9.

## Цель

- не смешивать независимые функциональные области в одной matrix и одном
  наборе тест-кейсов;
- сделать scope единицей obligations, matrix, двух независимых review и
  canonical test-case file;
- получать вопросы БА до test design, а не после выпуска кейсов.

## Основное правило

Если пользователь просит работать с большим ФТ, всем документом или
несколькими разнородными разделами, `ft-scope-analyzer` сначала строит карту
внешних candidate scope. Scope выделяются по разделам, подразделам или
самостоятельным функциональным блокам, когда они имеют разные объекты,
действия, статусы, интеграции или primary expected results.

Только после выбора одного внешнего scope запускается practical route v0.9.
Он создаёт `scope-obligations.json`, `scope-clarification-requests.md`,
`test-design-matrix.md`, `workflow-state.json` и один canonical TC file.

## Внешний scope

Внешний scope имеет:

- стабильный `scope_slug`;
- отдельный каталог `work/practical-v0.9/<scope-slug>/`;
- отдельные обязательства, matrix и immutable review artifacts;
- отдельный canonical файл `test-cases/<section-id>-<scope-slug>.md`.

Scope должен быть достаточно узким, чтобы reviewer мог независимо восстановить
требования и проверить покрытие без смешения несвязанных доменов.

## Когда нужен `agent-proposed-scope`

Используй его, если пользователь просит все ФТ, все разделы или документ,
содержащий несколько разных функциональных областей. Результат —
`scope-options.md` и `scope-selection-prompts.md` с краткими границами,
источниками и рекомендацией, с чего начать. До выбора одного scope не создавай
obligations, matrix, тест-кейсы или review artifacts.

## Когда допустим единый scope

Единый scope допустим, если выбранный раздел небольшой и однородный либо
пользователь явно подтверждает более широкий scope после предупреждения о
риске. В таком случае анализатор обязан явно указать в obligations разные
`CTX-*` для независимых create/edit, ролей, состояний и результатов. Не
создавай внутренние work packages только ради размера текста.

## Запрещённый паттерн

Не используй `all-sections`, `whole-ft` и аналогичные общие scope как
стандартный старт. Они скрывают границы, увеличивают риск дублирования и
делают matrix/review формальными.

## Downstream contract

После выбора scope `ft-scope-analyzer` проверяет DOCX/XHTML и доступный PDF,
сохраняет обязательства и вопросы БА. Если DOCX и PDF доступны, source parity
проверяет сохранность requirement codes для `source_anchor`/`req_id`. Только
после этого practical route создаёт matrix, проводит separate matrix review,
пишет TC и проводит separate final TC review. Отсутствие необходимого parity
artifact или неразрешённое противоречие источников — blocker, а не повод
додумывать поведение.
