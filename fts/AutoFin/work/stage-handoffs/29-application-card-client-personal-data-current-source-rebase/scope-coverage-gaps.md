# Пробелы покрытия scope

## Контекст

- `scope_slug`: `application-card-client-personal-data`.
- Основной FT: `source/FT4AutoFinFinal.docx`.
- XHTML rows: `56–66`; BSR `47–77`.

## Summary

- Найдено gaps: `3`.
- Есть blocking gaps: `no`.
- Writing можно стартовать: `yes`, после `scope_gap_review`.

## Coverage Gaps

### GAP-001
**FT Reference:** Table 4; `BSR 48, 51, 54, 61–63, 67, 71, 75`.
**Source Path:** `SRC-002..SRC-004; SRC-007; SRC-009..SRC-011`.
**Related Atomic Statement(s):** `not-yet-assigned`.
**Source Statement:** FT ограничивает допустимые символы и диапазон даты рождения.
**Gap Type:** `missing-rule`.
**Description:** Exact observable UI reaction на invalid value не определена.
**Impact:** `non-blocking`.
**Coverage Impact:** `partial`.
**Affected Atom ID:** `not-yet-assigned`.
**Missing Behavior:** message/highlight/filtering/blocked save or transition.
**Why Expected Result Not Derivable:** FT задаёт restriction, но не механизм реакции.
**Affected Test-design Dimension:** `expected-result`.
**Scope Obligation ID(s):** `SO-NEG-001..SO-NEG-015`.
**Blocked Negative Classes:** `digits; special-chars; under-18; future-date; older-than-100`.
**Missing Observable Oracle:** exact validation trigger and reaction.
**Why Not Executable:** нельзя выбрать один regression oracle без UI evidence.
**Downstream Do Not Test:** не применять; obligations должны стать calibration candidates.
**Risk:** `medium`.
**Blocks Ready For Review:** `no`.
**Question To Analyst:** Как UI отклоняет каждый invalid class?
**Temporary Handling:** создать отдельные candidate TC для UI calibration и positive boundary acceptance cases.
**Writer Rule:** сохранить все `SO-NEG-*`, не объединять invalid classes.
**Reviewer Rule:** не принимать invented exact reaction и не терять candidates.
**Needs User Input:** `no`.
**Status:** `open`.

### GAP-002
**FT Reference:** Table 4 column `О`; `BSR 68, 72, 76`.
**Source Path:** `SRC-002; SRC-003; SRC-006; SRC-007; SRC-009..SRC-011`.
**Related Atomic Statement(s):** `not-yet-assigned`.
**Source Statement:** Four fields are always required; at least one previous-FIO field is required when changed-FIO=`Да`.
**Gap Type:** `missing-rule`.
**Description:** Empty-value UI oracle and marker semantics are not specified.
**Impact:** `non-blocking`.
**Coverage Impact:** `partial`.
**Affected Atom ID:** `not-yet-assigned`.
**Missing Behavior:** visible marker/message/highlight/blocked save or transition.
**Why Expected Result Not Derivable:** requiredness exists, reaction does not.
**Affected Test-design Dimension:** `expected-result`.
**Scope Obligation ID(s):** `SO-REQ-001..SO-REQ-005`.
**Blocked Negative Classes:** `empty-required-field; condition-true-empty`.
**Missing Observable Oracle:** exact empty-value reaction.
**Why Not Executable:** source-backed regression oracle absent.
**Downstream Do Not Test:** не применять; create calibration candidates.
**Risk:** `high`.
**Blocks Ready For Review:** `no`.
**Question To Analyst:** Как UI сообщает и блокирует незаполненную обязательность?
**Temporary Handling:** separate calibration candidates; positive filled-value tests do not close requiredness.
**Writer Rule:** map every `SO-REQ-*` to candidate TC.
**Reviewer Rule:** reject coverage through valid values only.
**Needs User Input:** `no`.
**Status:** `open`.

### GAP-003
**FT Reference:** `BSR 57`; `BSR 59`; DaData clauses in `BSR 49, 52, 55, 69, 73, 77`.
**Source Path:** `SRC-002..SRC-006; SRC-009..SRC-011`.
**Related Atomic Statement(s):** `not-yet-assigned`.
**Source Statement:** ID заполняется из ABS после сохранения; поля допускают DaData suggestions; пол обновляется после выбора ФИО через DaData.
**Gap Type:** `missing-rule`.
**Description:** Failure/retry/fallback и доказательство backend attribution не определены.
**Impact:** `non-blocking`.
**Coverage Impact:** `design-constraint-on-covered-atom`.
**Affected Atom ID:** `not-yet-assigned`.
**Missing Behavior:** integration failure paths and technical evidence.
**Why Expected Result Not Derivable:** FT задаёт success effect, но не failures; UI result alone does not prove provider.
**Affected Test-design Dimension:** `integration`.
**Scope Obligation ID(s):** `not_applicable`.
**Blocked Negative Classes:** `not_applicable`.
**Missing Observable Oracle:** integration log/API artifact for attribution.
**Why Not Executable:** internal cause cannot be asserted through UI only.
**Downstream Do Not Test:** retry/fallback/errors and technical provider attribution without artifact.
**Risk:** `medium`.
**Blocks Ready For Review:** `no`.
**Question To Analyst:** Нужны ли integration failure cases и какой artifact их подтверждает?
**Temporary Handling:** cover UI-visible success effects and label technical attribution as unverified without evidence.
**Writer Rule:** keep success-path and internal attribution separate.
**Reviewer Rule:** reject unsupported backend assertions.
**Needs User Input:** `no`.
**Status:** `open`.

## Что Можно Покрывать Несмотря На Gaps

- Visibility, field type, editability, allowed values and positive valid inputs.
- Exact accepted date boundaries `today-18y` and `today-100y`.
- Conditional visibility and group applicability for previous FIO.
- UI-visible successful ID fill and gender update with explicit evidence limitation.
- All candidate negative/requiredness scenarios for later UI calibration.

## Что Нельзя Домысливать

- Exact validation messages/reactions.
- DaData/ABS retry, fallback, errors, payloads or backend attribution without artifact.
- Mockup sample values as required data.

## Требуемые Уточнения

- Non-blocking questions are recorded in `scope-clarification-requests.md`; writer may proceed through calibration candidates.
