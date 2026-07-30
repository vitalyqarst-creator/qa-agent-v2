# UI validation report: 13-4.3-employment-info

Date: 2026-07-30
Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
Mode: FT UI calibration / execution attempt
Source file: `fts/AutoFin/PostFinal-v2-rc5/test-cases/13-4.3-employment-info.md`

## Scope Summary

- Total test cases in file: 83 (`TC-EMP-001` ... `TC-EMP-083`).
- Current UI-calibration outcome after second pass: 76 confirmed / UI-ready, 0 mismatch-ft-ui, 7 blocked or not reproducible.
- UI was opened in a new application card.
- Second pass used clean new application cards for DaData organization, date/period masks, phone masks, and inactive-organization fixture.
- Block `Сведения о занятости` is available on the same application page without a separate wizard step.
- Baseline test-cases were not edited.

## Confirmed UI Behavior

### Income confirmation block

- `Способ подтверждения дохода` is visible by default with `Бумажное` selected.
- `Подтверждение дохода` is visible for `Бумажное`.
- Paperclip upload control is available in `Подтверждение дохода`.
- Valid PDF upload result: file name `valid-income.pdf` is displayed in the field.
- After successful upload, three icons appear at the right side of the field: eye/view, trash/delete, download.
- Trash/delete removes the uploaded file immediately, without confirmation. After deletion, file name disappears and field shows `Необходимо добавить файл`.
- Unsupported `.txt` upload shows exact message:
  `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат pdf, размер не более 40 МБ`
- `>40MB` PDF upload on a clean card shows the same exact message:
  `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат pdf, размер не более 40 МБ`
- Selecting `Госуслуги` hides `Подтверждение дохода` and shows exact green explanatory text:
  `При формировании анкеты будет сгенерирован QR-код для подтверждения доходов в Госуслугах`

### Phone/QR attach controls

- Top `ПРИКРЕПИТЬ С ТЕЛЕФОНА` in employment block is visible as a grey `div.button` control, not a native HTML `button`.
- Final implementation for this control is not available yet for `TC-EMP-002` / `TC-EMP-004`, so functional QR/modal behavior is not currently verifiable.

### Main job block

- Selecting `Социальный статус = работа по найму` shows fields:
  `Наименование организации, ИНН`, `ОПФ`, `Дата начала работы в компании`, `Фактический адрес работы`, `Рабочий телефон`, `Тип должности`, `Должность`, `Начало общего трудового стажа`, `Среднемесячный доход после вычета налогов, ₽`.
- DaData organization search behavior:
  - In a clean new application card, manual keypress input `7707083893` opened DaData suggestions after wait.
  - Dropdown DOM: `ul.ui-autocomplete.ui-front.ui-menu.ui-widget.ui-widget-content.ui-corner-all.vcm-dropdown`; options are visible as `li.ui-menu-item`.
  - Selected option: `ПАО СБЕРБАНК, 7707083893 7707083893 г Москва, ул Вавилова, д 19`.
  - After selecting the suggestion and blurring `Фактический адрес работы`, UI retained:
    - `Наименование организации, ИНН`: `ПАО СБЕРБАНК, 7707083893`
    - `ОПФ`: `ПАО`
    - `Фактический адрес работы`: `г Москва, ул Вавилова, д 19`
- `Тип должности` dropdown options:
  - `Главный специалист/Руководитель среднего звена`
  - `Индивидуальный предприниматель`
  - `Сотрудник/Рабочий/Ассистент`
  - `Топ менеджер/Руководитель высшего звена`
  - `Эксперт/Старший или Ведущий специалист`
- `Должность` is editable and retains typed value after blur, checked with `Инженер`.
- Main job trash control removes all main job fields immediately, without confirmation. After deletion, only `Социальный статус` remains in `Основная работа`.
- Re-selecting a working social status re-creates main job fields empty.

### Second-pass masked-field behavior

Second pass used clean new application cards and manual keypress input for masked fields.

