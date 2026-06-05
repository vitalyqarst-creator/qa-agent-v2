# Next-Step Prompt Format

## Special Contract `prompt.scope-gaps-to-reviewer.md`

`prompt.scope-gaps-to-reviewer.md` is the pre-writer handoff from `ft-scope-analyzer` to a new `ft-test-case-reviewer` session in mode `scope_gap_review`.

Use it only when `scope-coverage-gaps.md` contains at least one `GAP-*`.

Required inputs:

- `source-selection.md`
- `scope-contract.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `workflow-state.yaml`
- `source-parity-check.md`, when DOCX+PDF are available
- `source-row-inventory.md`, when row-level/table parity is required
- `mockup-visual-inventory.md`, when the scope uses mockups
- package `AGENT-NOTES.md`, when present

Required guardrails:

- reviewer mode is `scope_gap_review`;
- reviewer checks gap anchors, classification, clarification requests and routing readiness;
- reviewer must not write, rewrite or review test cases in this mode;
- passed review routes to `prompt.scope-to-writer.md`;
- failed review routes back to `ft-scope-analyzer` or `blocked-input`.

## Специальный Контракт `prompt.scope-to-writer.md`

`prompt.scope-to-writer.md` не должен быть только краткой ссылкой на `scope-contract.md`. Он обязан переносить в handoff критичные правила, без которых writer может воспроизвести старые дефекты даже при наличии правильных downstream-инструкций.

Обязательные входы для `prompt.scope-to-writer.md`:

- `source-selection.md`;
- `scope-contract.md`;
- `scope-coverage-gaps.md`;
- `workflow-state.yaml`;
- `source-parity-check.md`, если для основного ФТ доступны DOCX и PDF; если artifact должен быть, но отсутствует, prompt должен фиксировать blocking input issue вместо запуска writer-а;
- `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий; если artifact должен быть, но отсутствует, prompt должен фиксировать blocking input issue вместо запуска writer-а;
- `mockup-visual-inventory.md`, если подтвержденный UI scope содержит mockup / screen image / `mockups/`; если artifact должен быть, но отсутствует или `opened != yes`, prompt должен фиксировать blocking input issue вместо запуска writer-а;
- `scope-clarification-requests.md`, если есть хотя бы один `GAP-*` или открытый вопрос;
- `scope-gap-review.md`, если pre-writer `scope_gap_review` уже выполнен;
- package-specific `AGENT-NOTES.md`, если он есть в FT-пакете;
- regression/baseline artifacts, явно перечисленные в `scope-contract.md`, `source-parity-check.md`, `scope-coverage-gaps.md`, previous review/eval reports или workflow `latest_artifacts`;
- основной FT и разрешенные support materials, если writer должен извлекать детали требований.

Обязательные правила, которые должны быть явно продублированы в `prompt.scope-to-writer.md`, а не только спрятаны во вложенных артефактах:

- работать package-by-package для каждого scope; `scope-contract.md` должен содержать минимум один internal work package;
- каждый `ATOM-*` и каждый `TC-*` должен иметь `package_id`;
- для каждого package выполнить три gate: package ledger self-check, Package Test Design Plan self-check до написания TC и package TC self-check до перехода к следующему package;
- если scope строится по таблицам полей/действий или PDF/DOCX extraction, перед `Atomic Requirements Ledger` сверить writer-side `Source Row Inventory` с handoff `source-row-inventory.md`, затем создать `Source Table Normalization`; загрязненные строки с соседними полями, table-header residue или low confidence должны идти в `GAP-*`, а не в `covered`;
- до записи больших generated artifacts или canonical file выполнить `Artifact Write Strategy` preflight: если ожидается больше `20` `TC-*`, больше `30` `ATOM-*`, Markdown больше `20 000` символов, scope содержит `WP-*` или создается table-heavy artifact, stage обязан сразу использовать `scripts/write_artifact_sections.py --manifest <manifest.json>`; one-shot PowerShell/here-string/inline giant command, compact draft, summary draft, ad-hoc `tmp/generate_*.py` и объединение требований ради прохождения validator запрещены;
- для русскоязычных ФТ и Markdown-артефактов использовать UTF-8 preamble перед PowerShell-командами и перечитывать важные source artifacts через явную UTF-8 кодировку; если stdout/console дал mojibake, distorted output нельзя использовать как evidence, а fallback должен быть раскрыт в `Technical Fallbacks`;
- если scope является UI scope с mockup, сначала использовать `mockup-visual-inventory.md`: mockup уточняет только UI-шаги, видимые блоки/поля/actions и interaction hints; он не является источником бизнес-правил, allowed values, обязательности, validation или expected results;
- не смешивать разные `package_id` в одном `TC-*`, кроме явно обоснованного scenario/action case;
- сохранить mandatory requirement ids и source-parity findings; PDF-only коды/утверждения нельзя молча удалять;
- применить regression/baseline lessons до создания ledger: ранее зафиксированные `gap` / `unclear` не переводить в `covered` без нового источника или observable artifact;
- internal/API/RabbitMQ/DB/model/persistence/async effects без observable artifact оставлять `gap` / `unclear`; UI-visible action initiation можно покрывать отдельно;
- один `TC-*` = одна основная проверка и один основной expected result; valid и invalid classes не объединять в один case;
- обязательные outputs writer-а: canonical test-case file, `Source Table Normalization` для табличных/extraction scope, `Test Design Decision Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Test-design Applicability Matrix`, `Dependency Matrix` при зависимостях, `Risk / Priority Map`, coverage gaps, writer self-check и `prompt.writer-to-reviewer.round-1.md`;
- writer-pass завершает этап только `stage_status: ready-for-review`; writer не ставит `signed-off`.

