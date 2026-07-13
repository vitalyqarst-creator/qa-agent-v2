# Traceability Gate Finding

## Finding

- ID: `FIND-COND-TRACE-001`.
- Severity: `blocking`.
- Runner state: `accepted-not-promoted`.
- Release state: `blocked`.
- Draft SHA-256: `9e5d26946afa948b176041428f7c7d0028ba8ed9950db4a45bffc06ba265028a`.

Каждый testable obligation содержит source refs, однако соответствующий TC сохраняет только `OBL-*` и `ATOM-*`. Это нарушает обязательную трассировку BSR/source property и делает reviewer acceptance недостаточным для controlled rollout.

## Missing refs

| test_case_id | obligation | обязательные отсутствующие refs |
| --- | --- | --- |
| `TC-VACS-001` | `OBL-COND-001` | `SRC-002.P02`; `BSR 312` |
| `TC-VACS-002` | `OBL-COND-002` | `SRC-003.P01`; `BSR 314` |
| `TC-VACS-003` | `OBL-COND-003` | `SRC-003.P02`; `BSR 314` |
| `TC-VACS-004` | `OBL-COND-004` | `SRC-003.P06`; `SRC-009`; `BSR 317`; `DICT-101` |
| `TC-VACS-005` | `OBL-COND-005` | `SRC-002.P04`; `SRC-003.P08`; `SRC-005`; `SRC-006`; `BSR 313`; `BSR 315`; `DICT-101` |

## Root cause boundary

- Structured seed гарантирует только `OBL-*` и `ATOM-*`.
- Writer contract допускает не вернуть source refs.
- `prepared-package-obligation-gate-v2`, quality bundle и reviewer contract проверяют obligation/atom coverage, но не требуют полного множества `source_refs` каждого testable obligation в соответствующем TC.
- Поэтому три независимых формальных gate дали false acceptance.

## Required remediation

1. Добавить deterministic source-ref preservation check для каждого testable obligation.
2. Gate должен проверять соответствующий TC, а не наличие ref где-либо в draft.
3. Обязательны `SRC-*`, буквенно-цифровые requirement codes и `DICT-*`, перечисленные в obligation `source_refs`/`dictionary_refs`.
4. Добавить regression tests: missing one ref, ref in wrong TC, duplicate/grouped obligation, gap-obligation without TC.
5. После тестов скомпилировать новый immutable V2 и выполнить ровно один повторный conditional live canary.
