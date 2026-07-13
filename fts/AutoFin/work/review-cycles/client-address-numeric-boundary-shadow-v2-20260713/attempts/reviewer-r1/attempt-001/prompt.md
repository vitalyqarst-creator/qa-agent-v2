# Codex exec prepared-standard reviewer compact path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 5,
  "package_id": "client-address-numeric-boundaries-v2",
  "ft_slug": "AutoFin",
  "scope_slug": "application-card-client-address-numeric-boundaries-shadow",
  "section_id": "14",
  "execution_profile": "standard-required",
  "context_profile": "numeric-date-boundary",
  "unsupported_dimensions": [
    "date-boundaries",
    "negative-feedback",
    "integration-persistence",
    "dependency-state",
    "dictionary-values"
  ],
  "reviewed_draft_sha256": "1403dec17ce4ca223568c4111d7962845a808aadba98ad1a73cda859fb88f2f8"
}
```

# Prepared Reviewer Runtime Profile

This is the technical execution projection inside `ft-test-case-reviewer`. It introduces no new QA policy. The immutable package, context rule card and deterministic gates materialize the applicable canonical reviewer rubric for both `simple-field-property` and `standard-required` scopes.

## Eligibility

Continue only when the payload confirms:

- current package version and immutable draft SHA-256;
- explicit execution/context profiles and unsupported dimensions;
- scope-local source evidence and atomic obligations;
- passed structure, seed, obligation, quality and evidence-access gates;
- semantic-overlap diagnostic and calibration lifecycle.

Return a blocking finding when the payload is insufficient or inconsistent. Do not open full project instructions, package files, production test cases, earlier cycles or full sources to bypass eligibility.

## Review Procedure

1. Review every supplied obligation exactly once and preserve its exact `obligation_id -> atom_id` pair and draft SHA-256.
2. For every testable obligation, verify that its linked TC performs the supplied condition/action with concrete data and reaches the supplied observable oracle.
3. For every gap, unclear or not-applicable obligation, verify that the draft does not invent executable coverage.
4. For every non-blocking constraint gap, verify that the linked TC preserves the `GAP-*` and does not choose an unspecified mechanism.
5. Apply the embedded context rule card: boundary points remain independent; invalid classes remain independent; branch preconditions and integration triggers remain explicit.
6. Reject invented screens, fields, literals, dictionary values, messages, statuses, UI reactions, API/DB effects, persistence or internal state.
7. Reject non-atomic cases, generic fixtures, placeholder steps, source-rule-only expected results, duplicate titles and nominal traceability.
8. Classify every semantic-overlap group. Accept a shared body only when the package explicitly groups one observable multi-obligation check.
9. For UI-calibration candidates, require `ui-calibration-required`, `candidate-ui-calibration`, the linked GAP and a neutral expected result that does not preselect filtering/message/highlight/save behavior.
10. Return exactly the structured review contract requested by the runner. Do not write files.

## Decision Floor

- `accepted` requires every obligation to have a compatible verdict, every testable obligation to be correctly covered, all gaps to be preserved and no error finding.
- `changes-required` requires at least one concrete finding linked to supplied ATOM/TC identifiers, unless it is a set-level scope finding.
- A failed deterministic gate, draft hash mismatch, unknown identifier, lost constraint gap or insufficient evidence prevents sign-off.

## Runtime Boundary

No command is needed. If runtime confirmation is absolutely required, only the explicitly allowlisted environment probe may be used. Any repository exploration or workspace mutation violates the compact prepared reviewer contract.

## Context profile: `numeric-date-boundary`

- Keep every supplied boundary point independent and preserve relative-date clock assumptions.
- Do not invent catalog limits, rounding or timezone behavior.

## Selected source evidence

# Prepared Source Evidence

- package_id: `client-address-numeric-boundaries-v2`

## Mandatory package context

- source_path: `fts/AutoFin/AGENT-NOTES.md`
- source_sha256: `a79deafdfce98e3156dc4cacaf518031c248983c3dadaa1c72544903420bdca8`
- selectors: `## Сокращения В Таблицах UI-Полей`

## Сокращения В Таблицах UI-Полей

Статус: package-specific рабочее правило для AutoFin, добавленное по подтверждению пользователя и сверенное с аналогичными заметками в `fts/ft-2-OF_16/AGENT-NOTES.md`, `fts/ft-2-OF_17/AGENT-NOTES.md`, `fts/ft-2-OF_18/AGENT-NOTES.md`.

В таблицах описания свойств полей формы столбец `О` означает `Обязательность`, а столбец `Р` означает `Редактируемость`.

## Final source selection

- source_path: `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- source_sha256: `92c0189867c2c70749b9dbc4672da3e47a4d0b28ff90653782ed4d605a000af7`
- selectors: `full-explicit`

# Source Selection

## Context

- request_summary: AutoFin-only prepared compiler cross-scope validation.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-11`
- created_by: `Codex / ft-source-locator`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Explicit continuation boundary and authoritative source of truth. | `Final` | Exact stem matches XHTML and PDF. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source. | `Final XHTML` | Used by existing selected-scope row inventories. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural cross-check for the same FT. | `Final PDF` | Not used as row-level replacement for XHTML. |

## Machine-Readable XHTML Source

- main_ft_xhtml: `source/FT4AutoFinFinal.xhtml`
- xhtml_available: `yes`
- xhtml_path: `source/FT4AutoFinFinal.xhtml`
- xhtml_matches_main_ft: `yes`
- xhtml_role: `mandatory_machine_readable_extraction_source`
- xhtml_required_for_downstream: `yes`
- blocking_reason: `none`