Если canonical test-case file уже существует, `prompt.scope-to-writer.md` должен явно указать режим: `continue-current-workflow`, `revision-from-findings`, `rebuild-from-scope` или `fresh-eval-run`. Без такого режима следующий агент может ошибочно принять старый `signed-off` как запрет на writer-pass или, наоборот, перезаписать валидный baseline без причины.

Канонический `next-step prompt` используется как человекочитаемый handoff к следующему skill-у после завершения этапа.

## Назначение

- зафиксировать цель следующего этапа;
- перечислить обязательные входные артефакты;
- не заставлять следующего исполнителя восстанавливать intent по истории диалога;
- держать prompt-файлы в одном формате для ручного и агентного запуска.

## Расположение

Prompt-файлы хранятся в:

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/` для новых handoff-папок, по правилам `stage-handoff-model.md`

## Рекомендуемые имена файлов

- `prompt.scope-to-writer.md`
- `prompt.scope-to-iteration.md`
- `prompt.scope-gaps-to-reviewer.md`
- `prompt.writer-to-reviewer.round-1.md`
- `prompt.reviewer-to-writer.round-1.md`
- `prompt.writer-to-reviewer.round-2.md`
- `prompt.reviewer-to-ui-prep.md`

## Обязательные секции

- `## Цель этапа`
- `## Входные артефакты`
- `## Обязательные действия`
- `## Не делать`
- `## Ожидаемые выходы`
- `## Gate завершения`

## Рекомендуемый шаблон

```md
## Цель этапа
Кратко: что должен сделать следующий skill.

## Входные артефакты
- `...`
- `...`

## Обязательные действия
- `...`
- `...`

## Не делать
- не расширять scope
- не выдумывать поведение вне ФТ

## Ожидаемые выходы
- `...`
- `...`

## Gate завершения
Этап считается завершенным, когда созданы ...
```

## Правила использования

- Все человекочитаемые поля prompt-файла должны быть на русском языке.
- Prompt должен ссылаться только на актуальные артефакты текущего `scope-slug`.
- Prompt не заменяет `workflow-state.yaml`: process-status остается в state-файле.
- Prompt не должен дублировать полный workflow skill-а; он фиксирует только handoff для конкретного этапа и конкретного scope.
- Если после scope analysis доступны два варианта запуска, `prompt.scope-to-writer.md` используется для единичного writer-pass, а `prompt.scope-to-iteration.md` — для полного writer-reviewer loop через `ft-test-case-iteration`.

## Минимум автоматической проверки

`scripts/validate_agent_artifacts.py` проверяет только активный prompt, который следует из текущего `workflow-state.yaml`, а не все historical prompt-файлы в handoff-папке.

Минимальный enforced contract:

- есть секция цели этапа;
- есть секция входных артефактов;
- есть секция ограничений / guardrails;
- секция входных артефактов содержит хотя бы одну ссылку на artifact, который разрешается в текущем checkout.
- Для `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md` секция входных артефактов должна содержать resolving ссылки на `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`; если workflow включает `source-parity-check.md`, `source-row-inventory.md`, `mockup-visual-inventory.md` или `scope-clarification-requests.md`, prompt должен ссылаться и на них.
- Для `prompt.scope-gaps-to-reviewer.md` секция входных артефактов должна содержать resolving ссылки на `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md` и `workflow-state.yaml`; если workflow включает `source-parity-check.md`, `source-row-inventory.md` или `mockup-visual-inventory.md`, prompt должен ссылаться и на них.

Шесть секций выше остаются каноническим форматом для новых prompt-файлов. Legacy aliases вроде `Inputs`, `Constraints`, `Required Changes` пока принимаются валидатором для обратной совместимости.
