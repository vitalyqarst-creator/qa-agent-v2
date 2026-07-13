# Prepared Source Evidence

- package_id: `visual-assessment-conditional-v2`

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

## Conditional canary boundary

- source_path: `fts/AutoFin/work/stage-handoffs/35-visual-assessment-conditional-canary/scope-contract.md`
- source_sha256: `77b4a0168b166357fe7bb085e3cd5a049af1d1212d3d978b13933eed4ccedca7`
- selectors: `full-explicit`

# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`.
- Активный source set: `source/FT4AutoFinFinal.docx`, `.xhtml`, `.pdf`.
- Родительский подтверждённый scope: `visual-assessment-criteria` внутри карточки заявки.
- Текущий canary — внутренний conditional-state пакет, не новый внешний scope.

## Scope Identity

- `scope_slug`: `visual-assessment-conditional-state-shadow`.
- Разделы: `4.3` / Table 4 и Appendix 1 только как dependency dictionary.
- Цель: проверить standard structured pipeline на наблюдаемых переходах состояния поля визуальной оценки.

## Что Входит В Scope

- Начальное значение `Визуальная информация = Нет`, `SRC-002.P02`, `BSR 312`.
- Показ списка при `Визуальная информация = Да`, `SRC-003.P01`, `BSR 314`.
- Скрытие списка при `Визуальная информация = Нет`, `SRC-003.P02`, `BSR 314`.
- Показ комментария при выборе `Другое` в категории `Признаки алкоголика`, `SRC-003.P06`, `BSR 317`, `DICT-101`.
- Одновременный выбор двух обычных значений, `SRC-003.P08`, `BSR 313`, `BSR 315`, `DICT-101`.

## Что Не Входит В Scope

- Полнота всех восьми категорий и всех значений `DICT-001`.
- Standalone-поля `Комментарий` из Appendix 1.
- Неподтверждённый механизм requiredness для пустого списка и пустого комментария `Другое`.
- Persistence, scoring, status changes, production promotion и изменение baseline.

## Разрешённые Источники

- Только Final source set, package notes и перечисленные current-source design artifacts.
- `AutoFinPreFinal.*`, production TC и предыдущие generated drafts запрещены как requirement evidence.

## Условие Старта

- Immutable package v5: 5 testable obligations и 1 non-blocking gap-obligation.
- Validate-only выбирает `conditional-state` и подтверждает production boundary.
- Один live exec cycle, без SDK fallback.

## Final source parity

- source_path: `fts/AutoFin/work/stage-handoffs/35-visual-assessment-conditional-canary/source-parity-check.md`
- source_sha256: `3a9107406e36d61a8b8718436a46ffd4ce09c1afcd20944290396caac80278cc`
- selectors: `full-explicit`

# Source Parity Check

## Контекст

- Source set: `FT4AutoFinFinal.docx`, `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.pdf`.
- Current design anchors: `work/test-design/section-18-visual-assessment-criteria/source-row-inventory.md` и `source-table-normalization.md`.
- Проверяемые коды: `BSR 312`, `BSR 313`, `BSR 314`, `BSR 315`, `BSR 316`, `BSR 317`.

## Результат

| проверка | результат |
| --- | --- |
| XHTML содержит выбранные Table 4 свойства и Appendix 1 values | `pass` |
| PDF подтверждает Final BSR-коды и структуру | `pass` |
| DOCX сохранён как source of truth | `pass` |
| Старые PreFinal-коды `BSR 304–309` исключены из canary | `pass` |
| Blocking parity issue | `none` |

## Ограничения

- Appendix 1 используется только для конкретных fixtures `DICT-101`.
- PDF не является источником нового поведения.

## Selected state and fixture rows

- source_path: `fts/AutoFin/work/stage-handoffs/35-visual-assessment-conditional-canary/source-row-inventory.md`
- source_sha256: `1a5048acfabf149060f587d25017f14b0067f148f60cd084ae232cbc78d1f8b5`
- selectors: `full-explicit`

# Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-002` | `WP-COND` | Поле `Визуальная информация`: default и multiple-selection trigger | `SRC-002.P02`; `SRC-002.P04`; DOCX Table 4 | `BSR 312`; `BSR 313` | `yes` | canonical `ATOM-002`; `ATOM-013`; canary `ATOM-COND-001`; `ATOM-COND-005` |
| `SRC-003` | `WP-COND` | Список `Параметры визуальной оценки`: show/hide, `Другое`, requiredness | `SRC-003.P01`; `SRC-003.P02`; `SRC-003.P05`..`SRC-003.P08`; DOCX Table 4 | `BSR 314`; `BSR 315`; `BSR 316`; `BSR 317` | `yes` | canonical `ATOM-004`; `ATOM-005`; `ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-013`; canary `ATOM-COND-002`..`ATOM-COND-006`; `GAP-COND-001` |
| `SRC-005` | `WP-COND` | Fixture: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-005` | `yes` | canonical `ATOM-006`; `ATOM-007`; canary `ATOM-COND-005` |
| `SRC-006` | `WP-COND` | Fixture: `Отечность, нездоровый цвет лица, синяки под глазами` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-006` | `yes` | canonical `ATOM-006`; `ATOM-007`; canary `ATOM-COND-005` |
| `SRC-009` | `WP-COND` | Fixture: `Другое (комментарий обязателен)` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-009` | `yes` | canonical `ATOM-006`; `ATOM-009`; canary `ATOM-COND-004`; `GAP-COND-001` |

## Final conditional properties

- source_path: `fts/AutoFin/work/test-design/section-18-visual-assessment-criteria/source-table-normalization.md`
- source_sha256: `3621b2e1ac37592e43afd1758019a8f1ff9107a0fa032fa83adf65b4df58ec5b`
- selectors: `full-explicit`

# Source Table Normalization

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-002` | `SRC-002.P01` | `WP-01` | Поле `Визуальная информация` | `visibility` | always | Поле `Визуальная информация` отображается всегда. | `BSR 311` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-001` |
| `SRC-002` | `SRC-002.P02` | `WP-01` | Поле `Визуальная информация` | `default-value` | initial open | Значение по умолчанию равно `Нет`. | `BSR 312` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-002` |
| `SRC-002` | `SRC-002.P03` | `WP-01` | Поле `Визуальная информация` | `dependency-trigger` | user selects `Да` | Выбор значения `Да` является условием показа параметров визуальной оценки. | `BSR 313` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-003` |
| `SRC-002` | `SRC-002.P04` | `WP-01` | visual-assessment-trigger | `multiple-selection-capability` | user selects `Да` | Displayed visual-assessment parameters list supports multiple selection. | `BSR 313` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-013` |
| `SRC-003` | `SRC-003.P01` | `WP-01` | visual-assessment-parameters-list | `conditional-visibility` | `Визуальная информация = Да` | Dependent list is available. | `BSR 314` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-004` |
| `SRC-003` | `SRC-003.P02` | `WP-01` | visual-assessment-parameters-list | `conditional-visibility` | `Визуальная информация = Нет` | Dependent list is unavailable. | `BSR 314` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-005` |
| `SRC-003` | `SRC-003.P03` | `WP-01` | `Параметры визуальной оценки` | `table-list` | `Визуальная информация = Да` | Список использует активные группы и значения из `DICT-001`. | `BSR 315` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-006` |
| `SRC-003` | `SRC-003.P04` | `WP-01` | Значения `Параметры визуальной оценки` | `checkbox-list` | `Визуальная информация = Да` | Каждое обычное значение критерия доступно как checkbox value. | `BSR 315` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-007` |
| `SRC-003` | `SRC-003.P05` | `WP-01` | `Параметры визуальной оценки` | `requiredness` | `Визуальная информация = Да` | Для списка требуется минимум одно выбранное значение. | `BSR 316` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-008` |
| `SRC-003` | `SRC-003.P06` | `WP-01` | Checkbox `Другое` | `conditional-input-display` | `Другое` selected | Выбор `Другое` отображает текстовое поле комментария для этого блока. | `BSR 317` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-009` |
| `SRC-003` | `SRC-003.P07` | `WP-01` | Comment for `Другое` | `requiredness` | `Другое` comment | Комментарий для `Другое` обязателен. | `BSR 317` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-010` |
| `SRC-010` | `SRC-010.P01` | `WP-01` | Standalone `Комментарий` rows | `text-input` | rows clarified by answer | Строки `Комментарий` являются отдельными полями ввода, не checkbox values. | `GAP-001:closed` | DOCX section-18; PDF p.39 | `high` | `GAP-001:closed` | `ATOM-011` |
| `SRC-010` | `SRC-010.P02` | `WP-01` | Standalone `Комментарий` rows | `text-input-edit` | rows clarified by analyst answer | Standalone поле `Комментарий` принимает введенный текст. | `GAP-001:closed` | DOCX section-18; PDF p.39 | `high` | `GAP-001:closed` | `ATOM-012` |
| `SRC-003` | `SRC-003.P08` | `WP-01` | Значения `Параметры визуальной оценки` | `checkbox-list` | multiple ordinary values selected | Несколько обычных значений критериев могут быть выбраны одновременно. | `BSR 315` | DOCX section-14 table 7 rows 130-132; PDF p.33 | `high` | `none_required:covered` | `ATOM-013` |

## Final DICT-101 fixtures

- source_path: `fts/AutoFin/work/test-design/section-18-visual-assessment-criteria/dictionary-inventory.md`
- source_sha256: `7680865334ec351f2743dfd58c99456925ba842d78c6b6f75e8381340bb3f208`
- selectors: `full-explicit`

# Dictionary Inventory

| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DICT-001 | Параметры визуальной оценки | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | DICT-101`; `DICT-102`; `DICT-103`; `DICT-104`; `DICT-105`; `DICT-106`; `DICT-107`; `DICT-108 | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Parent inventory row; child category rows preserve the complete source values. |
| DICT-101 | Признаки алкоголика | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`; `Отечность, нездоровый цвет лица, синяки под глазами`; `Шатающаяся походка, несвязная речь, сильно трясутся руки`; `Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-102 | Признаки наркомана | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Длинные, спущенные рукава в любую погоду, отрешенный взгляд`; `Неоправданно резкие перемены настроения`; `Отечность, нездоровый цвет лица, синяки под глазами`; `Следы многочисленных уколов на кистях`; `Неестественно суженные / расширенные зрачки`; `Шатающаяся походка, несвязная речь, плохая координация движений`; `Неприятный запах кислоты`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-103 | Признаки бывшего заключенного | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Татуировки уголовного содержания на кистях, пальцах (например, с изображением перстней, крестов, четырех точек, образующих квадрат с пятой точкой посередине и др.)`; `Характерный для заключенных жаргон`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-104 | Признаки «преображенного» бомжа | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Несоответствие внешнего вида Клиента данным, которые он указывает в анкете (например, в анкете указано, что Клиент - гендиректор крупной организации, однако состояние зубов, волос, лица или кистей рук говорит о том, что ему полностью безразличны его внешний вид и здоровье)`; `Признаки алкоголика / наркомана / бывшего заключенного`; `Несоответствие размеров / стиля одежды`; `Сильный макияж / использует парик`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-105 | Поведенческие признаки потенциального неплательщика | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Клиент не может внятно объяснить, откуда он узнал о Банке / для чего ему необходим кредит, при этом испытывает волнение / раздражение`; `Мнимые семейные пары, часто с детьми (например Клиент называет свою "супругу" Надей, а в штампе паспорта имя супруги - Елена); неадекватная реакция на вопросы о супруге / детях`; `Сильное волнение клиента в ходе анкетирования, особенно при ответах на дополнительные / уточняющие вопросы`; `Слишком заострено внимание на последствиях неплатежей`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-106 | Сопровождение Клиента | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки по заполнению анкеты`; `Клиент находится в сопровождении подозрительных лиц, осуществляющих давление на Клиента`; `Клиент использовал "шпаргалку" при заполнении анкеты`; `Клиент неоднократно звонил по телефону для выяснения ответов на вопросы анкеты`; `Клиент замечен в сопровождении лиц, ранее приводивших мошенников / подставных лиц для получения кредитов`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-107 | Признаки подделки документов | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | Заметны следы подчистки документов, химического травления текста`; `Заметны следы подделки подписей, оттисков печатей и штампов`; `Наличие в документах дописок, допечаток, исправлений, орфографических ошибок`; `Личность заемщика не может быть достоверно подтверждена (заемщик явно не похож по фотографии)`; `Заметны следы замены фотографии в паспорте, листов в многостраничных документах`; `Другое (комментарий обязателен) | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | none_required:covered | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-108 | Прочие признаки (комментарий обязателен) | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md` | extracted | none_required:standalone-comment-only | none_required:no-archived-values | SRC-003.P03; SRC-003.P04; SRC-003.P06; SRC-003.P07; SRC-010.P01; SRC-010.P02 | GAP-001:closed | Standalone `Комментарий` rows are input fields when `has_comment = yes`. Child category of `DICT-001`. |
| DICT-002 | Согласия/Проверки | source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf | Приложение 2; aggregate reference `work/test-design/14-application-card/appendix-2-consents-checks-reference.md` | extracted | APP2-CHECK-001; APP2-CHECK-002; APP2-CHECK-003 | none_required:no-archived-values | SRC-005; SRC-006; SRC-007 | none_required:covered | Полный состав подблоков и полей хранится в aggregate reference. |

## Requiredness feedback boundary

- source_path: `fts/AutoFin/work/stage-handoffs/35-visual-assessment-conditional-canary/scope-coverage-gaps.md`
- source_sha256: `553a01d30d2a72f82ee2515fca7981f922bc319d00c719b9d1abda9459117103`
- selectors: `full-explicit`

# Пробелы покрытия

## GAP-COND-001

- Статус: `open`, `non-blocking`.
- Источник: `SRC-003.P05`, `SRC-003.P07`; `BSR 316`, `BSR 317`.
- Утверждение ФТ: требуется минимум один параметр; комментарий при выбранном `Другое` обязателен.
- Недостающее поведение: не определены текст/подсветка ошибки, момент валидации и блокируемое действие.
- Обработка: не создавать negative TC до UI evidence или уточнения требований; сохранить отдельной gap-obligation.
- Не влияет на позитивные state-transition cases.