## Structural Cross-Check PDF

- pdf_available: `yes`
- pdf_path: `source/FT4AutoFinFinal.pdf`
- pdf_matches_main_ft: `yes`
- limitation: structural cross-check only; row extraction remains XHTML-first and DOCX-authoritative.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Mandatory AutoFin package context. | `yes` | Does not add requirements. |
| `support/` | `support` | May be referenced by an already confirmed scope. | `scope-dependent` | Cannot expand scope or replace FT sources. |
| `mockups/` | `mockups` | UI hints for confirmed UI scopes. | `scope-dependent` | Not a source of business rules. |

## Source Quality

- active source documents: `source/FT4AutoFinFinal.docx`; `source/FT4AutoFinFinal.xhtml`; `source/FT4AutoFinFinal.pdf`.
- parseability: confirmed by existing FT4 source-selection, row-inventory and parity artifacts.
- section-id confidence: high for selected existing scopes with explicit section and source rows.
- oversized blocks: full XHTML is large; compiler reads only canonical prepared evidence artifacts.
- strict warnings: `AutoFinPreFinal.*`, neighboring `fts/*`, generated TC and previous cycle outputs are forbidden as requirement evidence.

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `fts/AutoFin/source/FT4AutoFinFinal.*` | Exact requested source family exists. | selected |
| `fts/AutoFin/source/AutoFinPreFinal.*` | Older source family used by legacy scopes. | rejected for this validation |
| neighboring `fts/*` | Outside user-authorized FT boundary. | forbidden |

## Handoff

- next_skill: `agent-architecture-auditor / prepared compiler preflight`
- required_inputs: this source selection, compiler workflow snapshots, existing FT4 canonical design artifacts.
- latest_artifacts: `scope-matrix.md`, `workflow-state.yaml`, `source-locator-session-log.md`, `agent-decision-log.md`.
- blocked_reasons: none.

## Canary boundary contract

- source_path: `fts/AutoFin/work/stage-handoffs/34-client-address-numeric-boundary-canary/scope-contract.md`
- source_sha256: `731dea1bf372470c7611e4bce623a304ea1a6cef6bfb77d56c90c59d6e8ddae0`
- selectors: `full-explicit`

# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`.
- Основной FT: `source/FT4AutoFinFinal.docx`.
- Машиночитаемый источник: `source/FT4AutoFinFinal.xhtml`.
- PDF cross-check: `source/FT4AutoFinFinal.pdf`.
- Родительский подтверждённый scope: `application-card-client-addresses-contacts`.
- Текущий canary является внутренним рабочим пакетом родительского scope, а не новым внешним scope.

## Scope Identity

- `scope_slug`: `application-card-client-address-numeric-boundaries-shadow`.
- Раздел: `4.3`, Table 4, блок адресов клиента.
- Цель: проверить standard structured pipeline на пяти однородных numeric-format obligations.

## Что Входит В Scope

- `Адрес регистрации / Почтовый индекс`, `SRC-004.P02`, `BSR 116`.
- `Адрес регистрации / Корпус`, `SRC-011.P02`, `BSR 124`.
- `Адрес регистрации / Квартира`, `SRC-012.P02`, `BSR 126`.
- `Фактический адрес / Квартира`, `SRC-025.P03`, `BSR 151`.
- `Фактический адрес / Почтовый индекс`, `SRC-026.P02`, `BSR 153`.
- Только source-backed положительный oracle: допустимое числовое значение; для индекса — ровно шесть цифр.

## Что Не Входит В Scope

- Тексты ошибок, фильтрация, блокировка перехода и иное поведение для невалидного ввода.
- Видимость, обязательность, DaData, сохранение `kladr`, контакты и прочие поля адреса.
- Production promotion и изменение существующих тест-кейсов.

## Разрешённые Источники

- Только выбранный комплект `FT4AutoFinFinal.*`, package notes и канонические source/design artifacts, перечисленные в prepared package.
- Старые `AutoFinPreFinal.*`, production test cases и предыдущие generated drafts запрещены как requirement evidence.

## Условие Старта

- Новый immutable package содержит 5 testable obligations и один non-blocking constraint gap.
- Validate-only и dispatcher preflight проходят до live-запуска.
- Запускается ровно один writer/reviewer cycle без SDK fallback.

## Canary source parity

- source_path: `fts/AutoFin/work/stage-handoffs/34-client-address-numeric-boundary-canary/source-parity-check.md`
- source_sha256: `13888e314fe44cff7c81476a4d01ed0cd5e42b181c4d78cf5936b62f5bac87b6`
- selectors: `full-explicit`

# Source Parity Check

## Контекст

- Активный комплект: `FT4AutoFinFinal.docx`, `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.pdf`.
- Канонический полный parity artifact: `work/stage-handoffs/02-application-card-client-addresses-contacts/source-parity-check.md`.
- Canary-срез: Table 4 address rows, `BSR 116`, `BSR 124`, `BSR 126`, `BSR 151`, `BSR 153`.

## Результат

| проверка | результат |
| --- | --- |
| XHTML доступен и соответствует выбранному Final stem | `pass` |
| PDF подтверждает непрерывность адресных строк и BSR-кодов | `pass` |
| Все пять BSR сохранены в source-row inventory и normalization | `pass` |
| PDF используется только для structural cross-check | `pass` |
| Blocking parity issue | `none` |

## Ограничения