- `Дата начала работы в компании`:
  - Manual input `01.01.2020` plus blur displayed `01.01.2020`; field/container state `valid`; no validation message.
  - Paste `64.64.6543` plus blur cleared the field and produced `required invalid` state.
  - Manual input `64.64.6543` plus blur retained `64.64.6543` in the field and produced `required invalid` state.
- `Начало общего трудового стажа`:
  - On focus, empty mask is `__.____`.
  - Manual input `01.2020` plus blur displayed `01.2020`; field/container state `valid`; no validation message.
  - Paste `55.6523` produced `55.6523__.____` while focused; after blur the field cleared and became `required invalid`.
  - Manual input `55.6523` plus blur retained `55.6523` in the field and produced `required invalid` state.
- `Рабочий телефон`:
  - On focus, empty mask is `+7 (___) ___–__–__`.
  - Manual input `9234567890` plus blur displayed `+7 (923) 456–78–90`; state `valid`; no validation message.
  - Manual input `923456789` showed incomplete value `+7 (923) 456–78–9_` while focused; after blur the field cleared, became `empty required invalid`, and showed `Обязательно к заполнению`.
  - Manual input `92345678901` ignored the 11th digit; after blur displayed `+7 (923) 456–78–90`; state `valid`; no validation message.
  - Manual input `92345A7890` filtered out `A`; resulting incomplete value cleared after blur, field became `empty required invalid`, and showed `Обязательно к заполнению`.

### Social status visibility matrix

| Social status | Visible employment fields |
|---|---|
| `военнослужащий` | Organization, OPF, start date, work address, work phone, position type, position, total employment start, income |
| `ИП` | Organization, OPF, start date, work address, work phone, position type, position, total employment start, income |
| `пенсионер (не работает)` | Total employment start, income |
| `работа по найму` | Organization, OPF, start date, work address, work phone, position type, position, total employment start, income |
| `самозанятый` | Total employment start, income |
| `собственник бизнеса` | Organization, OPF, start date, work address, work phone, position type, position, total employment start, income |

### OPF list

Visible/dropdown DOM contained these OPF values:

`ИП`, `ООО`, `АО`, `ПАО`, `НАО`, `ГУП`, `Полное товарищество`, `Товарищество на вере`, `Хозяйственное партнерство`, `Производственный кооператив`, `КФХ`, `ФГУП`, `МУП`, `Потребительский кооператив`, `Общественная организация`, `Общественное движение`, `Ассоциация`, `ТСН (ТСЖ)`, `Казачье общество`, `Община коренных народов`, `Нотариальная палата`, `Адвокатская палата`, `Фонд`, `Учреждение`, `АНО`, `Религиозная организация`, `Госкорпорация`, `Госкомпания`, `Публично-правовая компания`, `Глава КФХ`, `Простое товарищество`, `ПИФ`.

### Additional income

- `ДОБАВИТЬ ИСТОЧНИК ДОХОДА` adds a new additional-income row.
- New row fields: `Тип дохода`, `Среднемесячный доход после вычета налогов`, row trash control.
- `Тип дохода` dropdown initially contains exactly:
  - `Аренда`
  - `Дивиденды`
  - `Пенсия`
- Archive value `contribution` was not visible.
- Selecting `Аренда` retains the value after blur.
- Additional-income amount `5000` is accepted and displayed visually as `5 000`.
- Adding a second additional-income row is allowed, but the second row's `Тип дохода` dropdown excludes already selected `Аренда` and shows only `Дивиденды`, `Пенсия`.
- Deleting a second empty row removes only that row immediately, without confirmation.
- Deleting the filled `Аренда` row removes it immediately, without confirmation. Re-adding a row does not restore old values.

### Income amount validation

Checked field `Среднемесячный доход после вычета налогов, ₽`:

| Input | Displayed/eval value | Observed message |
|---|---:|---|
| `1999` | `1999` | `Введите сумму более 2000 руб` |
| `2000` | `2000` | no min-value error |
| `50000` | `50000` / visually `50 000` | no min-value error |
| `1000000` | `1000000` | no min-value error |
| `1000001` | visually `1 000 001` | `Перепроверьте доход` |
| paste `abc` | `0` | `Введите сумму более 2000 руб` |
| manual typing letters/symbols | unchanged / digits-only input | letters and non-digit symbols are not entered |

`Доход клиента` behavior was manually rechecked by the user and considered reproducible/correct for `TC-EMP-075`.

### Manual UI evidence from user

Additional manual verification provided by the user after the automated pass:

- `TC-EMP-002`, `TC-EMP-004`, `TC-EMP-028`: final implementation is not available yet, so these cases cannot be checked now.
- `TC-EMP-066`: `1000001` reproduced as invalid; UI displays value `1 000 001` and message `Перепроверьте доход`.
- `TC-EMP-067`: behavior depends on input method. When a text value is pasted into the field, UI displays `0` and message `Введите сумму более 2000 руб`. During manual keyboard entry, text and other non-digit symbols are not entered; only digits are accepted. Treat behavior as correct.
- `TC-EMP-075`: behavior reproduces correctly in UI.
- Second pass rechecked `TC-EMP-011`, `TC-EMP-027`, `TC-EMP-033`, `TC-EMP-036`, `TC-EMP-045`, `TC-EMP-046`, `TC-EMP-047`, `TC-EMP-048`, `TC-EMP-076` on clean cards where needed. Detailed observations are stored in `employment-second-pass-observations.md`.

## Blocked / Not Reliably Executed

- `ПРИКРЕПИТЬ С ТЕЛЕФОНА` QR modal in employment block: final implementation is not available yet; `TC-EMP-002` / `TC-EMP-004` cannot be checked now.
- `Госуслуги` request after `Далее`: final implementation is not available yet; `TC-EMP-028` cannot be checked now.
- Eye/view uploaded document: browser-control policy blocked the attempt to open/view the uploaded PDF. Delete was checked separately and confirmed.
- `TC-EMP-034`: required validation for empty `Начало общего трудового стажа` on `ДАЛЕЕ` was not re-executed end-to-end in the second pass.
- `TC-EMP-043`: required validation for empty `Рабочий телефон` on `ДАЛЕЕ` was not re-executed end-to-end in the second pass.
- Inactive organization fixture `ФОРМАД-ПЛАСТ ООО 7701`: on a clean new application card, paste input did not produce DaData options, the organization field stayed empty, no message `Организация не является действующей` was observed, and `ДАЛЕЕ` remained visible/enabled. Keep `TC-EMP-048` as `needs-test-data` / `not-reproducible` until a working inactive-organization fixture is available.
- `Фактический адрес работы` manual entry is partially observed only. Locator returned the typed value, but visual screenshot looked blank after blur; keep as needs manual re-check before automation.

## TC Outcome Summary

### Confirmed / UI-ready

`TC-EMP-001`, `TC-EMP-003`, `TC-EMP-005`, `TC-EMP-006`, `TC-EMP-007`, `TC-EMP-008`, `TC-EMP-009`, `TC-EMP-010`, `TC-EMP-011`, `TC-EMP-012`, `TC-EMP-013`, `TC-EMP-014`, `TC-EMP-015`, `TC-EMP-016`, `TC-EMP-017`, `TC-EMP-018`, `TC-EMP-019`, `TC-EMP-020`, `TC-EMP-021`, `TC-EMP-022`, `TC-EMP-023`, `TC-EMP-024`, `TC-EMP-025`, `TC-EMP-026`, `TC-EMP-027`, `TC-EMP-029`, `TC-EMP-031`, `TC-EMP-032`, `TC-EMP-033`, `TC-EMP-035`, `TC-EMP-036`, `TC-EMP-037`, `TC-EMP-038`, `TC-EMP-039`, `TC-EMP-040`, `TC-EMP-041`, `TC-EMP-042`, `TC-EMP-044`, `TC-EMP-045`, `TC-EMP-046`, `TC-EMP-047`, `TC-EMP-049`, `TC-EMP-050`, `TC-EMP-051`, `TC-EMP-052`, `TC-EMP-053`, `TC-EMP-054`, `TC-EMP-055`, `TC-EMP-056`, `TC-EMP-057`, `TC-EMP-058`, `TC-EMP-059`, `TC-EMP-060`, `TC-EMP-061`, `TC-EMP-062`, `TC-EMP-063`, `TC-EMP-064`, `TC-EMP-065`, `TC-EMP-066`, `TC-EMP-067`, `TC-EMP-068`, `TC-EMP-069`, `TC-EMP-070`, `TC-EMP-071`, `TC-EMP-072`, `TC-EMP-073`, `TC-EMP-074`, `TC-EMP-075`, `TC-EMP-076`, `TC-EMP-077`, `TC-EMP-078`, `TC-EMP-079`, `TC-EMP-080`, `TC-EMP-081`, `TC-EMP-082`, `TC-EMP-083`.

