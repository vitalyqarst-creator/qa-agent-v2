# Codex exec prepared-standard reviewer compact path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 7,
  "package_id": "visual-assessment-medium-scope-benchmark-v4",
  "package_digest": "0ef00ba00344229211375efcd280e7c3d2940e68e4f2af248d106c8181cb64ae",
  "input_fingerprint": "3bb4ae09be3b241aa119e15b3a62d5d8ecf36d556d579cd14f16e7568aff9871",
  "ft_slug": "AutoFin",
  "scope_slug": "visual-assessment-medium-scope-benchmark",
  "section_id": "18",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "dependency-state",
    "evidence-qualified-ui-calibration"
  ],
  "reviewed_draft_sha256": "0c512ea4369680a536dcdc3d065390667dc6bfaf61af0d1e660f110da8311cb5"
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
9. For UI-calibration candidates, require `ui-calibration-required`, `candidate-ui-calibration`, every linked constraint GAP when present, and a neutral expected result that does not preselect filtering/message/highlight/save behavior. Package-declared calibration without a GAP remains a valid lifecycle item.
10. Return exactly the structured review contract requested by the runner. Do not write files.

## Decision Floor

- `accepted` requires every obligation to have a compatible verdict, every testable obligation to be correctly covered, all gaps to be preserved and no error finding.
- `changes-required` requires at least one concrete finding linked to supplied ATOM/TC identifiers, unless it is a set-level scope finding.
- A failed deterministic gate, draft hash mismatch, unknown identifier, lost constraint gap or insufficient evidence prevents sign-off.

## Runtime Boundary

No command is needed. If runtime confirmation is absolutely required, only the explicitly allowlisted environment probe may be used. Any repository exploration or workspace mutation violates the compact prepared reviewer contract.

## Context profile: `character-restriction-calibration`

- Keep each invalid class and field independent.
- Preserve every constraint_gap_ids marker. Independently preserve calibration_status=ui-calibration-required with ui-calibration-required and candidate-ui-calibration, even without a GAP.
- Do not choose a validation message, filtering, highlight, save or transition mechanism that the evidence does not define.

## Selected source evidence

# Prepared Source Evidence

- package_id: `visual-assessment-medium-scope-benchmark-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v4-r1-20260714/prepared-input/.visual-assessment-medium-scope-benchmark-v4.compiled-evidence.md`
- source_sha256: `7f87475366a44cd13c3a5b9a342699807e26c29cd3cd66ab6589408320398ddf`
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

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. This compact projection contains every exact review-contract ID plus its source-backed statement, oracle, intent, reference and gap; the runner validates the final contract against the immutable artifact.