- Значение ограничения извлекается из XHTML/DOCX-backed normalization; PDF не добавляет новое поведение.
- Если live draft добавит negative feedback, которого нет в источнике, stop-gate считается нарушенным.

## Selected source rows

- source_path: `fts/AutoFin/work/stage-handoffs/34-client-address-numeric-boundary-canary/source-row-inventory.md`
- source_sha256: `09d933605a975c49e65c3b5475a6ee53ef4fe4fbbabf1e4d8db42ee8d8db1e02`
- selectors: `full-explicit`

# Source Row Inventory

| source_property_id | поле | locator | req_id | нормализованное правило |
| --- | --- | --- | --- | --- |
| `SRC-004.P02` | `Адрес регистрации / Почтовый индекс` | `DOCX row 035`; `PDF page 19` | `BSR 116` | Только 6 числовых символов. |
| `SRC-011.P02` | `Адрес регистрации / Корпус` | `DOCX row 042`; `PDF page 20` | `BSR 124` | Возможен ввод только числовых символов. |
| `SRC-012.P02` | `Адрес регистрации / Квартира` | `DOCX row 043`; `PDF page 20` | `BSR 126` | Возможен ввод только числовых символов. |
| `SRC-025.P03` | `Фактический адрес / Квартира` | `DOCX row 056`; `PDF page 22` | `BSR 151` | Возможен ввод только числовых символов. |
| `SRC-026.P02` | `Фактический адрес / Почтовый индекс` | `DOCX row 057`; `PDF page 22` | `BSR 153` | Только 6 числовых символов. |

## Final source-backed field properties

- source_path: `fts/AutoFin/work/test-design/14-application-card-client-addresses/source-table-normalization.md`
- source_sha256: `c262b7a186b3bc1d8c95e4f8c1a43f4af93fe19b24af7a4a0eb26d2265ea8e3e`
- selectors: `full-explicit`

