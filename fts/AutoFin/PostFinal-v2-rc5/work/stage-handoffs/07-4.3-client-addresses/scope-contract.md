# Scope Contract: 07-4.3-client-addresses

## Scope Identity

- `ft_slug`: `AutoFin/PostFinal-v2-rc5`
- `scope_slug`: `4-3-client-addresses`
- `handoff_id`: `07-4.3-client-addresses`
- `selected_section`: `4.3 / Таблица 4 / Блок «Адреса клиента»`
- `primary_source`: `fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.docx`
- `mandatory_machine_source`: `fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.xhtml`
- `pdf_cross_check_source`: `fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.pdf`
- `source_rows`: `33-58`
- `requirement_codes`: `BSR 115-161`
- `cross_reference_codes`: `BSR 324`
- `stage_status`: `blocked-input-resolved-rerun-required`

## Decision

`ft-scope-analyzer` запуск выполнен, но старый blocked handoff нельзя напрямую передавать в writer/reviewer. Входные блокеры сняты 2026-07-26: package-local vendor-reference по DaData добавлен, а применимость support v3 к текущему rc5 scope подтверждена пользователем. Перед writer/reviewer требуется повторить source-assertion materialization и независимый source assertion review.

## Included

- Отображение блока `Адреса клиента`.
- Адрес регистрации: поиск/заполнение через DaData, ручной режим, поля ручного ввода, обязательность, значения по умолчанию, подсказки и проверки формата.
- Адрес фактического места жительства: связь с адресом регистрации, поиск/заполнение через DaData, ручной режим, поля ручного ввода, обязательность, значения по умолчанию, подсказки и проверки формата.
- Условные чекбоксы частного дома для регистрационного и фактического адреса.
- Перекрестное требование `BSR 324` только в части наблюдаемой раскладки адреса DaData в ручные поля.

## Excluded

- Внутреннее заполнение `kladr` из `BSR 324`: support v3 помечает это как не проверяемое в рамках проекта без отдельного артефакта наблюдаемости.
- Общие ограничения типов данных раздела 5 и default `NULL`: support v3 исключает их из scope адресов клиента.
- Любые правила DaData, не подтвержденные ФТ/support/vendor reference: trigger, debounce, ordering, fallback, network errors, throttling, normalization details.
- Разделы карточки заявки за пределами строк `33-58`, кроме точечного cross-reference `BSR 324`.

## Source Set

| Source | Status | Use |
|---|---:|---|
| `source/PostFinal-v2.docx` | available | source of truth |
| `source/PostFinal-v2.xhtml` | available | mandatory machine extraction source |
| `source/PostFinal-v2.pdf` | available | structural/visual parity cross-check |
| `AGENT-NOTES.md` | available | package-specific mandatory context |
| `support/client-addresses-approved-clarifications-v3.md` | available, applicability confirmed 2026-07-26 | approved clarification evidence for current rc5 scope after source assertion rebuild |
| `support/client-addresses-approved-clarifications-v2.md` | available | superseded by v3 unless v3 rejected |
| `support/client-addresses-approved-clarifications.md` | available | superseded by v2/v3 unless later files rejected |
| `work/vendor-references/dadata-reference.md` | available, copied 2026-07-26 | package-local DaData vendor reference |

## Complexity Assessment

| Dimension | Level | Notes |
|---|---:|---|
| fields/blocks | high | 26 source rows plus BSR 324 cross-reference |
| conditional visibility/defaults | high | manual modes, same-address flag, private-house flags |
| requiredness | high | required fields and conditional requiredness across two address groups |
| negative validation | medium | numeric-only and 6-digit constraints have incomplete UI oracle |
| integrations | high | DaData-backed fields and region dictionary |
| status lifecycle | low | no separate workflow statuses in selected rows |

## Internal Work Packages

| package_id | package_name | source_refs | purpose | status |
|---|---|---|---|---|
| `WP-01` | Адрес регистрации | rows `34-45`, `BSR 115-137`, related `BSR 324` | UI visibility, defaults, manual mode, requiredness, numeric constraints, private-house logic for registration address | ready for source assertion rebuild; partially constrained by `GAP-003` |
| `WP-02` | Адрес фактического места жительства | rows `46-58`, `BSR 138-161`, related `BSR 324` | same-address behavior, factual address input, manual mode, requiredness, numeric constraints, private-house logic | ready for source assertion rebuild; partially constrained by `GAP-003` |
| `WP-03` | Cross-cutting DaData/dictionary/decomposition | `BSR 116`, `BSR 118-119`, `BSR 125`, `BSR 141`, `BSR 143-144`, `BSR 150`, `BSR 324`, support CLR-ADDR-001..005 | Bind DaData, dynamic region dictionary, approved clarifications and observable decomposition rules | ready for source assertion rebuild |

## Downstream Gate

Writer/reviewer может стартовать только после:

1. пересборки source assertions manifest по contract v4 с digest-bound источниками, включая `work/vendor-references/dadata-reference.md` и подтвержденный `support/client-addresses-approved-clarifications-v3.md`;
2. независимого `source_assertion_review` по новому manifest digest;
3. явной передачи writer-у `GAP-003` как non-blocking UI-calibration constraint без выдумывания exact validation messages/triggers.

До этого текущий blocked handoff не является разрешением на генерацию тест-кейсов.
