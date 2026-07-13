# Codex exec prepared-standard reviewer compact path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 6,
  "package_id": "search-clear-context-exec-benchmark-v4",
  "package_digest": "5a11807225be6671176d35bc2cc2a30656d6fe1692e67a97b6ecb2076ea9f97f",
  "ft_slug": "AutoFin",
  "scope_slug": "search-clear-context-exec-benchmark-v1",
  "section_id": "4.2",
  "execution_profile": "standard-required",
  "context_profile": "conditional-state",
  "unsupported_dimensions": [
    "dependency-state"
  ],
  "reviewed_draft_sha256": "4394b115f8fe3c58e70aeaf8370d6145768d1e54128f9b8157346e1c458f2f97"
}
```

# Prepared Reviewer Runtime Profile

This is the technical execution projection inside `ft-test-case-reviewer`. It introduces no new QA policy. The immutable package, context rule card and deterministic gates materialize the applicable canonical reviewer rubric for both `simple-field-property` and `standard-required` scopes.

## Eligibility

Continue only when the payload confirms:

- runner-validated current package metadata, including a non-empty SHA-256 `package_digest`, and immutable draft SHA-256;
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

## Context profile: `conditional-state`

- Preserve branch preconditions and state transitions exactly as supplied.
- Do not infer inverse branches or persistence across transitions.

## Selected source evidence

# Prepared Source Evidence

- package_id: `search-clear-context-exec-benchmark-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v4-20260713/prepared-input/.search-clear-context-exec-benchmark-v4.compiled-evidence.md`
- source_sha256: `cc091cadde7a482382cdc49fa0ffb0a83b467c5c7dfdf06300652be1954b5c8d`
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

- `FIX-SCCB-001`: environment has at least one available visible filter value that can produce a state different from captured initial.
- `FIX-SCCB-002`: results table contains at least one sortable header and one displayed row with observable selection state.
- `FIX-SCCB-003`: result set exposes at least one page different from captured initial; otherwise `TC-SCCB-003` is fixture-blocked.

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. This compact projection contains every exact review-contract ID plus its source-backed statement, oracle, intent, reference and gap; the runner validates the final contract against the immutable artifact.

```json
{"artifact":"fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v4-20260713/prepared-input/search-clear-context-exec-benchmark-v4/atomic-obligations.json","artifact_sha256":"1e3a6595c66c4c3794eb137642c47c53ed852c7afc573d428077274b11ddd50e","obligation_count":4,"semantic_evidence_source":"selected-source-evidence","coverage_gaps":[],"dictionary_evidence":[],"obligations":[{"obligation_id":"OBL-001","atom_id":"ATOM-001","coverage_status":"testable","planned_test_case_id":"TC-SCCB-001","source_refs":["BSR 32","SRC-001","SRC-001.P01"],"atomic_statement":"Нажатие `Очистить` очищает применённые фильтры поиска.","observable_oracle":"После нажатия `Очистить` доказанно изменённое состояние фильтров совпадает с зафиксированным initial state.","test_intent":"Capture visible values and state markers of the search filters before changing a filter.; Choose a visible filter value whose resulting visible state differs from the captured state; if no such value is available, report fixture-blocked.; Before the target action verify: Before `Очистить`, at least one visible filter value or state marker differs from the captured initial filter state.; Capture the initial visible filter state; create and prove a different visible filter state; click `Очистить`.","execution_semantics":"reset-to-captured-initial","state_change":{"initial_state_capture":"Capture visible values and state markers of the search filters before changing a filter.","changed_state_setup":"Choose a visible filter value whose resulting visible state differs from the captured state; if no such value is available, report fixture-blocked.","pre_action_state_oracle":"Before `Очистить`, at least one visible filter value or state marker differs from the captured initial filter state.","relation":"different-from-captured-initial"},"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-002","atom_id":"ATOM-002","coverage_status":"testable","planned_test_case_id":"TC-SCCB-002","source_refs":["BSR 32","SRC-001","SRC-001.P02"],"atomic_statement":"Нажатие `Очистить` очищает применённые сортировки.","observable_oracle":"После нажатия `Очистить` доказанно изменённое состояние сортировки совпадает с зафиксированным initial state.","test_intent":"Capture visible sort indicators before changing sorting.; Use a sortable header until its visible sort indicator differs from the captured state; if no different state can be produced, report fixture-blocked.; Before the target action verify: Before `Очистить`, the visible sort indicator differs from the captured initial sort state.; Capture the initial visible sort state; create and prove a different visible sort state; click `Очистить`.","execution_semantics":"reset-to-captured-initial","state_change":{"initial_state_capture":"Capture visible sort indicators before changing sorting.","changed_state_setup":"Use a sortable header until its visible sort indicator differs from the captured state; if no different state can be produced, report fixture-blocked.","pre_action_state_oracle":"Before `Очистить`, the visible sort indicator differs from the captured initial sort state.","relation":"different-from-captured-initial"},"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-003","atom_id":"ATOM-003","coverage_status":"testable","planned_test_case_id":"TC-SCCB-003","source_refs":["BSR 32","SRC-001","SRC-001.P03"],"atomic_statement":"Нажатие `Очистить` очищает постраничность.","observable_oracle":"После нажатия `Очистить` доказанно изменённое состояние постраничности совпадает с зафиксированным initial state.","test_intent":"Capture the visible active-page indicator before changing pagination.; Navigate to any available page whose visible active-page indicator differs from the captured initial page; if none is available, report fixture-blocked.; Before the target action verify: Before `Очистить`, the visible active-page indicator differs from the captured initial page.; Capture the initial active-page indicator; create and prove a different active page; click `Очистить`.","execution_semantics":"reset-to-captured-initial","state_change":{"initial_state_capture":"Capture the visible active-page indicator before changing pagination.","changed_state_setup":"Navigate to any available page whose visible active-page indicator differs from the captured initial page; if none is available, report fixture-blocked.","pre_action_state_oracle":"Before `Очистить`, the visible active-page indicator differs from the captured initial page.","relation":"different-from-captured-initial"},"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-004","atom_id":"ATOM-004","coverage_status":"testable","planned_test_case_id":"TC-SCCB-004","source_refs":["BSR 32","SRC-001","SRC-001.P04"],"atomic_statement":"Нажатие `Очистить` очищает состояние выделения строк.","observable_oracle":"После нажатия `Очистить` доказанно изменённое состояние выделения строк совпадает с зафиксированным initial state.","test_intent":"Capture the visible selection marker of each displayed row before changing selection.; Use the available row-selection action to make one displayed row marker differ from its captured value; if no different state can be produced, report fixture-blocked.; Before the target action verify: Before `Очистить`, the visible selection marker of at least one displayed row differs from its captured initial value.; Capture the initial visible row-selection markers; create and prove a different selection state; click `Очистить`.","execution_semantics":"reset-to-captured-initial","state_change":{"initial_state_capture":"Capture the visible selection marker of each displayed row before changing selection.","changed_state_setup":"Use the available row-selection action to make one displayed row marker differ from its captured value; if no different state can be produced, report fixture-blocked.","pre_action_state_oracle":"Before `Очистить`, the visible selection marker of at least one displayed row differs from its captured initial value.","relation":"different-from-captured-initial"},"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]}]}
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
    "test_case_count": 4,
    "testable_obligations": 4,
    "covered_obligations": [
      "OBL-001",
      "OBL-002",
      "OBL-003",
      "OBL-004"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 4
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
    "test_case_count": 4
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
  "test_case_count": 4,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\search-clear-context-exec-benchmark-v4-20260713\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v4-20260713/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"8e216a49fd15ddef0c1e2678a3a44ac86771877fbd960196702549c5e3f4e064","context_profile":"conditional-state","open_count":0,"resolved_count":0,"status_counts":{},"constraint_gap_ids":[],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-SCCB-001

**Название:** Очистка изменённого состояния фильтров поиска
**Тип:** позитивный
**Приоритет:** средний
**package_id:** search-clear-context-exec-benchmark-v4
**Трассировка:** OBL-001; ATOM-001; BSR 32; SRC-001; SRC-001.P01

### Предусловия

1. Открыта страница поиска; до изменения фильтра зафиксированы видимые значения и маркеры состояния фильтров.
2. По контракту `FIX-SCCB-001` доступно хотя бы одно видимое значение фильтра, позволяющее получить состояние, отличающееся от зафиксированного initial state.

### Тестовые данные

- Доступное видимое значение фильтра, при выборе которого его видимое состояние отличается от зафиксированного initial state.

### Шаги

1. Выбрать доступное значение фильтра и убедиться, что хотя бы одно видимое значение или маркер состояния фильтра отличается от зафиксированного initial state.
2. Нажать `Очистить`.

### Итоговый ожидаемый результат

После нажатия `Очистить` видимое состояние фильтров совпадает с зафиксированным initial state.

### Постусловия

- Не требуются: состояние фильтров возвращено к зафиксированному initial state.

## TC-SCCB-002

**Название:** Очистка изменённого состояния сортировки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** search-clear-context-exec-benchmark-v4
**Трассировка:** OBL-002; ATOM-002; BSR 32; SRC-001; SRC-001.P02

### Предусловия

1. Открыта таблица результатов; до изменения сортировки зафиксированы видимые индикаторы сортировки.
2. По контракту `FIX-SCCB-002` таблица содержит хотя бы один сортируемый заголовок и хотя бы одну отображаемую строку.

### Тестовые данные

- Сортируемый заголовок, позволяющий получить видимый индикатор сортировки, отличный от зафиксированного initial state.

### Шаги

1. Использовать сортируемый заголовок до появления видимого индикатора сортировки, отличающегося от зафиксированного initial state.
2. Нажать `Очистить`.

### Итоговый ожидаемый результат

После нажатия `Очистить` видимое состояние сортировки совпадает с зафиксированным initial state.

### Постусловия

- Не требуются: состояние сортировки возвращено к зафиксированному initial state.

## TC-SCCB-003

**Название:** Очистка изменённого состояния постраничности
**Тип:** позитивный
**Приоритет:** средний
**package_id:** search-clear-context-exec-benchmark-v4
**Трассировка:** OBL-003; ATOM-003; BSR 32; SRC-001; SRC-001.P03

### Предусловия

1. Открыта таблица результатов; до изменения постраничности зафиксирован видимый индикатор активной страницы.
2. По контракту `FIX-SCCB-003` доступна хотя бы одна страница с видимым индикатором активной страницы, отличающимся от зафиксированного initial state; иначе тест зафиксирован как fixture-blocked.

### Тестовые данные

- Доступная страница, индикатор активной страницы которой отличается от зафиксированного initial state.

### Шаги

1. Перейти на доступную страницу и убедиться, что видимый индикатор активной страницы отличается от зафиксированного initial state.
2. Нажать `Очистить`.

### Итоговый ожидаемый результат

После нажатия `Очистить` видимое состояние постраничности совпадает с зафиксированным initial state.

### Постусловия

- Не требуются: активная страница возвращена к зафиксированному initial state.

## TC-SCCB-004

**Название:** Очистка изменённого состояния выделения строк
**Тип:** позитивный
**Приоритет:** средний
**package_id:** search-clear-context-exec-benchmark-v4
**Трассировка:** OBL-004; ATOM-004; BSR 32; SRC-001; SRC-001.P04

### Предусловия

1. Открыта таблица результатов; до изменения выделения зафиксированы видимые маркеры выделения всех отображаемых строк.
2. По контракту `FIX-SCCB-002` таблица содержит хотя бы одну отображаемую строку с наблюдаемым состоянием выделения.

### Тестовые данные

- Отображаемая строка, для которой доступно действие изменения видимого маркера выделения.

### Шаги

1. Использовать доступное действие выделения строки и убедиться, что видимый маркер выделения хотя бы одной отображаемой строки отличается от зафиксированного initial state.
2. Нажать `Очистить`.

### Итоговый ожидаемый результат

После нажатия `Очистить` видимое состояние выделения строк совпадает с зафиксированным initial state.

### Постусловия

- Не требуются: состояние выделения строк возвращено к зафиксированному initial state.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