# Source Table Normalization

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `SRC-001.P01` | `WP-01` | Блок `Адреса клиента` | `visibility` | `always` | Блок `Адреса клиента` отображается в заявке. | `no_requirement_code:SRC-001` | `DOCX section-14 row 032` | `high` | `none_required:covered` | `ATOM-001` |
| `SRC-002` | `SRC-002.P01` | `WP-01` | `Адрес регистрации` | `visibility` | `always` | `Адрес регистрации` видим всегда. | `BSR 107` | `PDF page 19`; `DOCX row 033` | `high` | `none_required:covered` | `ATOM-002` |
| `SRC-002` | `SRC-002.P02` | `WP-01` | `Адрес регистрации` | `integration` | `DaData` | `Адрес регистрации` интегрирован с DaData. | `BSR 108` | `PDF page 19`; `DOCX row 033` | `high` | `GAP-001` | `ATOM-003` |
| `SRC-002` | `SRC-002.P03` | `WP-01` | `Адрес регистрации` | `address-required-components` | `no apartment / region and house required` | Обязательны регион и дом; отсутствие квартиры вызывает красную подсветку и точную подсказку. | `BSR 109` | `PDF page 19`; `DOCX row 033` | `high` | `none_required:covered` | `ATOM-004` |
| `SRC-002` | `SRC-002.P04` | `WP-01` | `Адрес регистрации` | `validation-message` | `DaData not found` | Для ненайденного адреса выводится текст `Некорректно указан адрес`. | `BSR 110` | `PDF page 19`; `DOCX row 033` | `high` | `none_required:covered` | `ATOM-005` |
| `SRC-002` | `SRC-002.P05` | `WP-01` | `Адрес регистрации` | `decomposition` | `DaData found` | Найденный адрес раскладывается по ручным полям. | `BSR 111` | `PDF page 19`; `DOCX row 033` | `high` | `none_required:covered` | `ATOM-006` |
| `SRC-002` | `SRC-002.P06` | `WP-01` | `Адрес регистрации` | `manual-assembly` | `manual fields filled` | При ручном заполнении адрес собирается из ручных полей в указанном порядке. | `BSR 112` | `PDF page 19`; `DOCX row 033` | `high` | `none_required:covered` | `ATOM-007` |
| `SRC-003` | `SRC-003.P01` | `WP-01` | `Адрес регистрации / Ввести вручную` | `visibility` | `always` | Элемент доступен на форме всегда. | `BSR 113` | `PDF page 19`; `DOCX row 034` | `high` | `none_required:covered` | `ATOM-008` |
| `SRC-003` | `SRC-003.P02` | `WP-01` | `Адрес регистрации / Ввести вручную` | `default-value` | `initial` | Значение по умолчанию равно `Нет`. | `BSR 114` | `PDF page 19`; `DOCX row 034` | `high` | `none_required:covered` | `ATOM-009` |
| `SRC-004` | `SRC-004.P01` | `WP-01` | `Адрес регистрации / Почтовый индекс` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 115` | `PDF page 19`; `DOCX row 035` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-004` | `SRC-004.P02` | `WP-01` | `Адрес регистрации / Почтовый индекс` | `numeric-format` | `manual = Да` | Ограничение на формат: только 6 числовых символов. | `BSR 116` | `PDF page 19`; `DOCX row 035` | `medium` | `none_required:covered` | `ATOM-011` |
| `SRC-005` | `SRC-005.P01` | `WP-01` | `Адрес регистрации / Регион` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 117` | `PDF page 19`; `DOCX row 036` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-005` | `SRC-005.P02` | `WP-01` | `Адрес регистрации / Регион` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-005` | `DOCX row 036` | `high` | `none_required:covered` | `ATOM-012` |
| `SRC-006` | `SRC-006.P01` | `WP-01` | `Адрес регистрации / Район` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 118` | `PDF page 19`; `DOCX row 037` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-007` | `SRC-007.P01` | `WP-01` | `Адрес регистрации / Населенный пункт` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 119` | `PDF page 19`; `DOCX row 038` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-007` | `SRC-007.P02` | `WP-01` | `Адрес регистрации / Населенный пункт` | `requiredness` | `Город empty` | Поле обязательно, если не заполнен город. | `no_requirement_code:SRC-007` | `DOCX row 038` | `high` | `none_required:covered` | `ATOM-013` |
| `SRC-008` | `SRC-008.P01` | `WP-01` | `Адрес регистрации / Город` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 120` | `PDF page 19`; `DOCX row 039` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-008` | `SRC-008.P02` | `WP-01` | `Адрес регистрации / Город` | `requiredness` | `Населенный пункт empty` | Поле обязательно, если не заполнен населенный пункт. | `no_requirement_code:SRC-008` | `DOCX row 039` | `high` | `none_required:covered` | `ATOM-014` |
| `SRC-009` | `SRC-009.P01` | `WP-01` | `Адрес регистрации / Улица` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 121` | `PDF page 20`; `DOCX row 040` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-010` | `SRC-010.P01` | `WP-01` | `Адрес регистрации / Дом` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 122` | `PDF page 20`; `DOCX row 041` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-010` | `SRC-010.P02` | `WP-01` | `Адрес регистрации / Дом` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-010` | `DOCX row 041` | `high` | `none_required:covered` | `ATOM-012` |
| `SRC-011` | `SRC-011.P01` | `WP-01` | `Адрес регистрации / Корпус` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 123` | `PDF page 20`; `DOCX row 042` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-011` | `SRC-011.P02` | `WP-01` | `Адрес регистрации / Корпус` | `numeric-format` | `manual = Да` | Возможен ввод только числовых символов. | `BSR 124` | `PDF page 20`; `DOCX row 042` | `medium` | `none_required:covered` | `ATOM-011` |
| `SRC-012` | `SRC-012.P01` | `WP-01` | `Адрес регистрации / Квартира` | `visibility` | `manual = Да` | Поле видно при ручном вводе адреса регистрации. | `BSR 125` | `PDF page 20`; `DOCX row 043` | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-012` | `SRC-012.P02` | `WP-01` | `Адрес регистрации / Квартира` | `numeric-format` | `manual = Да` | Возможен ввод только числовых символов. | `BSR 126` | `PDF page 20`; `DOCX row 043` | `medium` | `none_required:covered` | `ATOM-011` |
| `SRC-012` | `SRC-012.P03` | `WP-01` | `Адрес регистрации / Квартира` | `requiredness` | `private-house = Нет` | Поле обязательно, если клиент не зарегистрирован в частном доме. | `no_requirement_code:SRC-012` | `DOCX row 043` | `high` | `GAP-001` | `ATOM-015` |
| `SRC-013` | `SRC-013.P01` | `WP-01` | `Клиент зарегистрирован в частном доме` | `visibility` | `registration apartment missing` | Флажок отображается, если в адресе регистрации не указан номер квартиры. | `BSR 127` | `PDF page 20`; `DOCX row 044` | `high` | `none_required:covered` | `ATOM-016` |
| `SRC-013` | `SRC-013.P02` | `WP-01` | `Клиент зарегистрирован в частном доме` | `default-value` | `initial` | Значение по умолчанию равно `Нет`. | `BSR 128` | `PDF page 20`; `DOCX row 044` | `high` | `none_required:covered` | `ATOM-017` |
| `SRC-013` | `SRC-013.P03` | `WP-01` | `Клиент зарегистрирован в частном доме` | `hint-behavior` | `checked` | При активации исчезает подсказка о квартире с поля адреса регистрации. | `BSR 129` | `PDF page 20`; `DOCX row 044` | `high` | `none_required:covered` | `ATOM-018` |
| `SRC-014` | `SRC-014.P01` | `WP-02` | `Адрес фактического места жительства совпадает с адресом регистрации` | `visibility` | `always` | Элемент доступен на форме всегда. | `BSR 130` | `PDF page 20`; `DOCX row 045` | `high` | `none_required:covered` | `ATOM-019` |
| `SRC-014` | `SRC-014.P02` | `WP-02` | `Адрес фактического места жительства совпадает с адресом регистрации` | `default-value` | `initial` | Значение по умолчанию равно `Да`. | `BSR 131` | `PDF page 20`; `DOCX row 045` | `high` | `none_required:covered` | `ATOM-020` |
| `SRC-015` | `SRC-015.P01` | `WP-02` | `Адрес фактического места жительства` | `visibility` | `same-as-registration = Нет` | Поле видимо, если фактический адрес не совпадает с адресом регистрации. | `BSR 132` | `PDF page 20`; `DOCX row 046` | `high` | `none_required:covered` | `ATOM-021` |
| `SRC-015` | `SRC-015.P02` | `WP-02` | `Адрес фактического места жительства` | `integration` | `DaData` | Поле интегрировано с DaData. | `BSR 133` | `PDF page 20`; `DOCX row 046` | `high` | `GAP-001` | `ATOM-022` |
| `SRC-015` | `SRC-015.P03` | `WP-02` | `Адрес фактического места жительства` | `address-required-components` | `no apartment / region and house required` | Обязательны регион и дом; отсутствие квартиры вызывает красную подсветку и точную подсказку. | `BSR 134` | `PDF page 20`; `DOCX row 046` | `high` | `none_required:covered` | `ATOM-023` |
| `SRC-015` | `SRC-015.P04` | `WP-02` | `Адрес фактического места жительства` | `validation-message` | `DaData not found` | Для ненайденного адреса выводится текст `Некорректно указан адрес`. | `BSR 135` | `PDF page 20`; `DOCX row 046` | `high` | `none_required:covered` | `ATOM-024` |
| `SRC-015` | `SRC-015.P05` | `WP-02` | `Адрес фактического места жительства` | `decomposition` | `DaData found` | Найденный адрес раскладывается по ручным полям. | `BSR 136` | `PDF page 20`; `DOCX row 046` | `high` | `none_required:covered` | `ATOM-025` |
| `SRC-015` | `SRC-015.P06` | `WP-02` | `Адрес фактического места жительства` | `manual-assembly` | `manual fields filled` | При ручном заполнении адрес собирается из ручных полей в указанном порядке. | `BSR 137` | `PDF page 21`; `DOCX row 046` | `high` | `none_required:covered` | `ATOM-026` |
| `SRC-016` | `SRC-016.P01` | `WP-02` | `Клиент проживает в частном доме` | `visibility` | `same = Нет and apartment missing` | Флажок видим при несовпадении адресов и отсутствии квартиры. | `BSR 138` | `PDF page 21`; `DOCX row 047` | `high` | `none_required:covered` | `ATOM-033` |
| `SRC-016` | `SRC-016.P02` | `WP-02` | `Клиент проживает в частном доме` | `default-value` | `initial` | Значение по умолчанию равно `Нет`. | `BSR 139` | `PDF page 21`; `DOCX row 047` | `high` | `none_required:covered` | `ATOM-034` |
| `SRC-017` | `SRC-017.P01` | `WP-02` | `Фактический адрес / Ввести вручную` | `visibility` | `same = Нет` | Элемент доступен при несовпадении адресов. | `BSR 140` | `PDF page 21`; `DOCX row 048` | `high` | `none_required:covered` | `ATOM-027` |
| `SRC-017` | `SRC-017.P02` | `WP-02` | `Фактический адрес / Ввести вручную` | `default-value` | `initial` | Значение по умолчанию равно `Нет`. | `BSR 141` | `PDF page 21`; `DOCX row 048` | `high` | `none_required:covered` | `ATOM-028` |
| `SRC-018` | `SRC-018.P01` | `WP-02` | `Фактический адрес / Регион` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 142` | `PDF page 21`; `DOCX row 049` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-018` | `SRC-018.P02` | `WP-02` | `Фактический адрес / Регион` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-018` | `DOCX row 049` | `high` | `none_required:covered` | `ATOM-030` |
| `SRC-019` | `SRC-019.P01` | `WP-02` | `Фактический адрес / Район` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 143` | `PDF page 21`; `DOCX row 050` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-020` | `SRC-020.P01` | `WP-02` | `Фактический адрес / Населенный пункт` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 144` | `PDF page 21`; `DOCX row 051` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-021` | `SRC-021.P01` | `WP-02` | `Фактический адрес / Город` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 145` | `PDF page 21`; `DOCX row 052` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-021` | `SRC-021.P02` | `WP-02` | `Фактический адрес / Город` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-021` | `DOCX row 052` | `high` | `none_required:covered` | `ATOM-030` |
| `SRC-022` | `SRC-022.P01` | `WP-02` | `Фактический адрес / Улица` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 146` | `PDF page 21`; `DOCX row 053` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-022` | `SRC-022.P02` | `WP-02` | `Фактический адрес / Улица` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-022` | `DOCX row 053` | `high` | `none_required:covered` | `ATOM-030` |
| `SRC-023` | `SRC-023.P01` | `WP-02` | `Фактический адрес / Дом` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 147` | `PDF page 21`; `DOCX row 054` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-023` | `SRC-023.P02` | `WP-02` | `Фактический адрес / Дом` | `requiredness` | `manual = Да` | Поле обязательно. | `no_requirement_code:SRC-023` | `DOCX row 054` | `high` | `none_required:covered` | `ATOM-030` |
| `SRC-024` | `SRC-024.P01` | `WP-02` | `Фактический адрес / Корпус` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 148` | `PDF page 21`; `DOCX row 055` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-025` | `SRC-025.P01` | `WP-02` | `Фактический адрес / Квартира` | `requiredness` | `private-house = Нет` | Поле обязательно, если клиент не проживает в частном доме. | `BSR 149` | `PDF page 21`; `DOCX row 056` | `high` | `GAP-001` | `ATOM-031` |
| `SRC-025` | `SRC-025.P02` | `WP-02` | `Фактический адрес / Квартира` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 150` | `PDF page 21`; `DOCX row 056` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-025` | `SRC-025.P03` | `WP-02` | `Фактический адрес / Квартира` | `numeric-format` | `manual = Да` | Возможен ввод только числовых символов. | `BSR 151` | `PDF page 21`; `DOCX row 056` | `medium` | `none_required:covered` | `ATOM-032` |
| `SRC-026` | `SRC-026.P01` | `WP-02` | `Фактический адрес / Почтовый индекс` | `visibility` | `manual = Да` | Поле видно при ручном вводе фактического адреса. | `BSR 152` | `PDF page 21`; `DOCX row 057` | `high` | `none_required:covered` | `ATOM-029` |
| `SRC-026` | `SRC-026.P02` | `WP-02` | `Фактический адрес / Почтовый индекс` | `numeric-format` | `manual = Да` | Ограничение на формат: только 6 числовых символов. | `BSR 153` | `PDF page 21`; `DOCX row 057` | `medium` | `none_required:covered` | `ATOM-032` |
| `SRC-002`; `SRC-015` | `SRC-DADATA-KLADR` | `WP-01`; `WP-02` | Адрес из DaData | `model-data` | `kladr` | При выборе адреса из DaData в модели данных заполняется `kladr`. | `BSR 325` | `FT4AutoFinFinal` | `high` | `none_required:covered` | `ATOM-035` |

