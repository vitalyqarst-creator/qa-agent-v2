# Scope Coverage Gaps

## Контекст

- `scope_slug`: `application-card-personal-data-and-recognition`
- Основной FT: `source/PostFinal-v2.docx`
- Handoff: `work/stage-handoffs/06-application-card-personal-data-and-recognition/`

## Summary

- Найдено gaps: `8`
- Есть blocking gaps: `yes` (`GAP-001`-`GAP-003`)
- Writing можно стартовать: `no`, пока blocking gaps не закрыты, не приняты как residual risk или не исключены явным scope decision.
- Pre-writer gap review можно стартовать: `yes`

## Coverage Gaps

### GAP-001
**FT Reference:** `4.3 / Таблица 4 / row 15 / BSR 83 / recognition request and wait`
**Source Path:** `fts/AutoFin/PostFinal-v2/source/PostFinal-v2.xhtml /*/*[2]/*[116]/*[16]`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `BSR 83`: if files exist, the system sends a request to recognition, waits and fills application fields.
**Gap Type:** `missing-observation-interface`
**Description:** No authorized observable interface is defined for proving the recognition request, wait completion and service result.
**Impact:** `blocking`
**Coverage Impact:** `partial`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** No authorized observable interface is defined for proving the recognition request, wait completion and service result.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `integration`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `request log / visible status / callback artifact / filled-field evidence`
**Why Not Executable:** The source names an integration effect but does not define a tester-observable artifact.
**Downstream Do Not Test:** Do not assert that request was sent or wait completed without observable evidence.
**Risk:** `high`
**Blocks Ready For Review:** `yes`
**Question To Analyst:** Каким разрешённым способом тестировщик должен подтвердить запрос в систему распознавания, ожидание и завершение результата?
**Temporary Handling:** Cover popup opening/cancel/no-file warning; keep positive recognition integration branch blocked.
**Writer Rule:** Do not create executable TC for request/wait/fill unless an observable artifact is provided.
**Reviewer Rule:** Verify that BSR 83 remains blocking or is explicitly accepted/deferred; do not allow backend assumptions.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-002
**FT Reference:** `4.3 / Таблица 4 / row 15 / BSR 83 / `соответствующие поля Заявки``
**Source Path:** `fts/AutoFin/PostFinal-v2/source/PostFinal-v2.xhtml /*/*[2]/*[116]/*[16]`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `BSR 83`: recognition result fills corresponding application fields.
**Gap Type:** `missing-rule`
**Description:** Exact mapping from recognition result attributes to application fields is not defined.
**Impact:** `blocking`
**Coverage Impact:** `uncovered`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Exact mapping from recognition result attributes to application fields is not defined.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `integration`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `field mapping and success state`
**Why Not Executable:** There is no source-backed target field list or expected values.
**Downstream Do Not Test:** Do not test auto-fill of unspecified application fields.
**Risk:** `high`
**Blocks Ready For Review:** `yes`
**Question To Analyst:** Какие поля заявки должны заполняться после успешного распознавания и по каким видимым признакам тестировщик должен понять, что распознавание прошло успешно?
**Temporary Handling:** Do not verify field-filling after recognition; only retain it as open coverage.
**Writer Rule:** Do not invent field mapping from document type or mockup labels.
**Reviewer Rule:** Check that no downstream TC claims recognition-filled fields without source mapping.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-003
**FT Reference:** `4.3 / Таблица 4 / row 15 / BSR 79; BSR 82; BSR 83 / file attachment container`
**Source Path:** `fts/AutoFin/PostFinal-v2/source/PostFinal-v2.xhtml /*/*[2]/*[116]/*[16]`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `BSR 79`: container for files with drag & drop; `BSR 82`: no-file warning; `BSR 83`: if files exist, recognition starts.
**Gap Type:** `missing-constraint`
**Description:** Allowed file types, count, size and stable positive fixture for recognition are not defined.
**Impact:** `blocking`
**Coverage Impact:** `partial`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Allowed file types, count, size and stable positive fixture for recognition are not defined.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `file-upload`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `allowed file classes and valid fixture`
**Why Not Executable:** A stable positive file fixture cannot be derived from BSR 79-83.
**Downstream Do Not Test:** Do not test unsupported file classes or arbitrary successful recognition upload.
**Risk:** `medium`
**Blocks Ready For Review:** `yes`
**Question To Analyst:** Какие файлы можно использовать для успешного распознавания, включая формат, количество, максимальный размер и пример тестового файла?
**Temporary Handling:** Cover source-backed no-file warning; do not test invalid file type/size/count or positive recognition with arbitrary file.
**Writer Rule:** Use exact no-file warning only; block positive recognition file branch until fixture constraints are source-backed.
**Reviewer Rule:** Ensure writer does not choose arbitrary files or invent upload validation.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-004
**FT Reference:** `4.3 / Таблица 4 / BSR 49; 52; 55; 59; 69; 73; 77 / DaData`
**Source Path:** ``SRC-030`; `SRC-031`; `SRC-032`; `SRC-034`; `SRC-037`; `SRC-038`; `SRC-039``
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `CLR-005` confirms suggestion list appears on partial input when matching values exist in DaData.
**Gap Type:** `missing-rule`
**Description:** Selection effect, no-match behavior and DaData service error behavior are not defined.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Selection effect, no-match behavior and DaData service error behavior are not defined.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `integration`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `not_applicable`
**Why Not Executable:** not_applicable
**Downstream Do Not Test:** not_applicable
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** Что происходит после выбора подсказки, при отсутствии совпадений и при ошибке DaData?
**Temporary Handling:** Cover only display of suitable suggestions when values exist; exclude no-match/error/selection branches.
**Writer Rule:** Do not invent DaData fallback, error message, selection side effects or retry behavior.
**Reviewer Rule:** Check DaData branches are limited to approved `CLR-005` trigger/display behavior.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-005
**FT Reference:** `4.3 / Таблица 4 / validation and requiredness rows; `CLR-006`; `CLR-007``
**Source Path:** ``SRC-030`-`SRC-039`; requiredness/negative oracle inventories`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `CLR-006`: exact UI reaction must be clarified during UI research; `CLR-007`: spaces are forbidden.
**Gap Type:** `missing-rule`
**Description:** Exact UI rejection/requiredness mechanism is not source-backed for invalid or empty required values.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Exact UI rejection/requiredness mechanism is not source-backed for invalid or empty required values.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `expected-result`
**Scope Obligation ID(s):** `SO-NEG-001..SO-NEG-027; SO-REQ-001..SO-REQ-005`
**Blocked Negative Classes:** `digits; special-chars; spaces; too-long; younger-than-18; future-date; older-than-100; empty-required-field; condition-true-empty`
**Missing Observable Oracle:** `exact message / red highlight / blocked transition / input filtering / visible marker`
**Why Not Executable:** Candidate TC can be formed, but exact UI reaction is pending UI calibration.
**Downstream Do Not Test:** Do not create fully executable negative/requiredness TC without calibration evidence.
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** `none_required`: вопрос БА сейчас не требуется; `CLR-006` уже переносит точную реакцию UI на UI-калибровку.
**Temporary Handling:** Preserve all `SO-NEG-*` and `SO-REQ-*` rows as `candidate_tc_required` with `ui-calibration-required`.
**Writer Rule:** Create candidate UI-calibration TC; do not invent exact message/filtering/highlight/save block.
**Reviewer Rule:** Verify child obligations are not hidden inside this parent gap.
**Needs User Input:** `no`
**Status:** `open`

