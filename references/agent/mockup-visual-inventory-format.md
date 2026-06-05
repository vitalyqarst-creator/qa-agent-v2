# Mockup Visual Inventory Format

`mockup-visual-inventory.md` фиксирует, что UI-макет был реально открыт и использован для уточнения шагов взаимодействия, а не только перечислен как файл в пакете.

## Когда Обязателен

Артефакт обязателен для подтвержденного UI scope, если `scope-contract.md` содержит источник типа `mockup` или путь к файлу из `mockups/`.

Если макет нельзя открыть визуально, stage нельзя переводить в writer `ready-for-review`: зафиксируй причину в `workflow-state.yaml` и `scope-coverage-gaps.md` / `scope-clarification-requests.md`.

## Назначение

Макет можно использовать для:

- уточнения видимых блоков и порядка элементов;
- выбора естественного способа действия в шагах: нажать кнопку, выбрать из списка, отметить чекбокс, открыть модальное окно, перейти по вкладке;
- фиксации UI alias, если текст ФТ и подпись на макете отличаются;
- выявления mockup-only элементов и расхождений с ФТ.

Макет нельзя использовать как источник:

- обязательности, бизнес-валидации, допустимых значений, статусов, расчетов, API/backend behavior;
- точного expected result, если он не задан ФТ, support-файлом или другим утвержденным материалом;
- расширения scope без отдельного подтверждения.

При конфликте текста ФТ и макета приоритет у ФТ. Макет-only элемент должен стать `mockup-only item`, `FT conflict` или `coverage gap`, а не covered TC.

## Минимальный Формат

```md
# Mockup Visual Inventory

## Metadata

| item | value | evidence |
| --- | --- | --- |
| mockup_path | `fts/<ft-slug>/mockups/<file>` | `<path/hash/size>` |
| opened | `yes | no` | `<tool/method/time>` |
| method | `visual-inspection | OCR | image-viewer | other` | `<how inspected>` |
| screen_name | `<UI screen name>` | `<mockup caption/source>` |
| source_priority | `FT-over-mockup` | `AGENTS.md / scope-contract.md` |

## Visual Inventory

| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |
| --- | --- | --- | --- | --- |
| `visible_blocks` | `<block label>` | `<FT block/path>` | `visible` | `<ordering/position>` |
| `visible_fields` | `<field label>` | `<FT field/path>` | `visible/editable/readonly/unclear` | `<alias or mismatch>` |
| `visible_actions` | `<button/action label>` | `<FT action/path>` | `visible/enabled/disabled/unclear` | `<interaction hint>` |

## Interaction Hints

| element | interaction_hint | source | used_for_steps | limitation |
| --- | --- | --- | --- | --- |
| `<field/action>` | `<click/select/type/check/open modal>` | `mockup` | `yes/no` | `<not a business rule>` |

## Mockup-Only Items

| item | mockup_observation | ft_reference | handling |
| --- | --- | --- | --- |
| `<item>` | `<what is visible>` | `<missing/conflict/source ref>` | `gap | alias-only | ignore-out-of-scope` |

## FT Conflicts

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| `<item>` | `<FT quote/ref>` | `<mockup observation>` | `FT wins | gap | clarification` |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes/no` | `<which TC/package/design rows>` |
| not_used_as_requirement_source | `yes` | `mockup refines interaction only; FT/support define behavior` |
| open_questions | `<GAP-* or ->` | `<questions>` |
```

## Writer Rules

- Writer должен прочитать `mockup-visual-inventory.md` перед `Package Test Design Plan`.
- Шаги `TC-*` должны использовать `interaction_hints`, если они есть и не конфликтуют с ФТ.
- Generic шаги вроде `ввести или выбрать значение`, `привести данные к состоянию`, `нажать действие при необходимости` недопустимы, если макет дает более точную механику.
- Если writer не использовал макет для шагов, он должен объяснить это в `Writer Quality Gate` и `writer-session-log.md`.

## Reviewer Rules

Reviewer должен проверить:

- макет был открыт, а не только перечислен;
- `mockup_only_items` не превращены в требования;
- шаги используют подтвержденные `interaction_hints`;
- expected results не выводятся только из макета;
- конфликты ФТ/макет обработаны как `FT wins`, `GAP-*` или clarification.