## Numeric and length applicability

- source_path: `fts/AutoFin/work/test-design/14-application-card-client-addresses/test-design-applicability-matrix.md`
- source_sha256: `9850d04706946216cf1ac6c314dc5ddad72da8e4d6ae806462189df632392c1c`
- selectors: `full-explicit`

# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `conditional-visibility` | `yes` | `BSR 113`; `BSR 127`; `BSR 132`; `BSR 138`; `BSR 140` | Selected rows define source-backed visibility/availability conditions for address fields and private-house flags; unsupported inverse branches are not treated as separate obligations. | `ATOM-008`; `ATOM-016`; `ATOM-021`; `ATOM-027`; `ATOM-033` | `TC-ACCA-001`; `TC-ACCA-012`; `TC-ACCA-015`; `TC-ACCA-024` |  |
| `dependency` | `yes` | `BSR 109`; `BSR 129`; `BSR 134`; DOCX O-column | Apartment/private-house flags and city/settlement conditions affect hints or required markers; source-backed positive/dependency branches are covered. | `ATOM-004`; `ATOM-013`; `ATOM-014`; `ATOM-015`; `ATOM-018`; `ATOM-023`; `ATOM-031` | `TC-ACCA-009`; `TC-ACCA-011`; `TC-ACCA-013`; `TC-ACCA-023` | `GAP-001` |
| `equivalence` | `yes` | `BSR 109`; `BSR 110`; `BSR 134`; `BSR 135`; numeric rows | Source-backed positive and negative classes exist for found/not-found address and numeric-only fields. | `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-011`; `ATOM-022`; `ATOM-023`; `ATOM-024`; `ATOM-032` | `TC-ACCA-002`; `TC-ACCA-003`; `TC-ACCA-004`; `TC-ACCA-010`; `TC-ACCA-016`; `TC-ACCA-017`; `TC-ACCA-018`; `TC-ACCA-022` | `GAP-001`; `GAP-002` |
| `numeric` | `yes` | `BSR 116`; `BSR 124`; `BSR 126`; `BSR 151`; `BSR 153` | Postal index and some manual address fields have numeric restrictions. | `ATOM-011`; `ATOM-032` | `TC-ACCA-010`; `TC-ACCA-022` | `GAP-002` |
| `length` | `yes` | `BSR 116`; `BSR 153` | Postal index has exact 6-digit source restriction; invalid boundary behavior is not described. | `ATOM-011`; `ATOM-032` |  | `GAP-002` |
| `integration` | `yes_with_evidence` | `BSR 108`; `BSR 133`; `BSR 325` | DaData UI selection is covered; `kladr` model-data fill is covered with API/DB/log evidence; sorting, debounce, retry and partial-match behavior are not defined. | `ATOM-003`; `ATOM-022`; `ATOM-035` | `TC-ACCA-002`; `TC-ACCA-016`; `TC-ACCA-026` | `GAP-001:undefined-extra-dadata-mechanics` |
| `expected-result` | `yes` | `BSR 110`; `BSR 129`; `BSR 135` | Several rows define exact observable hint/message texts. | `ATOM-005`; `ATOM-018`; `ATOM-024` | `TC-ACCA-003`; `TC-ACCA-013`; `TC-ACCA-017` |  |
| `scope` | `no` | `scope-contract.md` | Action `Далее`, contacts, documents, participants, employment, visual assessment and consents are explicitly out of scope. | `-` |  |  |