### GAP-006
**FT Reference:** `4.3 / Таблица 4 / BSR 58; BSR 79 / dictionaries `Пол клиента`, `типы документов``
**Source Path:** ``SRC-034`; `SRC-040`; `support/АФБ справочники 26.06.26.md`; `CLR-008``
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** `CLR-008` confirms no default; dictionary values are extracted from support.
**Gap Type:** `missing-rule`
**Description:** Closed-set/no-extra-values semantics are not confirmed for extracted dictionaries.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Closed-set/no-extra-values semantics are not confirmed for extracted dictionaries.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `table-list`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `not_applicable`
**Why Not Executable:** not_applicable
**Downstream Do Not Test:** not_applicable
**Risk:** `low`
**Blocks Ready For Review:** `no`
**Question To Analyst:** Можно ли в полях `Пол` и `Тип документа` выбрать только значения из справочников, или допускаются другие значения?
**Temporary Handling:** Use extracted active values and no-default semantics; do not assert absence of extra values.
**Writer Rule:** Reference `DICT-001`/`DICT-002`; do not write closed-set rejection checks.
**Reviewer Rule:** Verify dictionary inventory is used and closed-set claim is not invented.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-007
**FT Reference:** `4.3 / Таблица 4 / rows 2-3 / BSR 43-46 / external FT `Калькулятор``
**Source Path:** ``SRC-027`; `SRC-028``
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** Selected rows refer to requirements for `Кредитный калькулятор` in a separate FT.
**Gap Type:** `cross-ft-dependency`
**Description:** Calculator calculation/content behavior is outside the current source package.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Calculator calculation/content behavior is outside the current source package.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `scope`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `not_applicable`
**Why Not Executable:** not_applicable
**Downstream Do Not Test:** not_applicable
**Risk:** `low`
**Blocks Ready For Review:** `no`
**Question To Analyst:** `none_required`: вопрос БА не требуется, если требования к калькулятору не добавляются как источник текущего scope.
**Temporary Handling:** Cover only visible summary content listed in BSR 44 and local click/open actions BSR 45-46.
**Writer Rule:** Do not test calculator calculations, validations or internal window behavior.
**Reviewer Rule:** Check current scope does not import external calculator rules.
**Needs User Input:** `no`
**Status:** `open`

