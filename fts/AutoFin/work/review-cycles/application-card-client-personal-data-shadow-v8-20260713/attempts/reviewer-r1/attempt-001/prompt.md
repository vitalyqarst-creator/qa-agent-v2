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
  "package_id": "application-card-client-personal-data-v8",
  "ft_slug": "AutoFin",
  "scope_slug": "application-card-client-personal-data",
  "section_id": "14",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "dependency-state",
    "input-boundaries",
    "integration-persistence",
    "numeric-boundaries"
  ],
  "reviewed_draft_sha256": "cd8cf5c8ab9cedfe5d2358e9f13a1341d12eb8805f62430f6fee63aabd8f5884"
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
6. Reject invented UI, literals, messages, API/DB effects or internal state; validate dictionary claims against projected `active_values`.
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

## Context profile: `character-restriction-calibration`

- Keep each invalid class and field independent.
- For obligations with constraint_gap_ids, preserve every GAP-* marker and label the case candidate-ui-calibration.
- Do not choose a validation message, filtering, highlight, save or transition mechanism that the evidence does not define.

## Selected source evidence

# Prepared Source Evidence

- package_id: `application-card-client-personal-data-v8`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/prepared-input/.application-card-client-personal-data-v8.compiled-evidence.md`
- source_sha256: `7eef8f58e646b95017359e3d7388f970707911b0a29c1fc2c078b1c456dbc3d0`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## Mandatory package context

source_path: fts/AutoFin/AGENT-NOTES.md

# Package Notes: AutoFin

## Сокращения В Таблицах UI-Полей

Статус: package-specific рабочее правило для AutoFin, добавленное по подтверждению пользователя и сверенное с аналогичными заметками в `fts/ft-2-OF_16/AGENT-NOTES.md`, `fts/ft-2-OF_17/AGENT-NOTES.md`, `fts/ft-2-OF_18/AGENT-NOTES.md`.

В таблицах описания свойств полей формы столбец `О` означает `Обязательность`, а столбец `Р` означает `Редактируемость`.

## Внешний Контекст: DaData На Интерфейсе

Источник и статус:

- Эта секция перенесена как справочный контекст из package notes `ft-2-OF_16`, `ft-2-OF_17`, `ft-2-OF_18`.
- В исходных заметках секция основана на публичной документации DaData, просмотренной `2026-06-03`.
- Это не источник новых требований ФТ и не замена основного ФТ/support-файлов AutoFin.
- Использовать только как справочный контекст для формулировки ручных UI-шагов и рисков, когда само ФТ AutoFin уже говорит, что поле интегрировано с DaData.
- Не добавлять в тест-кейсы поведение, которого нет в ФТ, support-файлах или подтвержденных UI evidence.

Официальные источники:

- `https://dadata.ru/api/suggest/` - общий API подсказок: помогает человеку быстро вводить корректные данные в формах; поддерживает ФИО, адреса, "Кем выдан паспорт" и другие справочники.
- `https://dadata.ru/api/suggest/address/` - подсказки по адресам: пользователь вводит часть адреса, сервис возвращает варианты; выбор конкретного адреса в API моделируется запросом `count = 1` по ранее возвращенному `unrestricted_value`.
- `https://dadata.ru/api/suggest/name/` - подсказки по ФИО: подсказывает ФИО одной строкой или отдельно фамилию, имя, отчество; может исправлять раскладку и определять пол, но не гарантирует автоматическую обработку без участия человека.
- `https://dadata.ru/api/suggest/fms_unit/` - подсказки "Кем выдан паспорт": поиск работает по коду подразделения и названию, результат содержит значение для списка, код подразделения и название подразделения.
- `https://support.dadata.ru/knowledge-bases/4/articles/7767-chto-schitaetsya-zaprosom-v-podskazkah` - виджет подсказок может отправлять запрос на каждый вводимый символ; количество запросов зависит от типа поля.

Практическая модель для ручных UI-шагов:

- Пользователь начинает вводить значение в поле, связанное с DaData.
- Интерфейс показывает список подсказок, если интеграция доступна и по введенному тексту есть варианты.
- Пользователь выбирает одну подсказку из списка; после выбора поле или связанные поля могут заполниться значениями из выбранной подсказки.
- Для паспортного подразделения подсказка может искаться по коду подразделения или названию подразделения.
- Для адреса выбранная подсказка может использоваться как источник разложения адреса на компоненты, если такое разложение прямо задано ФТ.
- Для ФИО подсказка может использоваться как ввод одной строкой или по отдельным частям ФИО, если такая форма прямо задана ФТ.

Ограничения для тест-дизайна:

- Не считать внутренние API-запросы, сохранение `kladr`, `esiaUserId`, `CorrelationId`, persistence/model changes или RabbitMQ/API effects покрытыми через UI без наблюдаемого артефакта.
- Не придумывать минимальное количество символов для запуска подсказок, debounce, порядок сортировки, точный вид dropdown, тексты ошибок DaData, fallback при недоступности сервиса или правила retry, если это не описано в ФТ/support/evidence.
- Не использовать публичную документацию DaData как основание менять обязательность, редактируемость, видимость, allowed values или expected results полей ФТ.
- Если UI-прогон показывает конкретное поведение виджета DaData, фиксировать это отдельно в UI evidence / UI-AGENT-NOTES и отличать от требований ФТ.

## Portable fixture contracts

- `FIX-ACPD-PORTABLE-SAVE-001`: открыть новую карточку действием создания заявки из BSR 38; заполнить in-scope поля синтетическими значениями `Фамилия=Иванов`, `Имя=Иван`, `Пол=Мужчина`, `Дата рождения=D-30y`, `Клиент менял ФИО=Нет`, кроме поля — цели конкретного кейса. Поля вне выбранного scope связываются с source-backed данными соответствующих scope при UI-prep. Существующий ID заявки, локатор и заранее сохранённая запись не требуются для FT-first draft.
- `FIX-ACPD-RUNTIME-DADATA-001`: ввести синтетический префикс `Иван`, выбрать из фактически возвращённых подсказок вариант с доступными составными частями ФИО и известным непустым полом; до выбора записать исходный `Пол`, после выбора сравнить видимый `Пол` со значением выбранной подсказки. Конкретный текст и порядок динамических подсказок заранее не фиксируются.

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. This compact projection contains every exact review-contract ID plus its source-backed statement, oracle, intent, reference and gap; the runner validates the final contract against the immutable artifact.