## Negative-oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/34-client-address-numeric-boundary-canary/scope-coverage-gaps.md`
- source_sha256: `4dcc3d4b3efad079c7281671ad4c68ce84f4852d99bf250ce88f26b40d2ce8ce`
- selectors: `full-explicit`

# Пробелы покрытия

## GAP-NUM-001

- Статус: `open`, `non-blocking`.
- Источник: `GAP-002`; section 4.3 Table 4; `SRC-004.P02`, `SRC-011.P02`, `SRC-012.P02`, `SRC-025.P03`, `SRC-026.P02`; `BSR 116`, `BSR 124`, `BSR 126`, `BSR 151`, `BSR 153`.
- Утверждение ФТ: выбранные поля допускают только числовые символы; почтовые индексы имеют длину ровно шесть цифр.
- Недостающее поведение: ФТ не определяет наблюдаемый результат для букв, пробелов, спецсимволов, знака, десятичного разделителя и неверной длины индекса.
- Обработка: генерировать только проверки допустимых значений; не утверждать фильтрацию, ошибку или блокировку перехода.
- Writer/reviewer rule: каждый testable obligation сохраняет `constraint_gap_ids: [GAP-NUM-001]`; gap не превращается в негативный TC.

## Atomic obligations

```json
{
  "coverage_gaps": [
    {
      "blocking": false,
      "gap_id": "GAP-NUM-001",
      "handling": "Покрывать только допустимые значения; не создавать negative TC без UI evidence или уточнения требования.",
      "problem": "ФТ задаёт допустимый числовой формат, но не описывает наблюдаемую реакцию на невалидные символы или неверную длину.",
      "source_refs": [
        "GAP-002",
        "SRC-004.P02",
        "SRC-011.P02",
        "SRC-012.P02",
        "SRC-025.P03",
        "SRC-026.P02"
      ]
    }
  ],
  "digest": "e3f1a6a24d9ec7530b68fdd902f940f30e84d8e00d37b2684c2af25514e9c17f",
  "obligations": [
    {
      "atom_id": "ATOM-NUM-001",
      "atomic_statement": "Поле `Адрес регистрации / Почтовый индекс` допускает ровно 6 числовых символов.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Не проверять неподтверждённую реакцию на неверную длину или нецифровые символы.",
      "obligation_id": "OBL-NUM-001",
      "observable_oracle": "После ввода допустимого значения `123456` поле отображает ровно эти 6 цифр.",
      "planned_test_case_id": "TC-ACNB-001",
      "source_refs": [
        "SRC-004.P02",
        "BSR 116"
      ],
      "test_intent": "Проверить допустимое шестизначное числовое значение почтового индекса адреса регистрации."
    },
    {
      "atom_id": "ATOM-NUM-002",
      "atomic_statement": "Поле `Адрес регистрации / Корпус` допускает только числовые символы.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Длина значения источником не ограничена.",
      "obligation_id": "OBL-NUM-002",
      "observable_oracle": "После ввода допустимого значения `12` поле отображает ровно эти цифры.",
      "planned_test_case_id": "TC-ACNB-002",
      "source_refs": [
        "SRC-011.P02",
        "BSR 124"
      ],
      "test_intent": "Проверить допустимое числовое значение корпуса адреса регистрации."
    },
    {
      "atom_id": "ATOM-NUM-003",
      "atomic_statement": "Поле `Адрес регистрации / Квартира` допускает только числовые символы.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Длина значения источником не ограничена.",
      "obligation_id": "OBL-NUM-003",
      "observable_oracle": "После ввода допустимого значения `34` поле отображает ровно эти цифры.",
      "planned_test_case_id": "TC-ACNB-003",
      "source_refs": [
        "SRC-012.P02",
        "BSR 126"
      ],
      "test_intent": "Проверить допустимое числовое значение квартиры адреса регистрации."
    },
    {
      "atom_id": "ATOM-NUM-004",
      "atomic_statement": "Поле `Фактический адрес / Квартира` допускает только числовые символы.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Длина значения источником не ограничена.",
      "obligation_id": "OBL-NUM-004",
      "observable_oracle": "После ввода допустимого значения `56` поле отображает ровно эти цифры.",
      "planned_test_case_id": "TC-ACNB-004",
      "source_refs": [
        "SRC-025.P03",
        "BSR 151"
      ],
      "test_intent": "Проверить допустимое числовое значение квартиры фактического адреса."
    },
    {
      "atom_id": "ATOM-NUM-005",
      "atomic_statement": "Поле `Фактический адрес / Почтовый индекс` допускает ровно 6 числовых символов.",
      "constraint_gap_ids": [],
      "coverage_status": "testable",
      "dictionary_refs": [],
      "gap_id": "",
      "notes": "Не проверять неподтверждённую реакцию на неверную длину или нецифровые символы.",
      "obligation_id": "OBL-NUM-005",
      "observable_oracle": "После ввода допустимого значения `654321` поле отображает ровно эти 6 цифр.",
      "planned_test_case_id": "TC-ACNB-005",
      "source_refs": [
        "SRC-026.P02",
        "BSR 153"
      ],
      "test_intent": "Проверить допустимое шестизначное числовое значение почтового индекса фактического адреса."
    },
    {
      "atom_id": "ATOM-NUM-006",
      "atomic_statement": "ФТ не определяет наблюдаемую реакцию выбранных полей на нецифровые символы и неверную длину почтового индекса.",
      "constraint_gap_ids": [],
      "coverage_status": "gap",
      "dictionary_refs": [],
      "gap_id": "GAP-NUM-001",
      "notes": "Gap-obligation сохраняет отрицательную границу без выбора неподтверждённого механизма.",
      "obligation_id": "OBL-NUM-006",
      "observable_oracle": "",
      "source_refs": [
        "GAP-002",
        "SRC-004.P02",
        "SRC-011.P02",
        "SRC-012.P02",
        "SRC-025.P03",
        "SRC-026.P02"
      ],
      "test_intent": "Не создавать негативный тест-кейс до появления UI evidence или уточнения требования."
    }
  ],
  "package_id": "client-address-numeric-boundaries-v2",
  "package_version": 5
}
```