### GAP-008
**FT Reference:** `Section 3 / external widget document `Описание базовых возможностей интерфейсных виджетов FIS Platform``
**Source Path:** ``SRC-016``
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** Main FT says base widget behavior is described in external FIS Platform documentation.
**Gap Type:** `cross-ft-dependency`
**Description:** Generic widget capabilities are not available as a source in this run.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** Generic widget capabilities are not available as a source in this run.
**Why Expected Result Not Derivable:** Source does not state the missing behavior and no approved clarification resolves it.
**Affected Test-design Dimension:** `scope`
**Scope Obligation ID(s):** `not_applicable`
**Blocked Negative Classes:** `not_applicable`
**Missing Observable Oracle:** `not_applicable`
**Why Not Executable:** not_applicable
**Downstream Do Not Test:** not_applicable
**Risk:** `low`
**Blocks Ready For Review:** `no`
**Question To Analyst:** `none_required`: вопрос БА не требуется, если спецификация виджетов не добавляется как источник текущего scope.
**Temporary Handling:** Use only local BSR behavior and mockup interaction hints.
**Writer Rule:** Do not test generic widget behavior not restated in BSR 43-83.
**Reviewer Rule:** Check writer does not import external widget rules by assumption.
**Needs User Input:** `no`
**Status:** `open`

## Что Можно Покрывать Несмотря На Gaps

- Field visibility/editability/default/requiredness source-backed obligations for BSR 43-82, with candidate UI calibration where exact UI reaction is absent.
- No-file warning for `BSR 82` with exact text `Отсутствуют файлы для распознавания`.
- Dictionary active values from `DICT-001`/`DICT-002` and absence of default per `CLR-008`.
- DaData suggestion display only under `CLR-005` condition: matching values exist and partial input is entered.

## Что Нельзя Домысливать

- Recognition request logs, waiting state, field mapping, successful filling and backend effects.
- Allowed file types/count/size and invalid upload behavior.
- DaData no-match/error/selection side effects.
- Exact validation/requiredness message, color, filtering, clearing, blocked transition or save/no-save effect.
- Closed-set/no-extra-values semantics for dictionaries.
- External calculator or generic widget behavior.

## Требуемые Уточнения

- See `scope-clarification-requests.md` for open questions linked to `GAP-001`-`GAP-004` and `GAP-006`.