```json
{"artifact":"fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v4-r1-20260714/prepared-input/visual-assessment-medium-scope-benchmark-v4/atomic-obligations.json","artifact_sha256":"6fd49ada148da93d1ad059988b898eeeca70a00ddf16a7eb0b18748c2eb7bd0f","obligation_count":13,"semantic_evidence_source":"selected-source-evidence","coverage_gaps":[],"dictionary_evidence":[{"dictionary_id":"DICT-001","dictionary_name":"Параметры визуальной оценки","source_file":"source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf","source_location":"Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md","extraction_status":"extracted","active_values":["DICT-101","DICT-102","DICT-103","DICT-104","DICT-105","DICT-106","DICT-107","DICT-108"],"archived_values":"none_required:no-archived-values"},{"dictionary_id":"DICT-108","dictionary_name":"Прочие признаки (комментарий обязателен)","source_file":"source/FT4AutoFinFinal.xhtml; source/FT4AutoFinFinal.docx; source/FT4AutoFinFinal.pdf","source_location":"Appendix 1; aggregate reference `work/test-design/14-application-card/appendix-1-visual-assessment-reference.md","extraction_status":"extracted","active_values":["none_required:standalone-comment-only"],"archived_values":"none_required:no-archived-values"}],"obligations":[{"obligation_id":"OBL-001","atom_id":"ATOM-001","coverage_status":"testable","planned_test_case_id":"TC-VAMB-001","source_refs":["SRC-002.P01","BSR 311","SRC-001","SRC-002"],"atomic_statement":"Поле `Визуальная информация` отображается всегда.","observable_oracle":"Поле `Визуальная информация` отображается всегда.","test_intent":"Открыть блок визуальной оценки в доступной анкете клиента.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-002","atom_id":"ATOM-002","coverage_status":"testable","planned_test_case_id":"TC-VAMB-002","source_refs":["SRC-002.P02","BSR 312","SRC-002"],"atomic_statement":"Для поля `Визуальная информация` значение по умолчанию равно `Нет`.","observable_oracle":"Значение по умолчанию равно `Нет`.","test_intent":"Открыть блок визуальной оценки до изменения поля.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-003","atom_id":"ATOM-003","coverage_status":"testable","planned_test_case_id":"TC-VAMB-003","source_refs":["SRC-002.P03","BSR 313","SRC-002","BSR 314"],"atomic_statement":"Выбор `Да` в поле `Визуальная информация` является условием показа параметров визуальной оценки.","observable_oracle":"После выбора `Да` отображается список `Параметры визуальной оценки`.","test_intent":"Выбрать `Да` в поле `Визуальная информация`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-004","atom_id":"ATOM-004","coverage_status":"testable","planned_test_case_id":"TC-VAMB-003","source_refs":["SRC-003.P01","BSR 314","SRC-003"],"atomic_statement":"При `Визуальная информация = Да` отображается список `Параметры визуальной оценки`.","observable_oracle":"После выбора `Да` отображается список `Параметры визуальной оценки`.","test_intent":"Выбрать `Да` в поле `Визуальная информация`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-005","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-VAMB-004","source_refs":["SRC-003.P02","BSR 314","SRC-003"],"atomic_statement":"Когда `Визуальная информация` не равна `Да`, список `Параметры визуальной оценки` не отображается.","observable_oracle":"Когда `Визуальная информация` не равна `Да`, список параметров не отображается.","test_intent":"Выбрать `Нет` в поле `Визуальная информация`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-006","atom_id":"ATOM-006","coverage_status":"testable","planned_test_case_id":"TC-VAMB-005","source_refs":["SRC-003.P03","BSR 315","SRC-003-SRC-052","DICT-001"],"atomic_statement":"`Параметры визуальной оценки` содержит восемь групп и полный состав значений из `DICT-001`.","observable_oracle":"Список содержит восемь групп и полный состав значений из `DICT-001`.","test_intent":"Выбрать `Да` и сверить группы и значения списка с полным `DICT-001`.","execution_semantics":"direct","state_change":null,"dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-007","atom_id":"ATOM-007","coverage_status":"testable","planned_test_case_id":"TC-VAMB-006","source_refs":["SRC-003.P04","BSR 315","SRC-005-SRC-050","DICT-001"],"atomic_statement":"Каждое обычное значение критерия из `DICT-001` доступно как checkbox value.","observable_oracle":"Каждое обычное значение `DICT-001` доступно как checkbox.","test_intent":"Проверить control type каждого обычного значения `DICT-001`.","execution_semantics":"direct","state_change":null,"dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-008","atom_id":"ATOM-008","coverage_status":"testable","planned_test_case_id":"TC-VAMB-007","source_refs":["SRC-003.P05","BSR 316","SRC-003"],"atomic_statement":"При `Визуальная информация = Да` требуется выбрать минимум одно значение; точный UI-механизм подтверждается последующей калибровкой.","observable_oracle":"`ui-calibration-required`; `candidate-ui-calibration`: при `Визуальная информация = Да` и пустом выборе выполнить следующее доступное действие формы и зафиксировать фактическое видимое состояние блока и результат действия, не утверждая текст сообщения, подсветку или blocked transition.","test_intent":"При `Визуальная информация = Да` оставить все параметры невыбранными и выполнить следующее доступное действие формы.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-009","atom_id":"ATOM-009","coverage_status":"testable","planned_test_case_id":"TC-VAMB-008","source_refs":["SRC-003.P06","BSR 317","SRC-009","SRC-019","SRC-024","SRC-030","SRC-036","SRC-043","SRC-050","DICT-001","DICT-108"],"atomic_statement":"Выбор checkbox `Другое` в группе отображает текстовое поле комментария.","observable_oracle":"Выбор checkbox `Другое` отображает текстовое поле комментария.","test_intent":"Выбрать checkbox `Другое` в любой группе, где он предусмотрен.","execution_semantics":"direct","state_change":null,"dictionary_refs":["DICT-001","DICT-108"],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-010","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-VAMB-009","source_refs":["SRC-003.P07","BSR 317","SRC-009","SRC-019","SRC-024","SRC-030","SRC-036","SRC-043","SRC-050","DICT-001"],"atomic_statement":"При выбранном `Другое` комментарий обязателен; точный UI-механизм подтверждается последующей калибровкой.","observable_oracle":"`ui-calibration-required`; `candidate-ui-calibration`: выбрать `Другое`, оставить открывшийся комментарий пустым, выполнить следующее доступное действие формы и зафиксировать фактическое видимое состояние поля и результат действия, не утверждая текст сообщения, подсветку или blocked transition.","test_intent":"Выбрать `Другое` в любой группе, где оно предусмотрено, оставить открывшийся комментарий пустым и выполнить следующее доступное действие формы.","execution_semantics":"direct","state_change":null,"dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-011","atom_id":"ATOM-011","coverage_status":"testable","planned_test_case_id":"TC-VAMB-010","source_refs":["SRC-010.P01","SRC-010","SRC-020","SRC-051","SRC-052"],"atomic_statement":"Standalone-строки `Комментарий` являются отдельными полями ввода и не смешиваются с checkbox `Другое`.","observable_oracle":"Standalone-строки `Комментарий` отображаются как отдельные поля ввода и не смешиваются с `Другое`.","test_intent":"Выбрать `Да` и осмотреть standalone-строки `Комментарий`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-012","atom_id":"ATOM-012","coverage_status":"testable","planned_test_case_id":"TC-VAMB-011","source_refs":["SRC-010.P02","SRC-010","SRC-020","SRC-051","SRC-052"],"atomic_statement":"Standalone-поле `Комментарий` принимает введённый текст.","observable_oracle":"После ввода текста `Наблюдение теста` standalone-поле отображает значение `Наблюдение теста`.","test_intent":"Ввести `Наблюдение теста` в standalone-поле `Комментарий`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-013","atom_id":"ATOM-013","coverage_status":"testable","planned_test_case_id":"TC-VAMB-012","source_refs":["SRC-003.P08","BSR 313","BSR 315","SRC-002","SRC-003","SRC-005-SRC-050","DICT-001"],"atomic_statement":"В checkbox list можно одновременно выбрать несколько обычных значений критериев.","observable_oracle":"После выбора двух обычных значений оба checkbox остаются выбранными одновременно.","test_intent":"В группе `Признаки алкоголика` (`DICT-101`) последовательно выбрать `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар` и `Отечность, нездоровый цвет лица, синяки под глазами`.","execution_semantics":"direct","state_change":null,"dictionary_refs":["DICT-001"],"gap_id":"","constraint_gap_ids":[]}]}
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
    "validator": "prepared-package-obligation-gate-v4",
    "findings_count": 0,
    "test_case_count": 12,
    "testable_obligations": 13,
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
      "OBL-013"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 12
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
    "test_case_count": 12
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
  "test_case_count": 12,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\visual-assessment-medium-scope-benchmark-v4-r1-20260714\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v4-r1-20260714/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"3535b3ee9c9a3fdb82550daccee5a712e0d743fdfbfbb2e6307677dc255fe378","context_profile":"character-restriction-calibration","open_count":2,"resolved_count":0,"status_counts":{"awaiting-ui-calibration":2},"constraint_gap_ids":[],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-VAMB-001