## Deterministic gate summaries

```json
[
  {
    "gate": "structure",
    "passed": true,
    "validator": "codex_review_cycle_runner.evaluate_test_case_markdown_structure",
    "findings_count": 0
  },
  {
    "gate": "seed",
    "passed": true,
    "validator": "prepared-draft-seed-gate-v1",
    "findings_count": 0
  },
  {
    "gate": "obligation",
    "passed": true,
    "validator": "prepared-package-obligation-gate-v2",
    "findings_count": 0,
    "test_case_count": 5,
    "testable_obligations": 5,
    "covered_obligations": [
      "OBL-NUM-001",
      "OBL-NUM-002",
      "OBL-NUM-003",
      "OBL-NUM-004",
      "OBL-NUM-005"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 5
  },
  {
    "gate": "writer-evidence-access",
    "passed": true,
    "validator": "prepared-evidence-access-gate-v1",
    "findings_count": 0,
    "commands_checked": 0,
    "fallback_authorizations": 0
  },
  {
    "gate": "quality-bundle",
    "passed": true,
    "validator": "prepared-quality-gate-bundle-v1",
    "findings_count": 0,
    "test_case_count": 5
  }
]
```

## Semantic overlap diagnostic (non-blocking, reviewer classification required)

```json
{
  "passed": true,
  "validator": "semantic-overlap-diagnostic-v1",
  "status": "clean",
  "blocking": false,
  "test_case_count": 5,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\client-address-numeric-boundary-shadow-v2-20260713\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle

```json
{
  "version": 1,
  "context_profile": "numeric-date-boundary",
  "items": [],
  "open_count": 0,
  "resolved_count": 0
}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-ACNB-001

