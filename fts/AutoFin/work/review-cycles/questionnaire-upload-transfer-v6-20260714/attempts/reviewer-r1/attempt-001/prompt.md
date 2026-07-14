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
  "package_id": "questionnaire-upload-transfer-v6-r1",
  "package_digest": "c0a6cb07676ca3d7ae3617289dcf4712f100c3ca510a0b4732e58a9b961cb32d",
  "input_fingerprint": "f60a5bdf97689cfdcd87860c0c7b55f9199663886cf83ee201c5f3f6b2a13b2c",
  "ft_slug": "AutoFin",
  "scope_slug": "questionnaire-upload-transfer-v6",
  "section_id": "16",
  "execution_profile": "standard-required",
  "context_profile": "character-restriction-calibration",
  "unsupported_dimensions": [
    "file-upload",
    "input-boundaries",
    "negative-oracle",
    "visibility"
  ],
  "reviewed_draft_sha256": "ecb656d276b4bc76981990aa1ab9e4b8d45f094977e8d313587666488283a31e"
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

- package_id: `questionnaire-upload-transfer-v6-r1`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v6-20260714/prepared-input/.questionnaire-upload-transfer-v6-r1.compiled-evidence.md`
- source_sha256: `b66f2b0ddf191d47e80b47bc9e9b347a1abfa9bde875c413164fdfbe44826b89`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## Mandatory package context

source_path: fts/AutoFin/AGENT-NOTES.md

# Package Notes: AutoFin

## Сокращения В Таблицах UI-Полей

Статус: package-specific рабочее правило для AutoFin, добавленное по подтверждению пользователя и сверенное с аналогичными заметками в `fts/ft-2-OF_16/AGENT-NOTES.md`, `fts/ft-2-OF_17/AGENT-NOTES.md`, `fts/ft-2-OF_18/AGENT-NOTES.md`.

В таблицах описания свойств полей формы столбец `О` означает `Обязательность`, а столбец `Р` означает `Редактируемость`.

<!-- DaData package notes: not applicable to selected scope. -->

## Verified obligation review index

The immutable full obligations artifact is identified by digest below. This compact projection contains every exact review-contract ID plus its source-backed statement, oracle, intent, reference and gap; the runner validates the final contract against the immutable artifact.

```json
{"artifact":"fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v6-20260714/prepared-input/questionnaire-upload-transfer-v6-r1/atomic-obligations.json","artifact_sha256":"b2e92672e1a528e2bb7597375390dbdf228746540af6dde48b219afd35d4639d","obligation_count":11,"semantic_evidence_source":"selected-source-evidence","coverage_gaps":[],"dictionary_evidence":[],"obligations":[{"obligation_id":"OBL-QUT-001","atom_id":"ATOM-001","coverage_status":"testable","planned_test_case_id":"TC-QUT-001","source_refs":["SRC-QUT-001.P01","BSR 206","SRC-QUT-001"],"atomic_statement":"Информационное поле отображается всегда.","observable_oracle":"Информационное поле отображается всегда.","test_intent":"Открыть блок `Документы по заявке`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-002","atom_id":"ATOM-002","coverage_status":"testable","planned_test_case_id":"TC-QUT-002","source_refs":["SRC-QUT-001.P02","BSR 207","SRC-QUT-001"],"atomic_statement":"Информационное поле не допускает ручного редактирования своего текста.","observable_oracle":"Текст информационного поля нельзя изменить ручным вводом.","test_intent":"Установить фокус на информационном поле и попытаться ввести `Тест`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-003","atom_id":"ATOM-003","coverage_status":"testable","planned_test_case_id":"TC-QUT-003","source_refs":["SRC-QUT-002.P01","BSR 208","SRC-QUT-002"],"atomic_statement":"Поле добавления файла `Анкета клиента` отображается всегда.","observable_oracle":"Поле добавления файла Анкета клиента отображается всегда.","test_intent":"Открыть блок `Документы по заявке`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-004","atom_id":"ATOM-004","coverage_status":"testable","planned_test_case_id":"TC-QUT-004","source_refs":["SRC-QUT-002.P02","BSR 209","SRC-QUT-002"],"atomic_statement":"Документ можно добавить через открытие проводника по кнопке.","observable_oracle":"После выбора portable jpg через проводник файл добавлен.","test_intent":"По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-005","atom_id":"ATOM-005","coverage_status":"testable","planned_test_case_id":"TC-QUT-004","source_refs":["SRC-QUT-002.P03","BSR 211","SRC-QUT-002"],"atomic_statement":"После добавления документа отображается имя прикреплённого файла.","observable_oracle":"После добавления отображается точное имя выбранного файла.","test_intent":"По кнопке открыть проводник и выбрать `FIXTURE-QUT-JPG`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-006","atom_id":"ATOM-006","coverage_status":"testable","planned_test_case_id":"TC-QUT-005","source_refs":["SRC-QUT-002.P04","BSR 209","SRC-QUT-002","BSR 211"],"atomic_statement":"Документ можно добавить через Drag and Drop.","observable_oracle":"После Drag and Drop portable pdf файл добавлен и его имя отображается.","test_intent":"Перетащить `FIXTURE-QUT-PDF` в поле `Анкета клиента`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-007","atom_id":"ATOM-007","coverage_status":"testable","planned_test_case_id":"TC-QUT-006","source_refs":["SRC-QUT-002.P05","BSR 210","SRC-QUT-002"],"atomic_statement":"Поле принимает файлы форматов jpg, png и pdf.","observable_oracle":"В отдельных чистых итерациях jpg, png и pdf добавляются успешно.","test_intent":"В трёх независимых чистых итерациях добавить через проводник `FIXTURE-QUT-JPG`, `FIXTURE-QUT-PNG`, `FIXTURE-QUT-PDF`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-008","atom_id":"ATOM-008","coverage_status":"testable","planned_test_case_id":"TC-QUT-007","source_refs":["SRC-QUT-002.P06","BSR 210","SRC-QUT-002"],"atomic_statement":"Файл размером ровно 40 МБ соответствует ограничению `не более 40 МБ`.","observable_oracle":"Файл ровно 41 943 040 байт добавляется успешно.","test_intent":"Добавить через проводник `FIXTURE-QUT-PDF-40MB`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-009","atom_id":"ATOM-009","coverage_status":"testable","planned_test_case_id":"TC-QUT-008","source_refs":["SRC-QUT-002.P07","BSR 210","SRC-QUT-002"],"atomic_statement":"Файл больше 40 МБ не загружается, отображается точный текст ошибки из ФТ.","observable_oracle":"Файл 41 943 041 байт не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.","test_intent":"Добавить через проводник `FIXTURE-QUT-PDF-OVER40`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-010","atom_id":"ATOM-010","coverage_status":"testable","planned_test_case_id":"TC-QUT-009","source_refs":["SRC-QUT-002.P08","BSR 210","SRC-QUT-002"],"atomic_statement":"Файл недопустимого формата не загружается, отображается точный текст ошибки из ФТ.","observable_oracle":"Файл txt не добавляется; отображается `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.","test_intent":"Добавить через проводник `FIXTURE-QUT-TXT`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]},{"obligation_id":"OBL-QUT-011","atom_id":"ATOM-011","coverage_status":"testable","planned_test_case_id":"TC-QUT-010","source_refs":["SRC-QUT-002.P09","BSR 210","SRC-QUT-002"],"atomic_statement":"После попытки добавить второй файл в типе документа остаётся не более одного файла.","observable_oracle":"После попытки добавить второй файл отображается не более одного имени файла этого типа.","test_intent":"Добавить `FIXTURE-QUT-PDF-A`, затем через тот же picker попытаться добавить `FIXTURE-QUT-PDF-B`.","execution_semantics":"direct","state_change":null,"dictionary_refs":[],"gap_id":"","constraint_gap_ids":[]}]}
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
    "test_case_count": 10,
    "testable_obligations": 11,
    "covered_obligations": [
      "OBL-QUT-001",
      "OBL-QUT-002",
      "OBL-QUT-003",
      "OBL-QUT-004",
      "OBL-QUT-005",
      "OBL-QUT-006",
      "OBL-QUT-007",
      "OBL-QUT-008",
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
    "test_case_count": 10
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
    "test_case_count": 10
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
  "test_case_count": 10,
  "findings": [],
  "checked_paths": [
    "C:\\Users\\Пользователь\\Documents\\Виталя\\GitProjects\\qa-agent-v2\\fts\\AutoFin\\work\\review-cycles\\questionnaire-upload-transfer-v6-20260714\\attempts\\writer-r1\\attempt-001\\stage-output\\draft.md"
  ]
}
```

## Calibration lifecycle summary

```json
{"artifact":"fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v6-20260714/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json","artifact_sha256":"29bb0927b8f662349b07b14496c2f973be30aa88a4b5948a075f039a76b5126a","context_profile":"character-restriction-calibration","open_count":0,"resolved_count":0,"status_counts":{},"constraint_gap_ids":[],"per_obligation_mapping_source":"verified-obligation-review-index"}
```

## Immutable writer draft

```markdown
# Тест-кейсы

## TC-QUT-001

**Название:** Отображение информационного поля в блоке «Документы по заявке»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-001; ATOM-001; SRC-QUT-001.P01; BSR 206; SRC-QUT-001

### Предусловия

1. Открыт блок «Документы по заявке».

### Тестовые данные

- Не требуются.

### Шаги

1. Просмотреть блок «Документы по заявке».

### Итоговый ожидаемый результат

Информационное поле отображается.

### Постусловия

- Не требуются.

## TC-QUT-002

**Название:** Запрет ручного изменения текста информационного поля
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-002; ATOM-002; SRC-QUT-001.P02; BSR 207; SRC-QUT-001

### Предусловия

1. Открыт блок «Документы по заявке» с отображаемым информационным полем.

### Тестовые данные

- Текст для ввода: `Тест`.

### Шаги

1. Установить фокус на информационном поле.
2. Попытаться ввести текст `Тест`.

### Итоговый ожидаемый результат

Текст информационного поля не изменяется.

### Постусловия

- Не требуются.

## TC-QUT-003

**Название:** Отображение поля добавления файла «Анкета клиента»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-003; ATOM-003; SRC-QUT-002.P01; BSR 208; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».

### Тестовые данные

- Не требуются.

### Шаги

1. Просмотреть блок «Документы по заявке».

### Итоговый ожидаемый результат

Поле добавления файла «Анкета клиента» отображается.

### Постусловия

- Не требуются.

## TC-QUT-004

**Название:** Добавление JPG через проводник с отображением имени файла
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-004; ATOM-004; SRC-QUT-002.P02; BSR 209; SRC-QUT-002; OBL-QUT-005; ATOM-005; SRC-QUT-002.P03; BSR 211

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-JPG`: файл `questionnaire-valid.jpg` допустимого формата JPG.

### Шаги

1. В поле «Анкета клиента» нажать кнопку добавления файла.
2. В открывшемся проводнике выбрать `FIXTURE-QUT-JPG`.

### Итоговый ожидаемый результат

Файл добавлен; отображается имя `questionnaire-valid.jpg`.

### Постусловия

- Не требуются.

## TC-QUT-005

**Название:** Добавление PDF перетаскиванием с отображением имени файла
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-006; ATOM-006; SRC-QUT-002.P04; BSR 209; SRC-QUT-002; BSR 211

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-PDF`: файл `questionnaire-valid.pdf` допустимого формата PDF.

### Шаги

1. Перетащить `FIXTURE-QUT-PDF` в поле «Анкета клиента».

### Итоговый ожидаемый результат

Файл добавлен; отображается имя `questionnaire-valid.pdf`.

### Постусловия

- Не требуются.

## TC-QUT-006

**Название:** Добавление файлов форматов JPG, PNG и PDF
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-007; ATOM-007; SRC-QUT-002.P05; BSR 210; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».

### Тестовые данные

- `FIXTURE-QUT-JPG`: допустимый файл формата JPG.
- `FIXTURE-QUT-PNG`: допустимый файл формата PNG.
- `FIXTURE-QUT-PDF`: допустимый файл формата PDF.

### Шаги

1. В чистой итерации добавить через проводник `FIXTURE-QUT-JPG` в поле «Анкета клиента».
2. В отдельной чистой итерации добавить через проводник `FIXTURE-QUT-PNG` в поле «Анкета клиента».
3. В отдельной чистой итерации добавить через проводник `FIXTURE-QUT-PDF` в поле «Анкета клиента».

### Итоговый ожидаемый результат

В каждой из трёх чистых итераций выбранный файл добавляется.

### Постусловия

- Не требуются.

## TC-QUT-007

**Название:** Добавление файла размером ровно 40 МБ
**Тип:** позитивный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-008; ATOM-008; SRC-QUT-002.P06; BSR 210; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-PDF-40MB`: файл PDF размером ровно 41 943 040 байт.

### Шаги

1. Добавить через проводник `FIXTURE-QUT-PDF-40MB` в поле «Анкета клиента».

### Итоговый ожидаемый результат

Файл размером ровно 41 943 040 байт добавляется.

### Постусловия

- Не требуются.

## TC-QUT-008

**Название:** Отклонение файла размером более 40 МБ
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-009; ATOM-009; SRC-QUT-002.P07; BSR 210; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-PDF-OVER40`: файл PDF размером 41 943 041 байт.

### Шаги

1. Добавить через проводник `FIXTURE-QUT-PDF-OVER40` в поле «Анкета клиента».

### Итоговый ожидаемый результат

Файл не добавляется; отображается текст: `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.

### Постусловия

- Не требуются.

## TC-QUT-009

**Название:** Отклонение файла недопустимого формата TXT
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-010; ATOM-010; SRC-QUT-002.P08; BSR 210; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-TXT`: файл недопустимого формата TXT.

### Шаги

1. Добавить через проводник `FIXTURE-QUT-TXT` в поле «Анкета клиента».

### Итоговый ожидаемый результат

Файл не добавляется; отображается текст: `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.

### Постусловия

- Не требуются.

## TC-QUT-010

**Название:** Ограничение количества файлов в поле «Анкета клиента»
**Тип:** негативный
**Приоритет:** средний
**package_id:** questionnaire-upload-transfer-v6-r1
**Трассировка:** OBL-QUT-011; ATOM-011; SRC-QUT-002.P09; BSR 210; SRC-QUT-002

### Предусловия

1. Открыт блок «Документы по заявке».
2. Поле добавления файла «Анкета клиента» не содержит добавленного файла.

### Тестовые данные

- `FIXTURE-QUT-PDF-A`: допустимый файл формата PDF.
- `FIXTURE-QUT-PDF-B`: другой допустимый файл формата PDF.

### Шаги

1. Добавить `FIXTURE-QUT-PDF-A` в поле «Анкета клиента».
2. Через тот же выбор файла попытаться добавить `FIXTURE-QUT-PDF-B` в поле «Анкета клиента».

### Итоговый ожидаемый результат

После второго действия в поле отображается не более одного имени файла.

### Постусловия

- Не требуются.
```

## Required final contract

Return contract_version 2, the exact reviewed_draft_sha256, one obligation_reviews item for every supplied obligation with its exact obligation_id and atom_id, structured findings and a non-empty summary. Classify every semantic-overlap group: accept only when the shared body is justified as one observable multi-obligation check; otherwise require consolidation with a duplication finding. Use only schema enum values. Do not emit commentary outside the final JSON object.
Dictionary evidence in the verified obligation projection is authoritative. Before claiming that a DICT-* value is absent, compare it with the exact active_values array supplied there.
<!-- PREPARED-REVIEW-PAYLOAD:END -->