```json
{"artifact":"fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/prepared-input/application-card-client-personal-data-v8/atomic-obligations.json","artifact_sha256":"1f9f8dbe01e984f9a95ff6a77c1a877f2765220b753780cbde4757b7c8fb2974","obligation_count":65,"semantic_evidence_source":"selected-source-evidence","coverage_gaps":[{"gap_id":"GAP-001","source_refs":["SRC-002..SRC-004","SRC-007","SRC-009..SRC-011","ATOM-005","ATOM-010","ATOM-015","ATOM-022","ATOM-023","ATOM-024","ATOM-025","ATOM-030","ATOM-035","ATOM-040"],"problem":"`BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition.","blocking":false},{"gap_id":"GAP-002","source_refs":["SRC-002","SRC-003","SRC-006","SRC-007","SRC-009..SRC-011","ATOM-003","ATOM-008","ATOM-019","ATOM-021","ATOM-031","ATOM-036","ATOM-041"],"problem":"Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.","handling":"Preserve requiredness calibration candidates and do not infer a message or save behavior.","blocking":false},{"gap_id":"GAP-003","source_refs":["SRC-002..SRC-006","SRC-009..SRC-011","ATOM-006","ATOM-011","ATOM-016","ATOM-018","ATOM-020","ATOM-032","ATOM-037","ATOM-042"],"problem":"`BSR 49, 52, 55, 57, 59, 69, 73, 77`; `SRC-002..SRC-006`; `SRC-009..SRC-011`.","handling":"Cover only source-backed UI-visible success effects; retain the technical-attribution limitation.","blocking":false}],"dictionary_evidence":[{"dictionary_id":"DICT-001","dictionary_name":"Пол клиента","source_file":"support/АФБ справочники 26.06.26.md","source_location":"mview.dictionaries.natural_person.gender_d","extraction_status":"extracted","active_values":[";"],"archived_values":"none_required:no_archived_values"}],"obligations":[{"obligation_id":"OBL-001","atom_id":"ATOM-001","coverage_status":"testable","planned_test_case_id":"TC-ACPD-001","source_refs":["SRC-001","SRC-001.P01"],"atomic_statement":"Блок `Персональные данные` отображается в карточке заявки.","observable_oracle":"Блок `Персональные данные` отображается в карточке заявки.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-002","atom_id":"ATOM-002","coverage_status":"testable","planned_test_case_id":"TC-ACPD-001","source_refs":["SRC-002","SRC-002.P01"],"atomic_statement":"Поле `Фамилия` отображается всегда.","observable_oracle":"Поле `Фамилия` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-003","atom_id":"ATOM-003","coverage_status":"testable","planned_test_case_id":"TC-ACPD-022","source_refs":["SRC-002","SRC-002.P02"],"atomic_statement":"Поле `Фамилия` является обязательным.","observable_oracle":"Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Фамилия` пустой, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-004","atom_id":"ATOM-004","coverage_status":"testable","planned_test_case_id":"TC-ACPD-002","source_refs":["SRC-002","SRC-002.P03"],"atomic_statement":"Поле `Фамилия` редактируемо.","observable_oracle":"Поле `Фамилия` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-005","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-ACPD-003","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Фамилия` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Иванов-Петров` в поле `Фамилия`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-006","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-ACPD-016","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванов2` в поле `Фамилия`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-007","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-ACPD-017","source_refs":["SRC-002","SRC-002.P04"],"atomic_statement":"В поле `Фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванов@` в поле `Фамилия`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-008","atom_id":"ATOM-006","coverage_status":"testable","planned_test_case_id":"TC-ACPD-004","source_refs":["SRC-002","SRC-002.P05"],"atomic_statement":"Для поля `Фамилия` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Фамилия` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Иван` в поле `Фамилия` при доступной интеграции.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-009","atom_id":"ATOM-007","coverage_status":"testable","planned_test_case_id":"TC-ACPD-001","source_refs":["SRC-003","SRC-003.P01"],"atomic_statement":"Поле `Имя` отображается всегда.","observable_oracle":"Поле `Имя` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-010","atom_id":"ATOM-008","coverage_status":"testable","planned_test_case_id":"TC-ACPD-023","source_refs":["SRC-003","SRC-003.P02"],"atomic_statement":"Поле `Имя` является обязательным.","observable_oracle":"Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Имя` пустым, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-011","atom_id":"ATOM-009","coverage_status":"testable","planned_test_case_id":"TC-ACPD-002","source_refs":["SRC-003","SRC-003.P03"],"atomic_statement":"Поле `Имя` редактируемо.","observable_oracle":"Поле `Имя` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-012","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-ACPD-005","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Имя` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Анна-Мария` в поле `Имя`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-013","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-ACPD-018","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иван2` в поле `Имя`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-014","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-ACPD-019","source_refs":["SRC-003","SRC-003.P04"],"atomic_statement":"В поле `Имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иван@` в поле `Имя`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-015","atom_id":"ATOM-011","coverage_status":"testable","planned_test_case_id":"TC-ACPD-006","source_refs":["SRC-003","SRC-003.P05"],"atomic_statement":"Для поля `Имя` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Имя` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Анна` в поле `Имя` при доступной интеграции.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-016","atom_id":"ATOM-012","coverage_status":"testable","planned_test_case_id":"TC-ACPD-001","source_refs":["SRC-004","SRC-004.P01"],"atomic_statement":"Поле `Отчество` отображается всегда.","observable_oracle":"Поле `Отчество` отображается всегда.","test_intent":"Открыть карточку заявки и проверить блок и три поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-017","atom_id":"ATOM-013","coverage_status":"testable","planned_test_case_id":"TC-ACPD-047","source_refs":["SRC-004","SRC-004.P02"],"atomic_statement":"Поле `Отчество` не является обязательным.","observable_oracle":"Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Отчество` пустым, инициировать сохранение и открыть сохранённую заявку повторно.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-018","atom_id":"ATOM-014","coverage_status":"testable","planned_test_case_id":"TC-ACPD-002","source_refs":["SRC-004","SRC-004.P03"],"atomic_statement":"Поле `Отчество` редактируемо.","observable_oracle":"Поле `Отчество` доступно для редактирования.","test_intent":"Указать валидные значения в три ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-019","atom_id":"ATOM-015","coverage_status":"testable","planned_test_case_id":"TC-ACPD-007","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Поле `Отчество` допускает текстовые символы и символ `-`.","test_intent":"Ввести `Иванович-Петрович` в поле `Отчество`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-020","atom_id":"ATOM-015","coverage_status":"testable","planned_test_case_id":"TC-ACPD-020","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванович2` в поле `Отчество`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-021","atom_id":"ATOM-015","coverage_status":"testable","planned_test_case_id":"TC-ACPD-021","source_refs":["SRC-004","SRC-004.P04"],"atomic_statement":"В поле `Отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан.","test_intent":"Ввести `Иванович@` в поле `Отчество`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-022","atom_id":"ATOM-016","coverage_status":"testable","planned_test_case_id":"TC-ACPD-008","source_refs":["SRC-004","SRC-004.P05"],"atomic_statement":"Для поля `Отчество` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Отчество` допускаются подсказки DaData при доступной интеграции.","test_intent":"Начать ввод `Иванович` в поле `Отчество` при доступной интеграции.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-023","atom_id":"ATOM-017","coverage_status":"testable","planned_test_case_id":"TC-ACPD-009","source_refs":["SRC-005","SRC-005.P01"],"atomic_statement":"Поле `ID клиента` отображается всегда и недоступно для ручного редактирования.","observable_oracle":"`ID клиента` отображается всегда и недоступен для ручного редактирования.","test_intent":"Открыть карточку заявки и попытаться изменить `ID клиента`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-024","atom_id":"ATOM-018","coverage_status":"testable","planned_test_case_id":"TC-ACPD-010","source_refs":["SRC-005","SRC-005.P02"],"atomic_statement":"Поле `ID клиента` заполняется автоматически системой ID клиента из АБС после сохранения заявки.","observable_oracle":"После save видимый `ID клиента` изменился с пустого на непустой; значение записано, ABS-атрибуция не утверждается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` записать пустой `ID клиента`, инициировать сохранение заявки и записать новое видимое значение.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-025","atom_id":"ATOM-019","coverage_status":"testable","planned_test_case_id":"TC-ACPD-011","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"atomic_statement":"Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`.","observable_oracle":"Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`.","test_intent":"Открыть переключатель `Пол`.","dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-026","atom_id":"ATOM-019","coverage_status":"testable","planned_test_case_id":"TC-ACPD-024","source_refs":["SRC-006","SRC-006.P01","DICT-001"],"atomic_statement":"Поле `Пол` отображается всегда, обязательно, редактируемо и использует справочник `Пол клиента`.","observable_oracle":"Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Пол` пустым, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-027","atom_id":"ATOM-020","coverage_status":"testable","planned_test_case_id":"TC-ACPD-012","source_refs":["SRC-006","SRC-006.P02"],"atomic_statement":"Поле `Пол` должно обновляться данными DaData после заполнения ФИО через подсказку DaData.","observable_oracle":"После выбора runtime-подсказки в `Фамилия` видимый `Пол` равен полу выбранного варианта; значения записаны, provider-attribution не утверждается.","test_intent":"В `Фамилия` выполнить `FIX-ACPD-RUNTIME-DADATA-001`, записав исходный `Пол` и пол выбранной подсказки.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-028","atom_id":"ATOM-021","coverage_status":"testable","planned_test_case_id":"TC-ACPD-013","source_refs":["SRC-007","SRC-007.P01"],"atomic_statement":"Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`.","observable_oracle":"Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются.","test_intent":"Ввести вычисленную дату `D-30 лет`, прочитать отображённое логическое значение.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-029","atom_id":"ATOM-021","coverage_status":"testable","planned_test_case_id":"TC-ACPD-025","source_refs":["SRC-007","SRC-007.P01"],"atomic_statement":"Поле `Дата рождения` отображается всегда, обязательно, редактируемо и имеет тип `Дата`.","observable_oracle":"Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` оставить `Дата рождения` пустой, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-030","atom_id":"ATOM-022","coverage_status":"testable","planned_test_case_id":"TC-ACPD-014","source_refs":["SRC-007","SRC-007.P02"],"atomic_statement":"Дата рождения не может быть позже чем `D-18 лет`.","observable_oracle":"После ввода вычисленной от `D` даты `D-18 лет` поле `Дата рождения` показывает ту же логическую дату.","test_intent":"Зафиксировать `D`; ввести `D-18 лет` в `Дата рождения`; завершить ввод.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-031","atom_id":"ATOM-022","coverage_status":"testable","planned_test_case_id":"TC-ACPD-026","source_refs":["SRC-007","SRC-007.P02"],"atomic_statement":"Дата рождения не может быть позже чем `D-18 лет`.","observable_oracle":"Evidence record: `D-18 лет + 1 день`, граница `D-18 лет`, завершение ввода, сохранение, видимое состояние поля и outcome; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D-18 лет + 1 день`, завершить ввод и сохранить; записать D-границу, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-032","atom_id":"ATOM-023","coverage_status":"testable","planned_test_case_id":"TC-ACPD-027","source_refs":["SRC-007","SRC-007.P03"],"atomic_statement":"Дата рождения не может быть больше текущей даты `D`.","observable_oracle":"Evidence record: `D+1 день`, дата `D`, завершение ввода, сохранение, видимое состояние поля и outcome; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D+1 день`, завершить ввод и сохранить; записать `D`, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-033","atom_id":"ATOM-024","coverage_status":"testable","planned_test_case_id":"TC-ACPD-015","source_refs":["SRC-007","SRC-007.P04"],"atomic_statement":"Дата рождения не может быть меньше чем `D-100 лет`.","observable_oracle":"После ввода вычисленной от `D` даты `D-100 лет` поле `Дата рождения` показывает ту же логическую дату.","test_intent":"Зафиксировать `D`; ввести `D-100 лет` в `Дата рождения`; завершить ввод.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-034","atom_id":"ATOM-024","coverage_status":"testable","planned_test_case_id":"TC-ACPD-028","source_refs":["SRC-007","SRC-007.P04"],"atomic_statement":"Дата рождения не может быть меньше чем `D-100 лет`.","observable_oracle":"Evidence record: `D-100 лет - 1 день`, граница `D-100 лет`, завершение ввода, сохранение, видимое состояние поля и outcome; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D-100 лет - 1 день`, завершить ввод и сохранить; записать D-границу, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-035","atom_id":"ATOM-025","coverage_status":"testable","planned_test_case_id":"TC-ACPD-014","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`.","test_intent":"Зафиксировать `D`; ввести `D-18 лет` в `Дата рождения`; завершить ввод.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-036","atom_id":"ATOM-025","coverage_status":"testable","planned_test_case_id":"TC-ACPD-015","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`.","test_intent":"Зафиксировать `D`; ввести `D-100 лет` в `Дата рождения`; завершить ввод.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-037","atom_id":"ATOM-025","coverage_status":"testable","planned_test_case_id":"TC-ACPD-026","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения позже `D-18 лет` использует текущую дату приложения `D`.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D-18 лет + 1 день`, завершить ввод и сохранить; записать D-границу, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-038","atom_id":"ATOM-025","coverage_status":"testable","planned_test_case_id":"TC-ACPD-027","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения больше `D` использует текущую дату приложения `D`.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D+1 день`, завершить ввод и сохранить; записать `D`, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-039","atom_id":"ATOM-025","coverage_status":"testable","planned_test_case_id":"TC-ACPD-028","source_refs":["SRC-007","SRC-007.P05"],"atomic_statement":"Границы даты рождения проверяются относительно текущей даты приложения `D`.","observable_oracle":"Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` ввести `D-100 лет - 1 день`, завершить ввод и сохранить; записать D-границу, состояние поля и outcome.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-040","atom_id":"ATOM-026","coverage_status":"testable","planned_test_case_id":"TC-ACPD-029","source_refs":["SRC-008","SRC-008.P01"],"atomic_statement":"Поле `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.","observable_oracle":"`Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.","test_intent":"Открыть переключатель `Клиент менял ФИО`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-041","atom_id":"ATOM-027","coverage_status":"testable","planned_test_case_id":"TC-ACPD-030","source_refs":["SRC-008","SRC-008.P02"],"atomic_statement":"Значение по умолчанию для `Клиент менял ФИО` равно `Нет`.","observable_oracle":"Значение по умолчанию `Клиент менял ФИО` равно `Нет`.","test_intent":"Открыть новую карточку заявки.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-042","atom_id":"ATOM-028","coverage_status":"testable","planned_test_case_id":"TC-ACPD-031","source_refs":["SRC-009","SRC-009.P01"],"atomic_statement":"Поле `Предыдущая фамилия` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущая фамилия` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-043","atom_id":"ATOM-028","coverage_status":"testable","planned_test_case_id":"TC-ACPD-032","source_refs":["SRC-009","SRC-009.P01"],"atomic_statement":"Поле `Предыдущая фамилия` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущая фамилия` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-044","atom_id":"ATOM-029","coverage_status":"testable","planned_test_case_id":"TC-ACPD-033","source_refs":["SRC-009","SRC-009.P02"],"atomic_statement":"Поле `Предыдущая фамилия` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущая фамилия` редактируема при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-045","atom_id":"ATOM-030","coverage_status":"testable","planned_test_case_id":"TC-ACPD-034","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"После ввода поле `Предыдущая фамилия` визуально содержит `Петрова-Сидорова`.","test_intent":"При `Клиент менял ФИО=Да` и видимой `Предыдущая фамилия` ввести `Петрова-Сидорова`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-046","atom_id":"ATOM-030","coverage_status":"testable","planned_test_case_id":"TC-ACPD-035","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Петрова2` в поле `Предыдущая фамилия`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-047","atom_id":"ATOM-030","coverage_status":"testable","planned_test_case_id":"TC-ACPD-036","source_refs":["SRC-009","SRC-009.P03"],"atomic_statement":"В поле `Предыдущая фамилия` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.","test_intent":"Ввести `Петрова@` в поле `Предыдущая фамилия`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-048","atom_id":"ATOM-031","coverage_status":"testable","planned_test_case_id":"TC-ACPD-041","source_refs":["SRC-009","SRC-009.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-049","atom_id":"ATOM-032","coverage_status":"testable","planned_test_case_id":"TC-ACPD-037","source_refs":["SRC-009","SRC-009.P05"],"atomic_statement":"Для поля `Предыдущая фамилия` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции.","test_intent":"При `Клиент менял ФИО=Да` и видимой `Предыдущая фамилия` ввести `Петрова`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-050","atom_id":"ATOM-033","coverage_status":"testable","planned_test_case_id":"TC-ACPD-031","source_refs":["SRC-010","SRC-010.P01"],"atomic_statement":"Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее имя` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-051","atom_id":"ATOM-033","coverage_status":"testable","planned_test_case_id":"TC-ACPD-032","source_refs":["SRC-010","SRC-010.P01"],"atomic_statement":"Поле `Предыдущее имя` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-052","atom_id":"ATOM-034","coverage_status":"testable","planned_test_case_id":"TC-ACPD-033","source_refs":["SRC-010","SRC-010.P02"],"atomic_statement":"Поле `Предыдущее имя` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущее имя` редактируемо при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-053","atom_id":"ATOM-035","coverage_status":"testable","planned_test_case_id":"TC-ACPD-038","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"`Предыдущее имя` допускает текстовые символы и символ `-`.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее имя` ввести `Анна-Мария`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-054","atom_id":"ATOM-035","coverage_status":"testable","planned_test_case_id":"TC-ACPD-039","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее имя` ввести `Анна2`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-055","atom_id":"ATOM-035","coverage_status":"testable","planned_test_case_id":"TC-ACPD-040","source_refs":["SRC-010","SRC-010.P03"],"atomic_statement":"В поле `Предыдущее имя` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее имя` ввести `Анна@`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-056","atom_id":"ATOM-036","coverage_status":"testable","planned_test_case_id":"TC-ACPD-041","source_refs":["SRC-010","SRC-010.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-057","atom_id":"ATOM-037","coverage_status":"testable","planned_test_case_id":"TC-ACPD-042","source_refs":["SRC-010","SRC-010.P05"],"atomic_statement":"Для поля `Предыдущее имя` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущее имя` допускаются подсказки DaData при доступной интеграции.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее имя` ввести `Анна`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]},{"obligation_id":"OBL-058","atom_id":"ATOM-038","coverage_status":"testable","planned_test_case_id":"TC-ACPD-031","source_refs":["SRC-011","SRC-011.P01"],"atomic_statement":"Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее отчество` отображается при `Клиент менял ФИО=Да`.","test_intent":"Установить `Клиент менял ФИО=Да`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-059","atom_id":"ATOM-038","coverage_status":"testable","planned_test_case_id":"TC-ACPD-032","source_refs":["SRC-011","SRC-011.P01"],"atomic_statement":"Поле `Предыдущее отчество` отображается при `Клиент менял ФИО = Да` и не отображается при `Нет`.","observable_oracle":"`Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`.","test_intent":"Установить `Клиент менял ФИО=Нет`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-060","atom_id":"ATOM-039","coverage_status":"testable","planned_test_case_id":"TC-ACPD-033","source_refs":["SRC-011","SRC-011.P02"],"atomic_statement":"Поле `Предыдущее отчество` редактируемо при выполнении условия видимости.","observable_oracle":"`Предыдущее отчество` редактируемо при выполнении условия видимости.","test_intent":"При `Клиент менял ФИО=Да` указать валидные значения в три предыдущих ФИО-поля.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-061","atom_id":"ATOM-040","coverage_status":"testable","planned_test_case_id":"TC-ACPD-043","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"`Предыдущее отчество` допускает текстовые символы и символ `-`.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее отчество` ввести `Ивановна-Петровна`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-062","atom_id":"ATOM-040","coverage_status":"testable","planned_test_case_id":"TC-ACPD-044","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение с цифрой не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее отчество` ввести `Ивановна2`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-063","atom_id":"ATOM-040","coverage_status":"testable","planned_test_case_id":"TC-ACPD-045","source_refs":["SRC-011","SRC-011.P03"],"atomic_statement":"В поле `Предыдущее отчество` возможен ввод только текстовых символов и символа `-`.","observable_oracle":"Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее отчество` ввести `Ивановна@`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-001"]},{"obligation_id":"OBL-064","atom_id":"ATOM-041","coverage_status":"testable","planned_test_case_id":"TC-ACPD-041","source_refs":["SRC-011","SRC-011.P04"],"atomic_statement":"Если `Клиент менял ФИО = Да`, должно быть заполнено хотя бы одно поле из группы предыдущей ФИО.","observable_oracle":"Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.","test_intent":"По `FIX-ACPD-PORTABLE-SAVE-001` задать `Клиент менял ФИО=Да`, оставить previous-FIO пустыми, инициировать сохранение и записать screenshot/post-state/persistence.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-002"]},{"obligation_id":"OBL-065","atom_id":"ATOM-042","coverage_status":"testable","planned_test_case_id":"TC-ACPD-046","source_refs":["SRC-011","SRC-011.P05"],"atomic_statement":"Для поля `Предыдущее отчество` при интеграции DaData допускаются подсказки.","observable_oracle":"Для `Предыдущее отчество` допускаются подсказки DaData при доступной интеграции.","test_intent":"При `Клиент менял ФИО=Да` и видимом `Предыдущее отчество` ввести `Ивановна`.","dictionary_refs":[],"gap_id":"","constraint_gap_ids":["GAP-003"]}]}
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
    "validator": "prepared-package-obligation-gate-v3",
    "findings_count": 0,
    "test_case_count": 47,
    "testable_obligations": 65,
    "covered_obligations": [
      "OBL-001",
      "OBL-002",
      "OBL-003",
      "OBL-004",
      "OBL-005",
      "OBL-006",
      "OBL-007",
      "OBL-008",
      "OBL-009",
      "OBL-010",
      "OBL-011",
      "OBL-012",
      "OBL-013",
      "OBL-014",
      "OBL-015",
      "OBL-016",
      "OBL-017",
      "OBL-018",
      "OBL-019",
      "OBL-020",
      "OBL-021",
      "OBL-022",
      "OBL-023",
      "OBL-024",
      "OBL-025",
      "OBL-026",
      "OBL-027",
      "OBL-028",
      "OBL-029",
      "OBL-030",
      "OBL-031",
      "OBL-032",
      "OBL-033",
      "OBL-034",
      "OBL-035",
      "OBL-036",
      "OBL-037",
      "OBL-038",
      "OBL-039",
      "OBL-040",
      "OBL-041",
      "OBL-042",
      "OBL-043",
      "OBL-044",
      "OBL-045",
      "OBL-046",
      "OBL-047",
      "OBL-048",
      "OBL-049",
      "OBL-050",
      "OBL-051",
      "OBL-052",
      "OBL-053",
      "OBL-054",
      "OBL-055",
      "OBL-056",
      "OBL-057",
      "OBL-058",
      "OBL-059",
      "OBL-060",
      "OBL-061",
      "OBL-062",
      "OBL-063",
      "OBL-064",
      "OBL-065"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 47
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
    "test_case_count": 47
  },
  {
    "gate": "package-metadata",
    "passed": true,
    "validator": "prepared-package-metadata-gate-v1",
    "findings_count": 0
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
  "test_case_count": 47,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\application-card-client-personal-data-shadow-v8-20260713\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v8-20260713/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"7e6802456c2e5122e87838a071e1eab40dd67938f539ed2ebdbf2498bc6d5caa","context_profile":"character-restriction-calibration","open_count":45,"resolved_count":0,"status_counts":{"awaiting-ui-calibration":45},"constraint_gap_ids":["GAP-002","GAP-001","GAP-003"],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-ACPD-001

**Название:** Отображение блока «Персональные данные» и полей ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-001; ATOM-001; SRC-001; SRC-001.P01; OBL-002; ATOM-002; SRC-002; SRC-002.P01; OBL-009; ATOM-007; SRC-003; SRC-003.P01; OBL-016; ATOM-012; SRC-004; SRC-004.P01

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть карточку заявки и перейти к разделу с персональными данными.

### Итоговый ожидаемый результат

В карточке заявки отображается блок `Персональные данные` с полями `Фамилия`, `Имя` и `Отчество`.

### Постусловия

- Не требуются.

## TC-ACPD-002

**Название:** Редактирование полей ФИО валидными значениями
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-004; ATOM-004; SRC-002; SRC-002.P03; OBL-011; ATOM-009; SRC-003; SRC-003.P03; OBL-018; ATOM-014; SRC-004; SRC-004.P03

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- `Фамилия`: `Иванов`.
- `Имя`: `Иван`.
- `Отчество`: `Иванович`.

### Шаги

1. Ввести указанные валидные значения в поля `Фамилия`, `Имя` и `Отчество`.

### Итоговый ожидаемый результат

Каждое из полей `Фамилия`, `Имя` и `Отчество` доступно для редактирования и принимает введённое значение.

### Постусловия

- Не требуются.

## TC-ACPD-003

**Название:** Ввод текстового значения с дефисом в поле «Фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-005; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- `Фамилия`: `Иванов-Петров`.

### Шаги

1. Ввести `Иванов-Петров` в поле `Фамилия`.

### Итоговый ожидаемый результат

Поле `Фамилия` принимает значение `Иванов-Петров`, состоящее из текстовых символов и символа `-`.

### Постусловия

- Не требуются.

## TC-ACPD-004

**Название:** Отображение подсказки при вводе фамилии
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-008; ATOM-006; SRC-002; SRC-002.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.
2. Интеграция DaData доступна.

### Тестовые данные

- Префикс фамилии: `Иван`.

### Шаги

1. Начать ввод `Иван` в поле `Фамилия`.

### Итоговый ожидаемый результат

Для поля `Фамилия` доступна подсказка, которую пользователь может выбрать.

### Постусловия

- Не требуются.

## TC-ACPD-005

**Название:** Ввод текстового значения с дефисом в поле «Имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-012; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- `Имя`: `Анна-Мария`.

### Шаги

1. Ввести `Анна-Мария` в поле `Имя`.

### Итоговый ожидаемый результат

Поле `Имя` принимает значение `Анна-Мария`, состоящее из текстовых символов и символа `-`.

### Постусловия

- Не требуются.

## TC-ACPD-006

**Название:** Отображение подсказки при вводе имени
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-015; ATOM-011; SRC-003; SRC-003.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.
2. Интеграция DaData доступна.

### Тестовые данные

- Префикс имени: `Анна`.

### Шаги

1. Начать ввод `Анна` в поле `Имя`.

### Итоговый ожидаемый результат

Для поля `Имя` доступна подсказка, которую пользователь может выбрать.

### Постусловия

- Не требуются.

## TC-ACPD-007

**Название:** Ввод текстового значения с дефисом в поле «Отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-019; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- `Отчество`: `Иванович-Петрович`.

### Шаги

1. Ввести `Иванович-Петрович` в поле `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` принимает значение `Иванович-Петрович`, состоящее из текстовых символов и символа `-`.

### Постусловия

- Не требуются.

## TC-ACPD-008

**Название:** Отображение подсказки при вводе отчества
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-022; ATOM-016; SRC-004; SRC-004.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.
2. Интеграция DaData доступна.

### Тестовые данные

- Префикс отчества: `Иванович`.

### Шаги

1. Начать ввод `Иванович` в поле `Отчество`.

### Итоговый ожидаемый результат

Для поля `Отчество` доступна подсказка, которую пользователь может выбрать.

### Постусловия

- Не требуются.

## TC-ACPD-009

**Название:** Недоступность ручного редактирования поля «ID клиента»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-023; ATOM-017; SRC-005; SRC-005.P01

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- Не требуются.

### Шаги

1. Найти поле `ID клиента` в карточке заявки и попытаться изменить его значение вручную.

### Итоговый ожидаемый результат

Поле `ID клиента` отображается в карточке заявки и недоступно для ручного редактирования.

### Постусловия

- Не требуются.

## TC-ACPD-010

**Название:** Заполнение поля «ID клиента» после сохранения заявки
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-024; ATOM-018; SRC-005; SRC-005.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`.
2. В поле `ID клиента` отображается пустое значение.

### Тестовые данные

- `Фамилия`: `Иванов`.
- `Имя`: `Иван`.
- `Пол`: `Мужчина`.
- `Дата рождения`: дата, соответствующая относительному значению `D-30y`.
- `Клиент менял ФИО`: `Нет`.

### Шаги

1. Сохранить заявку и после успешного сохранения записать видимое значение поля `ID клиента`.

### Итоговый ожидаемый результат

После успешного сохранения заявки видимое значение `ID клиента` изменяется с пустого на непустое.

### Постусловия

- Не требуются.

## TC-ACPD-011

**Название:** Перечень активных значений и выбор в поле «Пол»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-025; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки, созданная действием создания заявки из BSR 38.

### Тестовые данные

- Активные значения справочника `Пол клиента`: `Мужчина`, `Женщина`.

### Шаги

1. Открыть элемент выбора поля `Пол`.

### Итоговый ожидаемый результат

Поле `Пол` отображается и доступно для выбора; элемент выбора содержит полный активный перечень значений: `Мужчина`, `Женщина`.

### Постусловия

- Не требуются.

## TC-ACPD-012

**Название:** Обновление поля «Пол» значением выбранной подсказки в «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-027; ATOM-020; SRC-006; SRC-006.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; интеграция DaData доступна.

### Тестовые данные

- `FIX-ACPD-RUNTIME-DADATA-001`: префикс `Иван` и фактически возвращённая подсказка с доступными составными частями ФИО и известным непустым полом.

### Шаги

1. Записать исходное видимое значение поля `Пол`, ввести `Иван` в поле `Фамилия`, выбрать фактически возвращённую подсказку с известным полом и записать пол выбранного варианта и итоговое видимое значение поля `Пол`.

### Итоговый ожидаемый результат

Evidence record содержит действие с префиксом `Иван`, пол выбранной runtime-подсказки, исходное и итоговое видимые значения `Пол` и наблюдаемый outcome; после выбора видимый `Пол` равен полу выбранного варианта. Provider-attribution не утверждается.

### Постусловия

- Не требуются.

## TC-ACPD-013

**Название:** Отображение и ввод даты рождения `D-30 лет`
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-028; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поля scope заполнены по `FIX-ACPD-PORTABLE-SAVE-001`.

### Тестовые данные

- Логическая дата рождения: `D-30 лет`, где `D` — текущая дата приложения.

### Шаги

1. Ввести в поле `Дата рождения` вычисленную дату `D-30 лет`.
2. Прочитать отображаемое в поле логическое значение даты.

### Итоговый ожидаемый результат

Поле `Дата рождения` видно, доступно для редактирования и отображает введённую логическую дату `D-30 лет`; формат ввода и виджет не утверждаются.

### Постусловия

- Не применимо: результат обязательности и сохранения не проверяется в данном кейсе.

## TC-ACPD-014

**Название:** Ввод даты рождения на верхней границе `D-18 лет`
**Тип:** граничный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-030; ATOM-022; SRC-007; SRC-007.P02; OBL-035; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`.

### Тестовые данные

- Дата рождения: `D-18 лет`, вычисленная относительно текущей даты приложения `D`.

### Шаги

1. Зафиксировать текущую дату приложения `D`, ввести в поле `Дата рождения` вычисленную дату `D-18 лет` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит зафиксированную `D`, ввод `D-18 лет`, видимое состояние поля после завершения ввода и наблюдаемый outcome; поле `Дата рождения` визуально показывает логическую дату `D-18 лет`, вычисленную от текущей даты приложения `D`.

### Постусловия

- Не требуются.

## TC-ACPD-015

**Название:** Ввод даты рождения на нижней границе `D-100 лет`
**Тип:** граничный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-033; ATOM-024; SRC-007; SRC-007.P04; OBL-036; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`.

### Тестовые данные

- Дата рождения: `D-100 лет`, вычисленная относительно текущей даты приложения `D`.

### Шаги

1. Зафиксировать текущую дату приложения `D`, ввести в поле `Дата рождения` вычисленную дату `D-100 лет` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит зафиксированную `D`, ввод `D-100 лет`, видимое состояние поля после завершения ввода и наблюдаемый outcome; поле `Дата рождения` визуально показывает логическую дату `D-100 лет`, вычисленную от текущей даты приложения `D`.

### Постусловия

- Не требуются.

## TC-ACPD-016

**Название:** Ввод цифры в поле `Фамилия`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-006; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Фамилия` доступно для ввода.

### Тестовые данные

- Значение поля `Фамилия`: `Иванов2`.

### Шаги

1. Ввести в поле `Фамилия` значение `Иванов2`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Фамилия`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-017

**Название:** Ввод спецсимвола `@` в поле `Фамилия`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-007; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Фамилия` доступно для ввода.

### Тестовые данные

- Значение поля `Фамилия`: `Иванов@`.

### Шаги

1. Ввести в поле `Фамилия` значение `Иванов@`.

### Итоговый ожидаемый результат

Значение со спецсимволом `@` не признаётся допустимым для поля `Фамилия`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-018

**Название:** Ввод цифры в поле `Имя`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-013; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Имя` доступно для ввода.

### Тестовые данные

- Значение поля `Имя`: `Иван2`.

### Шаги

1. Ввести в поле `Имя` значение `Иван2`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Имя`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-019

**Название:** Ввод спецсимвола `@` в поле `Имя`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-014; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Имя` доступно для ввода.

### Тестовые данные

- Значение поля `Имя`: `Иван@`.

### Шаги

1. Ввести в поле `Имя` значение `Иван@`.

### Итоговый ожидаемый результат

Значение со спецсимволом `@` не признаётся допустимым для поля `Имя`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-020

**Название:** Ввод цифры в поле `Отчество`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-020; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Отчество` доступно для ввода.

### Тестовые данные

- Значение поля `Отчество`: `Иванович2`.

### Шаги

1. Ввести в поле `Отчество` значение `Иванович2`.

### Итоговый ожидаемый результат

Значение с цифрой не признаётся допустимым для поля `Отчество`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-021

**Название:** Ввод спецсимвола `@` в поле `Отчество`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-021; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поле `Отчество` доступно для ввода.

### Тестовые данные

- Значение поля `Отчество`: `Иванович@`.

### Шаги

1. Ввести в поле `Отчество` значение `Иванович@`.

### Итоговый ожидаемый результат

Значение со спецсимволом `@` не признаётся допустимым для поля `Отчество`; конкретный механизм UI-отклонения калибруется в UI.

### Постусловия

- Не применимо: конкретное проявление недопустимости фиксируется при UI-калибровке.

## TC-ACPD-022

**Название:** Сохранение заявки с пустым полем `Фамилия`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-003; ATOM-003; SRC-002; SRC-002.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поля scope заполнены по `FIX-ACPD-PORTABLE-SAVE-001`, кроме поля `Фамилия`.

### Тестовые данные

- Поле `Фамилия` оставлено пустым.
- Остальные поля scope: `Имя=Иван`, `Пол=Мужчина`, `Дата рождения=D-30y`, `Клиент менял ФИО=Нет`.

### Шаги

1. Оставить поле `Фамилия` пустым.
2. Инициировать сохранение заявки.
3. Зафиксировать действие сохранения, пустое поле `Фамилия`, видимое состояние после действия и факт перехода либо сохранения.

### Итоговый ожидаемый результат

Зафиксированы действие сохранения, пустое поле `Фамилия`, видимое состояние после действия и факт перехода либо сохранения; механизм обработки обязательности не предписан и калибруется в UI.

### Постусловия

- Не применимо: факт и механизм сохранения фиксируются при UI-калибровке.

## TC-ACPD-023

**Название:** Сохранение заявки с пустым полем `Имя`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-010; ATOM-008; SRC-003; SRC-003.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поля scope заполнены по `FIX-ACPD-PORTABLE-SAVE-001`, кроме поля `Имя`.

### Тестовые данные

- Поле `Имя` оставлено пустым.
- Остальные поля scope: `Фамилия=Иванов`, `Пол=Мужчина`, `Дата рождения=D-30y`, `Клиент менял ФИО=Нет`.

### Шаги

1. Оставить поле `Имя` пустым.
2. Инициировать сохранение заявки.
3. Зафиксировать действие сохранения, пустое поле `Имя`, видимое состояние после действия и факт перехода либо сохранения.

### Итоговый ожидаемый результат

Зафиксированы действие сохранения, пустое поле `Имя`, видимое состояние после действия и факт перехода либо сохранения; механизм обработки обязательности не предписан и калибруется в UI.

### Постусловия

- Не применимо: факт и механизм сохранения фиксируются при UI-калибровке.

## TC-ACPD-024

**Название:** Сохранение заявки с пустым полем `Пол`
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-026; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поля scope заполнены по `FIX-ACPD-PORTABLE-SAVE-001`, кроме поля `Пол`.

### Тестовые данные

- Поле `Пол` оставлено пустым.
- Остальные поля scope: `Фамилия=Иванов`, `Имя=Иван`, `Дата рождения=D-30y`, `Клиент менял ФИО=Нет`.

### Шаги

1. Оставить поле `Пол` пустым.
2. Инициировать сохранение заявки.
3. Зафиксировать действие сохранения, пустое поле `Пол`, видимое состояние после действия и факт перехода либо сохранения.

### Итоговый ожидаемый результат

Зафиксированы действие сохранения, пустое поле `Пол`, видимое состояние после действия и факт перехода либо сохранения; механизм обработки обязательности не предписан и калибруется в UI.

### Постусловия

- Не применимо: факт и механизм сохранения фиксируются при UI-калибровке.

## TC-ACPD-025

**Название:** Проверка обязательности поля «Дата рождения» при пустом значении
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-029; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38; поля выбранного scope заполнены значениями из `FIX-ACPD-PORTABLE-SAVE-001`, кроме поля «Дата рождения».

### Тестовые данные

- «Дата рождения»: пустое значение.

### Шаги

1. Убедиться, что поле «Дата рождения» пустое, и инициировать сохранение карточки заявки.

### Итоговый ожидаемый результат

Зафиксированы evidence: действие сохранения, пустое поле «Дата рождения», видимое состояние после действия и факт перехода либо сохранения; механизм реакции интерфейса не предписан.

### Постусловия

- Не применимо: результат сохранения или перехода фиксируется как evidence.

## TC-ACPD-026

**Название:** Проверка даты рождения позже границы D-18 лет
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-031; ATOM-022; SRC-007; SRC-007.P02; OBL-037; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; поля выбранного scope заполнены синтетическими значениями, кроме поля «Дата рождения».

### Тестовые данные

- `D`: текущая дата приложения.
- «Дата рождения»: `D-18 лет + 1 день`.

### Шаги

1. Ввести в поле «Дата рождения» значение `D-18 лет + 1 день`, завершить ввод и сохранить карточку.

### Итоговый ожидаемый результат

Зафиксирована evidence record с текущей датой приложения `D`, границей `D-18 лет`, введённым значением `D-18 лет + 1 день`, действием завершения ввода и сохранения, видимым состоянием поля «Дата рождения» и наблюдаемым outcome после сохранения; проверка значения позже `D-18 лет` выполняется относительно текущей даты приложения `D`.

### Постусловия

- Не применимо: evidence record сохраняется для UI-калибровки без предписания механизма UI-реакции.

## TC-ACPD-027

**Название:** Проверка даты рождения позже текущей даты D
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-032; ATOM-023; SRC-007; SRC-007.P03; OBL-038; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; поля выбранного scope заполнены синтетическими значениями, кроме поля «Дата рождения».

### Тестовые данные

- `D`: текущая дата приложения.
- «Дата рождения»: `D+1 день`.

### Шаги

1. Ввести в поле «Дата рождения» значение `D+1 день`, завершить ввод и сохранить карточку.

### Итоговый ожидаемый результат

Зафиксирована evidence record с текущей датой приложения `D`, введённым значением `D+1 день`, действием завершения ввода и сохранения, видимым состоянием поля «Дата рождения» и наблюдаемым outcome после сохранения; проверка значения больше `D` выполняется относительно текущей даты приложения `D`.

### Постусловия

- Не применимо: evidence record сохраняется для UI-калибровки без предписания механизма UI-реакции.

## TC-ACPD-028

**Название:** Проверка даты рождения раньше границы D-100 лет
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-034; ATOM-024; SRC-007; SRC-007.P04; OBL-039; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; поля выбранного scope заполнены синтетическими значениями, кроме поля «Дата рождения».

### Тестовые данные

- `D`: текущая дата приложения.
- «Дата рождения»: `D-100 лет - 1 день`.

### Шаги

1. Ввести в поле «Дата рождения» значение `D-100 лет - 1 день`, завершить ввод и сохранить карточку.

### Итоговый ожидаемый результат

Зафиксирована evidence record с текущей датой приложения `D`, границей `D-100 лет`, введённым значением `D-100 лет - 1 день`, действием завершения ввода и сохранения, видимым состоянием поля «Дата рождения» и наблюдаемым outcome после сохранения; проверка значения раньше `D-100 лет` выполняется относительно текущей даты приложения `D`.

### Постусловия

- Не применимо: evidence record сохраняется для UI-калибровки без предписания механизма UI-реакции.

## TC-ACPD-029

**Название:** Проверка переключателя «Клиент менял ФИО» с вариантами «Да/Нет»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-040; ATOM-026; SRC-008; SRC-008.P01

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть переключатель «Клиент менял ФИО».

### Итоговый ожидаемый результат

Поле «Клиент менял ФИО» отображается как переключатель с вариантами «Да» и «Нет».

### Постусловия

- Не применимо.

## TC-ACPD-030

**Название:** Проверка значения по умолчанию «Нет» для переключателя «Клиент менял ФИО»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-041; ATOM-027; SRC-008; SRC-008.P02

### Предусловия

1. Новая карточка заявки ещё не открывалась в текущей проверке.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть новую карточку заявки действием создания заявки из BSR 38.

### Итоговый ожидаемый результат

Значение переключателя «Клиент менял ФИО» по умолчанию равно «Нет».

### Постусловия

- Не применимо.

## TC-ACPD-031

**Название:** Проверка отображения полей предыдущей ФИО при значении «Да»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-042; ATOM-028; SRC-009; SRC-009.P01; OBL-050; ATOM-033; SRC-010; SRC-010.P01; OBL-058; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.

### Тестовые данные

- «Клиент менял ФИО»: «Да».

### Шаги

1. Установить в переключателе «Клиент менял ФИО» значение «Да».

### Итоговый ожидаемый результат

Отображаются поля «Предыдущая фамилия», «Предыдущее имя» и «Предыдущее отчество».

### Постусловия

- Не применимо.

## TC-ACPD-032

**Название:** Проверка скрытия полей предыдущей ФИО при значении «Нет»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-043; ATOM-028; SRC-009; SRC-009.P01; OBL-051; ATOM-033; SRC-010; SRC-010.P01; OBL-059; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.

### Тестовые данные

- «Клиент менял ФИО»: «Нет».

### Шаги

1. Установить в переключателе «Клиент менял ФИО» значение «Нет».

### Итоговый ожидаемый результат

Поля «Предыдущая фамилия», «Предыдущее имя» и «Предыдущее отчество» не отображаются.

### Постусловия

- Не применимо.

## TC-ACPD-033

**Название:** Проверка редактируемости полей предыдущей ФИО при значении «Да»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-044; ATOM-029; SRC-009; SRC-009.P02; OBL-052; ATOM-034; SRC-010; SRC-010.P02; OBL-060; ATOM-039; SRC-011; SRC-011.P02

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.
1. В переключателе «Клиент менял ФИО» установлено значение «Да».

### Тестовые данные

- «Предыдущая фамилия»: `Петрова`.
- «Предыдущее имя»: `Анна`.
- «Предыдущее отчество»: `Ивановна`.

### Шаги

1. Ввести тестовые значения в поля «Предыдущая фамилия», «Предыдущее имя» и «Предыдущее отчество».

### Итоговый ожидаемый результат

Все три отображённые поля доступны для редактирования.

### Постусловия

- Не применимо.

## TC-ACPD-034

**Название:** Ввод фамилии с дефисом в поле «Предыдущая фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-045; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущая фамилия` видно.

### Тестовые данные

- `Предыдущая фамилия`: `Петрова-Сидорова`.

### Шаги

1. Ввести `Петрова-Сидорова` в поле `Предыдущая фамилия` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Петрова-Сидорова`, видимое состояние поля после завершения ввода и наблюдаемый outcome; поле `Предыдущая фамилия` визуально содержит точное значение `Петрова-Сидорова`.

### Постусловия

- Не требуются.

## TC-ACPD-035

**Название:** Проверка недопустимого значения с цифрой в поле «Предыдущая фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-046; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.
1. В переключателе «Клиент менял ФИО» установлено значение «Да».

### Тестовые данные

- «Предыдущая фамилия»: `Петрова2`.

### Шаги

1. Ввести в поле «Предыдущая фамилия» значение `Петрова2`.

### Итоговый ожидаемый результат

Значение с цифрой не является допустимым для поля «Предыдущая фамилия»; механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не применимо: наблюдаемая UI-реакция фиксируется для калибровки.

## TC-ACPD-036

**Название:** Проверка недопустимого значения со специальным символом в поле «Предыдущая фамилия»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-047; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.
1. В переключателе «Клиент менял ФИО» установлено значение «Да».

### Тестовые данные

- «Предыдущая фамилия»: `Петрова@`.

### Шаги

1. Ввести в поле «Предыдущая фамилия» значение `Петрова@`.

### Итоговый ожидаемый результат

Значение со специальным символом `@`, отличным от `-`, не является допустимым для поля «Предыдущая фамилия»; механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не применимо: наблюдаемая UI-реакция фиксируется для калибровки.

## TC-ACPD-037

**Название:** Подсказки для поля «Предыдущая фамилия» при доступной интеграции DaData
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-049; ATOM-032; SRC-009; SRC-009.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущая фамилия` видно и интеграция DaData доступна.

### Тестовые данные

- Префикс: `Петрова`.

### Шаги

1. Ввести `Петрова` в поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Петрова`, видимое состояние поля, визуально доступные подсказки и наблюдаемый outcome; для `Предыдущая фамилия` при доступной интеграции допускаются подсказки DaData. Техническая атрибуция провайдера не утверждается.

### Постусловия

- Не требуются.

## TC-ACPD-038

**Название:** Ввод имени с дефисом в поле «Предыдущее имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-053; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее имя` видно.

### Тестовые данные

- `Предыдущее имя`: `Анна-Мария`.

### Шаги

1. Ввести `Анна-Мария` в поле `Предыдущее имя` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Анна-Мария`, видимое состояние поля после завершения ввода и наблюдаемый outcome; поле `Предыдущее имя` визуально содержит точное значение `Анна-Мария`.

### Постусловия

- Не требуются.

## TC-ACPD-039

**Название:** Калибровка ввода цифры в поле «Предыдущее имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-054; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее имя` видно.

### Тестовые данные

- `Предыдущее имя`: `Анна2`.

### Шаги

1. Ввести `Анна2` в поле `Предыдущее имя` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Анна2`, видимое состояние поля после завершения ввода и наблюдаемый outcome; значение с цифрой не является допустимым для `Предыдущее имя`. Механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не требуются.

## TC-ACPD-040

**Название:** Калибровка ввода спецсимвола в поле «Предыдущее имя»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-055; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее имя` видно.

### Тестовые данные

- `Предыдущее имя`: `Анна@`.

### Шаги

1. Ввести `Анна@` в поле `Предыдущее имя` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Анна@`, видимое состояние поля после завершения ввода и наблюдаемый outcome; значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`. Механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не требуются.

## TC-ACPD-041

**Название:** Сохранение заявки с пустой группой предыдущей ФИО при признаке изменения ФИО
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-048; ATOM-031; SRC-009; SRC-009.P04; OBL-056; ATOM-036; SRC-010; SRC-010.P04; OBL-064; ATOM-041; SRC-011; SRC-011.P04
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.
2. Поля в scope заполнены синтетическими значениями: «Фамилия» = `Иванов`, «Имя» = `Иван`, «Пол» = `Мужчина`, «Дата рождения» = `D-30y`.

### Тестовые данные

- «Клиент менял ФИО» = `Да`.
- Поля группы предыдущей ФИО оставлены пустыми.

### Шаги

1. Установить значение `Да` в поле «Клиент менял ФИО».
2. Убедиться, что поля группы предыдущей ФИО не заполнены.
3. Инициировать сохранение заявки.
4. Зафиксировать снимок экрана, видимое состояние после действия и факт перехода либо сохранения.

### Итоговый ожидаемый результат

Зафиксированы действие сохранения, условие «Клиент менял ФИО = Да», пустая группа предыдущей ФИО, видимое состояние после действия и факт перехода либо сохранения; сообщение, блокировка сохранения и иной UI-механизм не предписаны и требуют калибровки.

### Постусловия

- Результат действия сохранения и видимое состояние зафиксированы как evidence; иных постусловий нет.

## TC-ACPD-042

**Название:** Подсказки для поля «Предыдущее имя» при доступной интеграции DaData
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-057; ATOM-037; SRC-010; SRC-010.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее имя` видно и интеграция DaData доступна.

### Тестовые данные

- Префикс: `Анна`.

### Шаги

1. Ввести `Анна` в поле `Предыдущее имя`.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Анна`, видимое состояние поля, визуально доступные подсказки и наблюдаемый outcome; для `Предыдущее имя` при доступной интеграции допускаются подсказки DaData. Техническая атрибуция провайдера не утверждается.

### Постусловия

- Не требуются.

## TC-ACPD-043

**Название:** Ввод отчества с дефисом в поле «Предыдущее отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-061; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее отчество` видно.

### Тестовые данные

- `Предыдущее отчество`: `Ивановна-Петровна`.

### Шаги

1. Ввести `Ивановна-Петровна` в поле `Предыдущее отчество` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Ивановна-Петровна`, видимое состояние поля после завершения ввода и наблюдаемый outcome; поле `Предыдущее отчество` визуально содержит точное значение `Ивановна-Петровна`.

### Постусловия

- Не требуются.

## TC-ACPD-044

**Название:** Калибровка ввода цифры в поле «Предыдущее отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-062; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее отчество` видно.

### Тестовые данные

- `Предыдущее отчество`: `Ивановна2`.

### Шаги

1. Ввести `Ивановна2` в поле `Предыдущее отчество` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Ивановна2`, видимое состояние поля после завершения ввода и наблюдаемый outcome; значение с цифрой не является допустимым для `Предыдущее отчество`. Механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не требуются.

## TC-ACPD-045

**Название:** Калибровка ввода спецсимвола в поле «Предыдущее отчество»
**Тип:** негативный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-063; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее отчество` видно.

### Тестовые данные

- `Предыдущее отчество`: `Ивановна@`.

### Шаги

1. Ввести `Ивановна@` в поле `Предыдущее отчество` и завершить ввод.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Ивановна@`, видимое состояние поля после завершения ввода и наблюдаемый outcome; значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`. Механизм UI-отклонения не задан и подлежит калибровке.

### Постусловия

- Не требуются.

## TC-ACPD-046

**Название:** Подсказки для поля «Предыдущее отчество» при доступной интеграции DaData
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-065; ATOM-042; SRC-011; SRC-011.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Открыта новая карточка заявки по `FIX-ACPD-PORTABLE-SAVE-001`; установлено `Клиент менял ФИО=Да`, поле `Предыдущее отчество` видно и интеграция DaData доступна.

### Тестовые данные

- Префикс: `Ивановна`.

### Шаги

1. Ввести `Ивановна` в поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

Evidence record содержит ввод `Ивановна`, видимое состояние поля, визуально доступные подсказки и наблюдаемый outcome; для `Предыдущее отчество` при доступной интеграции допускаются подсказки DaData. Техническая атрибуция провайдера не утверждается.

### Постусловия

- Не требуются.

## TC-ACPD-047

**Название:** Сохранение заявки с пустым полем «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** application-card-client-personal-data-v8
**Трассировка:** OBL-017; ATOM-013; SRC-004; SRC-004.P02

### Предусловия

1. Открыта новая карточка заявки действием создания заявки из BSR 38.
2. Поля в scope заполнены синтетическими значениями: «Фамилия» = `Иванов`, «Имя» = `Иван`, «Пол» = `Мужчина`, «Дата рождения» = `D-30y`, «Клиент менял ФИО» = `Нет`.

### Тестовые данные

- Поле «Отчество» оставлено пустым.

### Шаги

1. Не заполнять поле «Отчество».
2. Инициировать сохранение заявки.
3. Повторно открыть сохранённую заявку.

### Итоговый ожидаемый результат

Сохранение завершено; после повторного открытия поле «Отчество» пусто и не блокировало сохранение.

### Постусловия

- Не применимо: дополнительная очистка данных не требуется.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