**Название:** Отображение поля «Визуальная информация»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-001; ATOM-001; SRC-002.P01; BSR 311; SRC-001; SRC-002

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть блок визуальной оценки в анкете клиента.

### Итоговый ожидаемый результат

Поле `Визуальная информация` отображается.

### Постусловия

- Не требуются.

## TC-VAMB-002

**Название:** Значение по умолчанию поля «Визуальная информация» — «Нет»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-002; ATOM-002; SRC-002.P02; BSR 312; SRC-002

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки, в котором значение поля `Визуальная информация` ещё не изменялось.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть блок визуальной оценки.

### Итоговый ожидаемый результат

В поле `Визуальная информация` выбрано значение `Нет`.

### Постусловия

- Не требуются.

## TC-VAMB-003

**Название:** Отображение списка параметров после выбора «Да»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-003; ATOM-003; SRC-002.P03; BSR 313; SRC-002; BSR 314; OBL-004; ATOM-004; SRC-003.P01; SRC-003

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Значение поля `Визуальная информация`: `Да`.

### Шаги

1. В поле `Визуальная информация` выбрать `Да`.

### Итоговый ожидаемый результат

Отображается список `Параметры визуальной оценки`.

### Постусловия

- Не требуются.

## TC-VAMB-004

**Название:** Скрытие списка параметров при значении «Нет»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-005; ATOM-005; SRC-003.P02; BSR 314; SRC-003

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Значение поля `Визуальная информация`: `Нет`.

