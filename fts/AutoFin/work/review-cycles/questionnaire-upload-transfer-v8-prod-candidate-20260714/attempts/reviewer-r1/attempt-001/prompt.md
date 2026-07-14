# Codex exec prepared-standard reviewer compact path

The upstream package and runner already applied the full source, scope, reviewer-routing and deterministic validation contracts.
Use only the embedded Prepared Reviewer Runtime Profile and verified payload below. Do not load the full ft-test-case-reviewer skill, instruction manifest, package files, project references, prior cycles, production test cases or full sources.
This stage is read-only. Do not modify or create any workspace file.
No shell command is needed. If the runtime environment is not already confirmed, only `python scripts/probe_environment.py` is allowed.

<!-- PREPARED-REVIEW-PAYLOAD:BEGIN -->
## Verified review metadata

```json
{
  "package_version": 8,
  "package_id": "questionnaire-upload-transfer-v8-prod-candidate-r1",
  "package_digest": "d84baaba4f46eacfff012d4884fab9c03556dd36b2b8e163c2c102649b9fa731",
  "input_fingerprint": "935aa313baf111cd2044bf5fe62039fecb2640b3a0c6ea95da991424a0a21007",
  "ft_slug": "AutoFin",
  "scope_slug": "questionnaire-upload-transfer-v8-prod-candidate",
  "section_id": "16",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "file-upload",
    "input-boundaries",
    "negative-oracle",
    "visibility"
  ],
  "reviewed_draft_sha256": "30737645afe53d3535db78c005968225b495e63a11ec201edeed2db107e2080b"
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

- package_id: `questionnaire-upload-transfer-v8-prod-candidate-r1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/prepared-input/.questionnaire-upload-transfer-v8-prod-candidate-r1.compiled-evidence.md`
- source_sha256: `8bda098bc64de1bbc0de3635b657ed155593ba3557447f8635eabd631e4efa2e`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## Mandatory package context

source_path: fts/AutoFin/AGENT-NOTES.md

# Package Notes: AutoFin

## Сокращения В Таблицах UI-Полей

Статус: package-specific рабочее правило для AutoFin, добавленное по подтверждению пользователя и сверенное с аналогичными заметками в `fts/ft-2-OF_16/AGENT-NOTES.md`, `fts/ft-2-OF_17/AGENT-NOTES.md`, `fts/ft-2-OF_18/AGENT-NOTES.md`.

В таблицах описания свойств полей формы столбец `О` означает `Обязательность`, а столбец `Р` означает `Редактируемость`.

<!-- DaData package notes: not applicable to selected scope. -->

## Source-to-package fidelity bindings

```json
[{"atom_id":"ATOM-001","binding_id":"FID-QUT-001","binding_kind":"literal","handling":"preserve","obligation_id":"OBL-QUT-001","required_targets":["atomic_statement","required_behavior","single_expected_behavior"],"source_ref":"BSR 206; DOCX table 6 row 81; XHTML row 134","source_text":"Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку"},{"atom_id":"ATOM-008","binding_id":"FID-QUT-002","binding_kind":"unit","decision_reason":"Final FT does not define decimal or binary byte convention.","gap_id":"GAP-QUT-001","handling":"coverage-gap","obligation_id":"OBL-QUT-008","required_targets":["atomic_statement","required_behavior","single_expected_behavior"],"source_ref":"BSR 210; DOCX table 6 row 82; XHTML row 135","source_text":"размер файла не более 40 МБ","unit_symbol":"МБ","unit_value":40},{"atom_id":"ATOM-009","binding_id":"FID-QUT-003","binding_kind":"unit","decision_reason":"50 МБ fixture is unambiguously over the limit under both conventions.","handling":"source-unit-only","obligation_id":"OBL-QUT-009","required_targets":["atomic_statement","required_behavior","single_expected_behavior"],"source_ref":"BSR 210; DOCX table 6 row 82; XHTML row 135","source_text":"размер файла не более 40 МБ","unit_symbol":"МБ","unit_value":40}]
```

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. This compact projection contains every exact review-contract ID plus its source-backed statement, oracle, intent, reference and gap; the runner validates the final contract against the immutable artifact.

```json
{"artifact":"fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/prepared-input/questionnaire-upload-transfer-v8-prod-candidate-r1/atomic-obligations.json","artifact_sha256":"8ab8b469faf5be8b231200ba66461b9f88ffe77724390775a1e4a9ecf141eaf5","obligation_count":11,"semantic_evidence_source":"selected-source-evidence","coverage_gaps":[{"gap_id":"GAP-QUT-001","source_refs":["BSR 210","SRC-QUT-002.P06","ATOM-008","OBL-QUT-008"],"problem":"BSR 210; SRC-QUT-002.P06; DOCX table 6 row 82; XHTML row 135; размер файла не более 40 МБ","handling":"Сохранить `ATOM-008` / `OBL-QUT-008` как отдельный gap; не создавать exact-boundary/just-over byte TC. Writer и reviewer могут обработать остальные 10 testable obligations при явном сохранении этого ограничения.","blocking":false}],"dictionary_evidence":[],"obligations":[{"obligation_id":"OBL-QUT-001","atom_id":"ATOM-001","coverage_status":"testable","planned_test_case_id":"TC-QUT-001","source_refs":["SRC-QUT-001.P01","BSR 206","SRC-QUT-001"],"atomic_statement":"Буквальный текст `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку` отображается всегда.","observable_oracle":"Буквальный текст `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку` отображается всегда.","test_intent":"Открыть блок `Документы по заявке`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-002","atom_id":"ATOM-002","coverage_status":"testable","planned_test_case_id":"TC-QUT-002","source_refs":["SRC-QUT-001.P02","BSR 207","SRC-QUT-001"],"atomic_statement":"Информационное поле не допускает ручного редактирования своего текста.","observable_oracle":"Текст информационного поля нельзя изменить ручным вводом.","test_intent":"Установить фокус на информационном поле и попытаться ввести `Тест`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-003","atom_id":"ATOM-003","coverage_status":"testable","planned_test_case_id":"TC-QUT-003","source_refs":["SRC-QUT-002.P01","BSR 208","SRC-QUT-002"],"atomic_statement":"Поле добавления файла `Анкета клиента` отображается всегда.","observable_oracle":"Поле добавления файла `Анкета клиента` отображается всегда.","test_intent":"Открыть блок `Документы по заявке`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-004","atom_id":"ATOM-004","coverage_status":"testable","planned_test_case_id":"TC-QUT-004","source_refs":["SRC-QUT-002.P02","BSR 209","SRC-QUT-002"],"atomic_statement":"Документ можно добавить через открытие проводника по кнопке.","observable_oracle":"После выбора portable jpg через проводник файл добавлен.","test_intent":"По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-005","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-QUT-004","source_refs":["SRC-QUT-002.P03","BSR 211","SRC-QUT-002"],"atomic_statement":"После добавления документа отображается имя прикреплённого файла.","observable_oracle":"После добавления отображается точное имя выбранного файла.","test_intent":"По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-006","atom_id":"ATOM-006","coverage_status":"testable","planned_test_case_id":"TC-QUT-005","source_refs":["SRC-QUT-002.P04","BSR 209","SRC-QUT-002","BSR 211"],"atomic_statement":"Документ можно добавить через Drag and Drop.","observable_oracle":"После Drag and Drop portable pdf файл добавлен и его имя отображается.","test_intent":"Перетащить `FIXTURE-QUT-PDF` в поле `Анкета клиента`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-007","atom_id":"ATOM-007","coverage_status":"testable","planned_test_case_id":"TC-QUT-006","source_refs":["SRC-QUT-002.P05","BSR 210","SRC-QUT-002"],"atomic_statement":"Поле принимает файлы форматов jpg, png и pdf.","observable_oracle":"В отдельных чистых итерациях jpg, png и pdf добавляются успешно.","test_intent":"В трёх чистых итерациях добавить `FIXTURE-QUT-JPG`, `FIXTURE-QUT-PNG`, `FIXTURE-QUT-PDF`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-008","atom_id":"ATOM-008","coverage_status":"gap","planned_test_case_id":"","source_refs":["SRC-QUT-002.P06","BSR 210","SRC-QUT-002"],"atomic_statement":"Точное граничное значение для `размер файла не более 40 МБ` нельзя задать без byte convention.","observable_oracle":"","test_intent":"Точное граничное значение для `размер файла не более 40 МБ` нельзя задать без byte convention.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"GAP-QUT-001","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-009","atom_id":"ATOM-009","coverage_status":"testable","planned_test_case_id":"TC-QUT-007","source_refs":["SRC-QUT-002.P07","BSR 210","SRC-QUT-002"],"atomic_statement":"Ограничение `размер файла не более 40 МБ`: файл размером 50 МБ не загружается и отображается точный текст ошибки.","observable_oracle":"Ограничение `размер файла не более 40 МБ`: файл размером 50 МБ не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.","test_intent":"Добавить `FIXTURE-QUT-PDF-OVER40`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-010","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-QUT-008","source_refs":["SRC-QUT-002.P08","BSR 210","SRC-QUT-002"],"atomic_statement":"Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ.","observable_oracle":"Файл txt не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.","test_intent":"Добавить `FIXTURE-QUT-TXT`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-011","atom_id":"ATOM-011","coverage_status":"testable","planned_test_case_id":"TC-QUT-009","source_refs":["SRC-QUT-002.P09","BSR 210","SRC-QUT-002"],"atomic_statement":"После попытки добавить второй файл в типе документа остаётся не более одного файла.","observable_oracle":"После попытки добавить второй файл отображается не более одного имени файла этого типа.","test_intent":"Добавить `FIXTURE-QUT-PDF-A`, затем попытаться добавить `FIXTURE-QUT-PDF-B`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]}]}
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
    "test_case_count": 9,
    "testable_obligations": 10,
    "covered_obligations": [
      "OBL-QUT-001",
      "OBL-QUT-002",
      "OBL-QUT-003",
      "OBL-QUT-004",
      "OBL-QUT-005",
      "OBL-QUT-006",
      "OBL-QUT-007",
      "OBL-QUT-009",
      "OBL-QUT-010",
      "OBL-QUT-011"
    ]
  },
  {
    "gate": "semantic-overlap",
    "passed": true,
    "validator": "semantic-overlap-diagnostic-v1",
    "findings_count": 0,
    "test_case_count": 9
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
    "test_case_count": 9
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
  "test_case_count": 9,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\questionnaire-upload-transfer-v8-prod-candidate-20260714\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"29bb0927b8f662349b07b14496c2f973be30aa88a4b5948a075f039a76b5126a","context_profile":"character-restriction-calibration","open_count":0,"resolved_count":0,"status_counts":{},"constraint_gap_ids":[],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-QUT-001

**Название:** Постоянное отображение текста информационного поля «Анкета клиента»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-001; ATOM-001; SRC-QUT-001.P01; BSR 206; SRC-QUT-001

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть блок `Документы по заявке`.

### Итоговый ожидаемый результат

Отображается буквальный текст `Анкета клиента. Распечатайте, подпишите с клиентом и загрузите скан в заявку`.

### Постусловия

- Не применимо.

## TC-QUT-002

**Название:** Запрет ручного редактирования текста информационного поля
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-002; ATOM-002; SRC-QUT-001.P02; BSR 207; SRC-QUT-001

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- Текст для ввода: `Тест`.

### Шаги

1. Установить фокус на информационном поле с текстом об анкете клиента.
2. Попытаться ввести текст `Тест`.

### Итоговый ожидаемый результат

Текст информационного поля не изменяется.

### Постусловия

- Не применимо.

## TC-QUT-003

**Название:** Постоянное отображение поля добавления файла «Анкета клиента»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-003; ATOM-003; SRC-QUT-002.P01; BSR 208; SRC-QUT-002

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- Не требуются.

### Шаги

1. Открыть блок `Документы по заявке`.

### Итоговый ожидаемый результат

Отображается поле добавления файла `Анкета клиента`.

### Постусловия

- Не применимо.

## TC-QUT-004

**Название:** Добавление JPG-файла через проводник с отображением имени
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-004; ATOM-004; SRC-QUT-002.P02; BSR 209; SRC-QUT-002; OBL-QUT-005; ATOM-005; SRC-QUT-002.P03; BSR 211

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-JPG`: файл `questionnaire-valid.jpg`.

### Шаги

1. В поле `Анкета клиента` нажать кнопку добавления файла.
2. В открывшемся проводнике выбрать `questionnaire-valid.jpg`.

### Итоговый ожидаемый результат

Файл добавлен, отображается имя `questionnaire-valid.jpg`.

### Постусловия

- Не применимо.

## TC-QUT-005

**Название:** Добавление PDF-файла перетаскиванием с отображением имени
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-006; ATOM-006; SRC-QUT-002.P04; BSR 209; SRC-QUT-002; BSR 211

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-PDF`: файл `questionnaire-valid.pdf`.

### Шаги

1. Перетащить `questionnaire-valid.pdf` в поле `Анкета клиента`.

### Итоговый ожидаемый результат

Файл добавлен, отображается имя `questionnaire-valid.pdf`.

### Постусловия

- Не применимо.

## TC-QUT-006

**Название:** Добавление файлов допустимых форматов JPG, PNG и PDF
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-007; ATOM-007; SRC-QUT-002.P05; BSR 210; SRC-QUT-002

### Предусловия

1. Для каждой итерации открыта чистая заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-JPG`: JPG-файл.
- `FIXTURE-QUT-PNG`: PNG-файл.
- `FIXTURE-QUT-PDF`: PDF-файл.

### Шаги

1. В первой чистой итерации добавить в поле `Анкета клиента` `FIXTURE-QUT-JPG`.
2. Во второй чистой итерации добавить в поле `Анкета клиента` `FIXTURE-QUT-PNG`.
3. В третьей чистой итерации добавить в поле `Анкета клиента` `FIXTURE-QUT-PDF`.

### Итоговый ожидаемый результат

В каждой итерации выбранный файл допустимого формата добавляется.

### Постусловия

- Не применимо.

## TC-QUT-007

**Название:** Отклонение PDF-файла размером 50 МБ
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-009; ATOM-009; SRC-QUT-002.P07; BSR 210; SRC-QUT-002

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-PDF-OVER40`: PDF-файл размером 50 МБ.

### Шаги

1. Попытаться добавить в поле `Анкета клиента` `FIXTURE-QUT-PDF-OVER40`.

### Итоговый ожидаемый результат

Файл не добавляется; отображается текст `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.

### Постусловия

- Не применимо.

## TC-QUT-008

**Название:** Отклонение TXT-файла недопустимого формата
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-010; ATOM-010; SRC-QUT-002.P08; BSR 210; SRC-QUT-002

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-TXT`: TXT-файл.

### Шаги

1. Попытаться добавить в поле `Анкета клиента` `FIXTURE-QUT-TXT`.

### Итоговый ожидаемый результат

Файл не добавляется; отображается текст `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.

### Постусловия

- Не применимо.

## TC-QUT-009

**Название:** Ограничение количества файлов после попытки добавить второй PDF-файл
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v8-prod-candidate-r1
**Трассировка:** OBL-QUT-011; ATOM-011; SRC-QUT-002.P09; BSR 210; SRC-QUT-002

### Предусловия

1. Открыта заявка с блоком `Документы по заявке`.

### Тестовые данные

- `FIXTURE-QUT-PDF-A`: первый PDF-файл.
- `FIXTURE-QUT-PDF-B`: второй PDF-файл.

### Шаги

1. Добавить в поле `Анкета клиента` `FIXTURE-QUT-PDF-A`.
2. Попытаться добавить в то же поле `FIXTURE-QUT-PDF-B`.

### Итоговый ожидаемый результат

После второго действия отображается не более одного имени файла.

### Постусловия

- Не применимо.

## Coverage gaps

- `GAP-QUT-001`: OBL-QUT-008; ATOM-008; BSR 210; SRC-QUT-002.P06. Для ограничения `размер файла не более 40 МБ` не создан тест на точную границу или значение непосредственно выше границы: ФТ не определяет byte convention для единицы `МБ`.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