**Название:** Ввод шестизначного числового почтового индекса адреса регистрации
**Тип:** позитивный
**Приоритет:** средний
**package_id:** client-address-numeric-boundaries-v2
**Трассировка:** OBL-NUM-001; ATOM-NUM-001; SRC-004.P02; BSR 116
**Ограничение покрытия:** GAP-NUM-001 — реакция на неверную длину и нецифровые символы не определена ФТ.

### Предусловия

1. Открыта карточка заявки; для адреса регистрации включён ручной ввод (`Ввести вручную` = `Да`).

### Тестовые данные

- Почтовый индекс: `123456`.

### Шаги

1. Ввести `123456` в поле `Адрес регистрации / Почтовый индекс`.

### Итоговый ожидаемый результат

Поле `Адрес регистрации / Почтовый индекс` отображает ровно 6 цифр `123456`.

### Постусловия

- Не применимо.

## TC-ACNB-002

**Название:** Ввод числового значения корпуса адреса регистрации
**Тип:** позитивный
**Приоритет:** средний
**package_id:** client-address-numeric-boundaries-v2
**Трассировка:** OBL-NUM-002; ATOM-NUM-002; SRC-011.P02; BSR 124
**Ограничение покрытия:** GAP-NUM-001 — реакция на неверную длину и нецифровые символы не определена ФТ.

### Предусловия

1. Открыта карточка заявки; для адреса регистрации включён ручной ввод (`Ввести вручную` = `Да`).

### Тестовые данные

- Корпус: `12`.

### Шаги

1. Ввести `12` в поле `Адрес регистрации / Корпус`.

### Итоговый ожидаемый результат

Поле `Адрес регистрации / Корпус` отображает ровно цифры `12`.

### Постусловия

- Не применимо.

## TC-ACNB-003

**Название:** Ввод числового значения квартиры адреса регистрации
**Тип:** позитивный
**Приоритет:** средний
**package_id:** client-address-numeric-boundaries-v2
**Трассировка:** OBL-NUM-003; ATOM-NUM-003; SRC-012.P02; BSR 126
**Ограничение покрытия:** GAP-NUM-001 — реакция на неверную длину и нецифровые символы не определена ФТ.

### Предусловия

1. Открыта карточка заявки; для адреса регистрации включён ручной ввод (`Ввести вручную` = `Да`).

### Тестовые данные

- Квартира: `34`.

### Шаги

1. Ввести `34` в поле `Адрес регистрации / Квартира`.

### Итоговый ожидаемый результат

Поле `Адрес регистрации / Квартира` отображает ровно цифры `34`.

### Постусловия

- Не применимо.

## TC-ACNB-004

**Название:** Ввод числового значения квартиры фактического адреса
**Тип:** позитивный
**Приоритет:** средний
**package_id:** client-address-numeric-boundaries-v2
**Трассировка:** OBL-NUM-004; ATOM-NUM-004; SRC-025.P03; BSR 151
**Ограничение покрытия:** GAP-NUM-001 — реакция на неверную длину и нецифровые символы не определена ФТ.

### Предусловия

1. Открыта карточка заявки; указано, что фактический адрес не совпадает с адресом регистрации (`Адрес фактического места жительства совпадает с адресом регистрации` = `Нет`), и для фактического адреса включён ручной ввод (`Ввести вручную` = `Да`).

### Тестовые данные

- Квартира: `56`.

### Шаги

1. Ввести `56` в поле `Фактический адрес / Квартира`.

### Итоговый ожидаемый результат

Поле `Фактический адрес / Квартира` отображает ровно цифры `56`.

### Постусловия

- Не применимо.

## TC-ACNB-005

**Название:** Ввод шестизначного числового почтового индекса фактического адреса
**Тип:** позитивный
**Приоритет:** средний
**package_id:** client-address-numeric-boundaries-v2
**Трассировка:** OBL-NUM-005; ATOM-NUM-005; SRC-026.P02; BSR 153
**Ограничение покрытия:** GAP-NUM-001 — реакция на неверную длину и нецифровые символы не определена ФТ.

### Предусловия

1. Открыта карточка заявки; указано, что фактический адрес не совпадает с адресом регистрации (`Адрес фактического места жительства совпадает с адресом регистрации` = `Нет`), и для фактического адреса включён ручной ввод (`Ввести вручную` = `Да`).

### Тестовые данные

- Почтовый индекс: `654321`.

### Шаги

1. Ввести `654321` в поле `Фактический адрес / Почтовый индекс`.

### Итоговый ожидаемый результат

Поле `Фактический адрес / Почтовый индекс` отображает ровно 6 цифр `654321`.

### Постусловия

- Не применимо.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