### Шаги

1. В поле `Визуальная информация` выбрать `Нет`.

### Итоговый ожидаемый результат

Список `Параметры визуальной оценки` не отображается.

### Постусловия

- Не требуются.

## TC-VAMB-005

**Название:** Полный состав списка параметров визуальной оценки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-006; ATOM-006; SRC-003.P03; BSR 315; SRC-003-SRC-052; DICT-001

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Справочник для сверки: `DICT-001`, режим покрытия `full-hierarchy`.



<!-- runner-dictionary-projection:start OBL-006 -->
- Полный набор `DICT-001` (`full-hierarchy`):
- Группа `DICT-001 > DICT-101`: `Признаки алкоголика`
- Значение `DICT-001 > DICT-101`: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`
- Значение `DICT-001 > DICT-101`: `Отечность, нездоровый цвет лица, синяки под глазами`
- Значение `DICT-001 > DICT-101`: `Шатающаяся походка, несвязная речь, сильно трясутся руки`
- Значение `DICT-001 > DICT-101`: `Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени`
- Значение `DICT-001 > DICT-101`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-102`: `Признаки наркомана`
- Значение `DICT-001 > DICT-102`: `Длинные, спущенные рукава в любую погоду, отрешенный взгляд`
- Значение `DICT-001 > DICT-102`: `Неоправданно резкие перемены настроения`
- Значение `DICT-001 > DICT-102`: `Отечность, нездоровый цвет лица, синяки под глазами`
- Значение `DICT-001 > DICT-102`: `Следы многочисленных уколов на кистях`
- Значение `DICT-001 > DICT-102`: `Неестественно суженные / расширенные зрачки`
- Значение `DICT-001 > DICT-102`: `Шатающаяся походка, несвязная речь, плохая координация движений`
- Значение `DICT-001 > DICT-102`: `Неприятный запах кислоты`
- Значение `DICT-001 > DICT-102`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-103`: `Признаки бывшего заключенного`
- Значение `DICT-001 > DICT-103`: `Татуировки уголовного содержания на кистях, пальцах (например, с изображением перстней, крестов, четырех точек, образующих квадрат с пятой точкой посередине и др.)`
- Значение `DICT-001 > DICT-103`: `Характерный для заключенных жаргон`
- Значение `DICT-001 > DICT-103`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-104`: `Признаки «преображенного» бомжа`
- Значение `DICT-001 > DICT-104`: `Несоответствие внешнего вида Клиента данным, которые он указывает в анкете (например, в анкете указано, что Клиент - гендиректор крупной организации, однако состояние зубов, волос, лица или кистей рук говорит о том, что ему полностью безразличны его внешний вид и здоровье)`
- Значение `DICT-001 > DICT-104`: `Признаки алкоголика / наркомана / бывшего заключенного`
- Значение `DICT-001 > DICT-104`: `Несоответствие размеров / стиля одежды`
- Значение `DICT-001 > DICT-104`: `Сильный макияж / использует парик`
- Значение `DICT-001 > DICT-104`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-105`: `Поведенческие признаки потенциального неплательщика`
- Значение `DICT-001 > DICT-105`: `Клиент не может внятно объяснить, откуда он узнал о Банке / для чего ему необходим кредит, при этом испытывает волнение / раздражение`
- Значение `DICT-001 > DICT-105`: `Мнимые семейные пары, часто с детьми (например Клиент называет свою "супругу" Надей, а в штампе паспорта имя супруги - Елена)`
- Значение `DICT-001 > DICT-105`: `неадекватная реакция на вопросы о супруге / детях`
- Значение `DICT-001 > DICT-105`: `Сильное волнение клиента в ходе анкетирования, особенно при ответах на дополнительные / уточняющие вопросы`
- Значение `DICT-001 > DICT-105`: `Слишком заострено внимание на последствиях неплатежей`
- Значение `DICT-001 > DICT-105`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-106`: `Сопровождение Клиента`
- Значение `DICT-001 > DICT-106`: `Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки по заполнению анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент находится в сопровождении подозрительных лиц, осуществляющих давление на Клиента`
- Значение `DICT-001 > DICT-106`: `Клиент использовал "шпаргалку" при заполнении анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент неоднократно звонил по телефону для выяснения ответов на вопросы анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент замечен в сопровождении лиц, ранее приводивших мошенников / подставных лиц для получения кредитов`
- Значение `DICT-001 > DICT-106`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-107`: `Признаки подделки документов`
- Значение `DICT-001 > DICT-107`: `Заметны следы подчистки документов, химического травления текста`
- Значение `DICT-001 > DICT-107`: `Заметны следы подделки подписей, оттисков печатей и штампов`
- Значение `DICT-001 > DICT-107`: `Наличие в документах дописок, допечаток, исправлений, орфографических ошибок`
- Значение `DICT-001 > DICT-107`: `Личность заемщика не может быть достоверно подтверждена (заемщик явно не похож по фотографии)`
- Значение `DICT-001 > DICT-107`: `Заметны следы замены фотографии в паспорте, листов в многостраничных документах`
- Значение `DICT-001 > DICT-107`: `Другое (комментарий обязателен)`
- Группа `DICT-001 > DICT-108`: `Прочие признаки (комментарий обязателен)`
<!-- runner-dictionary-projection:end OBL-006 -->

### Шаги

1. В поле `Визуальная информация` выбрать `Да`.
2. Сверить отображаемые группы и значения списка `Параметры визуальной оценки` с полным составом `DICT-001`.

### Итоговый ожидаемый результат

Отображаются все восемь групп и все активные значения `DICT-001`, без пропусков и добавлений.

### Постусловия

- Не требуются.

## TC-VAMB-006

**Название:** Тип элемента для обычных значений параметров визуальной оценки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-007; ATOM-007; SRC-003.P04; BSR 315; SRC-005-SRC-050; DICT-001

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Справочник для сверки: `DICT-001`, режим покрытия `all-leaf-values`.



<!-- runner-dictionary-projection:start OBL-007 -->
- Полный набор `DICT-001` (`all-leaf-values`):
- Значение `DICT-001 > DICT-101`: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар`
- Значение `DICT-001 > DICT-101`: `Отечность, нездоровый цвет лица, синяки под глазами`
- Значение `DICT-001 > DICT-101`: `Шатающаяся походка, несвязная речь, сильно трясутся руки`
- Значение `DICT-001 > DICT-101`: `Неадекватная реакция на задаваемые вопросы, плохая ориентация во времени`
- Значение `DICT-001 > DICT-101`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-102`: `Длинные, спущенные рукава в любую погоду, отрешенный взгляд`
- Значение `DICT-001 > DICT-102`: `Неоправданно резкие перемены настроения`
- Значение `DICT-001 > DICT-102`: `Отечность, нездоровый цвет лица, синяки под глазами`
- Значение `DICT-001 > DICT-102`: `Следы многочисленных уколов на кистях`
- Значение `DICT-001 > DICT-102`: `Неестественно суженные / расширенные зрачки`
- Значение `DICT-001 > DICT-102`: `Шатающаяся походка, несвязная речь, плохая координация движений`
- Значение `DICT-001 > DICT-102`: `Неприятный запах кислоты`
- Значение `DICT-001 > DICT-102`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-103`: `Татуировки уголовного содержания на кистях, пальцах (например, с изображением перстней, крестов, четырех точек, образующих квадрат с пятой точкой посередине и др.)`
- Значение `DICT-001 > DICT-103`: `Характерный для заключенных жаргон`
- Значение `DICT-001 > DICT-103`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-104`: `Несоответствие внешнего вида Клиента данным, которые он указывает в анкете (например, в анкете указано, что Клиент - гендиректор крупной организации, однако состояние зубов, волос, лица или кистей рук говорит о том, что ему полностью безразличны его внешний вид и здоровье)`
- Значение `DICT-001 > DICT-104`: `Признаки алкоголика / наркомана / бывшего заключенного`
- Значение `DICT-001 > DICT-104`: `Несоответствие размеров / стиля одежды`
- Значение `DICT-001 > DICT-104`: `Сильный макияж / использует парик`
- Значение `DICT-001 > DICT-104`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-105`: `Клиент не может внятно объяснить, откуда он узнал о Банке / для чего ему необходим кредит, при этом испытывает волнение / раздражение`
- Значение `DICT-001 > DICT-105`: `Мнимые семейные пары, часто с детьми (например Клиент называет свою "супругу" Надей, а в штампе паспорта имя супруги - Елена)`
- Значение `DICT-001 > DICT-105`: `неадекватная реакция на вопросы о супруге / детях`
- Значение `DICT-001 > DICT-105`: `Сильное волнение клиента в ходе анкетирования, особенно при ответах на дополнительные / уточняющие вопросы`
- Значение `DICT-001 > DICT-105`: `Слишком заострено внимание на последствиях неплатежей`
- Значение `DICT-001 > DICT-105`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-106`: `Клиент находится в сопровождении подозрительных лиц, осуществляющих подсказки по заполнению анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент находится в сопровождении подозрительных лиц, осуществляющих давление на Клиента`
- Значение `DICT-001 > DICT-106`: `Клиент использовал "шпаргалку" при заполнении анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент неоднократно звонил по телефону для выяснения ответов на вопросы анкеты`
- Значение `DICT-001 > DICT-106`: `Клиент замечен в сопровождении лиц, ранее приводивших мошенников / подставных лиц для получения кредитов`
- Значение `DICT-001 > DICT-106`: `Другое (комментарий обязателен)`
- Значение `DICT-001 > DICT-107`: `Заметны следы подчистки документов, химического травления текста`
- Значение `DICT-001 > DICT-107`: `Заметны следы подделки подписей, оттисков печатей и штампов`
- Значение `DICT-001 > DICT-107`: `Наличие в документах дописок, допечаток, исправлений, орфографических ошибок`
- Значение `DICT-001 > DICT-107`: `Личность заемщика не может быть достоверно подтверждена (заемщик явно не похож по фотографии)`
- Значение `DICT-001 > DICT-107`: `Заметны следы замены фотографии в паспорте, листов в многостраничных документах`
- Значение `DICT-001 > DICT-107`: `Другое (комментарий обязателен)`
<!-- runner-dictionary-projection:end OBL-007 -->

### Шаги

1. В поле `Визуальная информация` выбрать `Да`.
2. Проверить тип элемента управления для каждого обычного значения `DICT-001`.

### Итоговый ожидаемый результат

Каждое обычное значение `DICT-001` доступно как checkbox.

### Постусловия

- Не требуются.

## TC-VAMB-007

**Название:** Калибровка обязательности выбора параметра визуальной оценки
**Тип:** негативный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-008; ATOM-008; SRC-003.P05; BSR 316; SRC-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.
2. В поле `Визуальная информация` выбрано `Да`.
3. Ни один параметр визуальной оценки не выбран.

### Тестовые данные

- Пустой выбор параметров визуальной оценки.

### Шаги

1. Выполнить следующее доступное действие формы.

### Итоговый ожидаемый результат

`ui-calibration-required`; `candidate-ui-calibration`: зафиксировано фактическое видимое состояние блока `Параметры визуальной оценки` и результат выполненного действия без утверждения текста сообщения, подсветки или блокировки перехода.

### Постусловия

- Не требуются.

## TC-VAMB-008

**Название:** Отображение комментария после выбора «Другое»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-009; ATOM-009; SRC-003.P06; BSR 317; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; DICT-001; DICT-108

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.
2. В поле `Визуальная информация` выбрано `Да`.

### Тестовые данные

- Checkbox `Другое` в группе, где он предусмотрен.

### Шаги

1. Выбрать checkbox `Другое`.

### Итоговый ожидаемый результат

В той же группе отображается текстовое поле комментария.

### Постусловия

- Не требуются.

## TC-VAMB-009

**Название:** Калибровка обязательности комментария для «Другое»
**Тип:** негативный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-010; ATOM-010; SRC-003.P07; BSR 317; SRC-009; SRC-019; SRC-024; SRC-030; SRC-036; SRC-043; SRC-050; DICT-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.
2. В поле `Визуальная информация` выбрано `Да`.
3. Выбран checkbox `Другое`, и открывшееся поле комментария оставлено пустым.

### Тестовые данные

- Пустой комментарий для выбранного `Другое`.

### Шаги

1. Выполнить следующее доступное действие формы.

### Итоговый ожидаемый результат

`ui-calibration-required`; `candidate-ui-calibration`: зафиксировано фактическое видимое состояние поля комментария и результат выполненного действия без утверждения текста сообщения, подсветки или блокировки перехода.

### Постусловия

- Не требуются.

## TC-VAMB-010

**Название:** Отдельное отображение standalone-полей «Комментарий»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-011; ATOM-011; SRC-010.P01; SRC-010; SRC-020; SRC-051; SRC-052

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.

### Тестовые данные

- Значение поля `Визуальная информация`: `Да`.

### Шаги

1. В поле `Визуальная информация` выбрать `Да`.
2. Осмотреть standalone-строки `Комментарий` в списке параметров визуальной оценки.

### Итоговый ожидаемый результат

Standalone-строки `Комментарий` отображаются как отдельные поля ввода и не являются checkbox `Другое`.

### Постусловия

- Не требуются.

## TC-VAMB-011

**Название:** Ввод текста в standalone-поле «Комментарий»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-012; ATOM-012; SRC-010.P02; SRC-010; SRC-020; SRC-051; SRC-052

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.
2. Отображается standalone-поле `Комментарий`.

### Тестовые данные

- Текст комментария: `Наблюдение теста`.

### Шаги

1. Ввести `Наблюдение теста` в standalone-поле `Комментарий`.

### Итоговый ожидаемый результат

Standalone-поле `Комментарий` отображает значение `Наблюдение теста`.

### Постусловия

- Не требуются.

## TC-VAMB-012

**Название:** Одновременный выбор двух обычных параметров визуальной оценки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** visual-assessment-medium-scope-benchmark-v4
**Трассировка:** OBL-013; ATOM-013; SRC-003.P08; BSR 313; BSR 315; SRC-002; SRC-003; SRC-005-SRC-050; DICT-001

### Предусловия

1. Доступна анкета клиента с блоком визуальной оценки.
2. В поле `Визуальная информация` выбрано `Да`.

### Тестовые данные

- Два обычных значения из `DICT-101`.

### Шаги

1. В группе `DICT-101` последовательно выбрать два обычных значения.

### Итоговый ожидаемый результат

Оба выбранных checkbox остаются выбранными одновременно.

### Постусловия

- Не требуются.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
