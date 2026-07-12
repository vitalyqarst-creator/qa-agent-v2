# Coverage Gaps

### GAP-001
**FT Reference:** Table 4; `BSR 48, 51, 54`.
**Source Path:** `SRC-002..SRC-004`.
**Related Atomic Statement(s):** `ATOM-003; ATOM-004; ATOM-007; ATOM-008; ATOM-011; ATOM-012`.
**Source Statement:** FT разрешает только текстовые символы и специальный символ `-`.
**Gap Type:** `missing-rule`.
**Description:** Exact observable UI reaction на invalid value не определена.
**Impact:** `non-blocking`.
**Coverage Impact:** `partial`.
**Affected Atom ID:** `ATOM-003; ATOM-004; ATOM-007; ATOM-008; ATOM-011; ATOM-012`.
**Missing Behavior:** message/highlight/filtering/blocked save or transition.
**Why Expected Result Not Derivable:** FT задаёт restriction, но не механизм реакции.
**Affected Test-design Dimension:** `expected-result`.
**Scope Obligation ID(s):** `OBL-003; OBL-004; OBL-007; OBL-008; OBL-011; OBL-012`.
**Blocked Negative Classes:** `digits; special-chars`.
**Missing Observable Oracle:** exact validation trigger and reaction.
**Why Not Executable:** нельзя выбрать один regression oracle без UI evidence.
**Downstream Do Not Test:** не применять; obligations должны остаться calibration candidates.
**Risk:** `medium`.
**Blocks Ready For Review:** `no`.
**Question To Analyst:** Как UI отклоняет цифру и специальный символ для каждого поля?
**Temporary Handling:** создать отдельные candidate TC и фиксировать фактическую UI-реакцию при UI calibration.
**Writer Rule:** не объединять invalid classes и не выдумывать сообщение, подсветку, фильтрацию или блокировку.
**Reviewer Rule:** не принимать invented exact reaction и не терять candidates.
**Needs User Input:** `no`.
**Status:** `open`.