### Needs test-case correction / mismatch-ft-ui

No open `mismatch-ft-ui` items after user manual recheck.

### Blocked-observability / not reliably executed

- `TC-EMP-002`, `TC-EMP-004`, `TC-EMP-028`: final implementation is not available yet; cannot be checked now.
- `TC-EMP-034`: required validation for empty `Начало общего трудового стажа` on `ДАЛЕЕ` was not re-executed end-to-end in the second pass.
- `TC-EMP-043`: required validation for empty `Рабочий телефон` on `ДАЛЕЕ` was not re-executed end-to-end in the second pass.
- `TC-EMP-030`: PDF viewer/eye action blocked by browser-control policy.
- `TC-EMP-048`: inactive organization fixture did not reproduce on a clean card; needs better fixture or manual data setup.

## Recommended Test-case Adjustments

- For DaData organization positive path, use a clean card, focus the visible `Наименование организации, ИНН` input, manually enter `7707083893`, wait for the DaData dropdown, and select `ПАО СБЕРБАНК, 7707083893 7707083893 г Москва, ул Вавилова, д 19`.
- For `ПРИКРЕПИТЬ С ТЕЛЕФОНА`, split tests:
  - visibility/technical locator of `div.button`;
  - actual QR modal opening only after confirming the card state where the control is functional.
- Add negative date/period coverage. Current file covers positive date/period input, but does not separately cover impossible day/month values:
  - `Дата начала работы в компании`: manual `64.64.6543` remains visible after blur and marks the field invalid; paste `64.64.6543` clears the field after blur.
  - `Начало общего трудового стажа`: manual `55.6523` remains visible after blur and marks the field invalid; paste `55.6523` clears the field after blur.
- For `Рабочий телефон`, assert exact second-pass behavior:
  - empty focus mask: `+7 (___) ___–__–__`;
  - valid `9234567890` -> `+7 (923) 456–78–90`;
  - short `923456789` clears after blur and shows `Обязательно к заполнению`;
  - long `92345678901` ignores the 11th digit and remains `+7 (923) 456–78–90`;
  - manual alpha `92345A7890` filters out `A`; incomplete resulting value clears after blur and shows `Обязательно к заполнению`.
- For income numeric validation, update expectations:
  - `1999` -> `Введите сумму более 2000 руб`;
  - paste `abc` -> field displays `0` and message `Введите сумму более 2000 руб`;
  - manual typing letters/symbols -> non-digit characters are not entered;
  - `1000001` displays `1 000 001` and message `Перепроверьте доход`.
- `TC-EMP-075` can be treated as reproducible/correct based on manual UI recheck.
- For additional income duplicate type, assert that used type is filtered out from the next row dropdown, not that a duplicate-row add is blocked.
- For upload errors, use the exact unified message:
  `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат pdf, размер не более 40 МБ`
- Keep `TC-EMP-048` dependent on a verified inactive-organization fixture. `ФОРМАД-ПЛАСТ ООО 7701` did not reproduce on a clean new card in the second pass.
