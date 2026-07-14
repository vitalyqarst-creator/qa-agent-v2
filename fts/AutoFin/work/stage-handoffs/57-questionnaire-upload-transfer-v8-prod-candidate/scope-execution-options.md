# Scope Execution Options — Questionnaire Upload Transfer V8 Prod Candidate

## Recommended

- Повторить независимый `scope_gap_review` на исправленном routing contract.
- При verdict `passed` с `GAP-QUT-001 = open-non-blocking` создать immutable prepared package и перейти в `ft-test-case-iteration` с promotion off.

## Allowed After Passed Gap Review

- compile и validate-only нового package;
- один exec-only writer и один fresh exec-only reviewer;
- сохранение unsigned draft и deterministic/reviewer evidence в новом cycle;
- ручной quality gate и promotion dry-run.

## Forbidden

- exact byte fixture без source-backed policy;
- SDK fallback, retry/resume failed cycle или ручная правка draft;
- promotion до reviewer acceptance, quality gate и явного human approval;
- использование V6/V7 test cases как requirement evidence.
