---
name: ft-practical-route
description: Compact default route for producing source-traceable, executable test cases from one confirmed FT scope.
---

# Compact practical route v0.9

Use this skill for a normal request to write test cases from a selected FT scope. It replaces v0.8 as the default. Use v0.8 only to resume an already existing v0.8 run or when the user explicitly requests it.

Read [../../references/agent/practical-test-case-route-v0.9.md](../../references/agent/practical-test-case-route-v0.9.md) and the matching format reference before work.

## Входы

Подтверждённый scope ФТ, DOCX, XHTML, support, `AGENT-NOTES.md`, visual references и PDF, если он доступен для structural/visual cross-check.

## Выходы

Только канонические артефакты v0.9, перечисленные в маршруте: пакетный source manifest, обязательства scope, conditional вопросы к БА, matrix, TC и независимые review-артефакты при требуемых переходах.

## Ограничения

Не заменяет UI-калибровку; не создаёт фиктивный review или `accepted`; подробные контракты остаются в canonical reference.

## Route

1. Resolve DOCX, XHTML, support, existing `AGENT-NOTES.md`, visual references and an available PDF. Create `source-package-manifest.json`.
2. Create `scope-obligations.json` with one source-backed `OBL-*` per independent assertion. Record every gap in `clarifications`; if a business answer is required, create the linked `scope-clarification-requests.md` in the same run. Do not create TC yet.
3. Create `workflow-state.json`, then write one Russian `test-design-matrix.md`.
4. Run `validate_practical_scope.py` exactly once for the frozen stage.
5. Run independent matrix review only when the deterministic v0.9 complexity rule requires it.
6. Write canonical TC after accepted/skipped matrix review; run one fresh scoped validation.
7. Run final independent TC review in a separate top-level Codex session. One targeted revision plus one fresh final review is the maximum.

## Do not create

- writer self-check, TC self-check, WQG, stage summary, dispatch/preflight receipts, parking prompts, duplicated coverage ledgers or full-route artifacts;
- benchmark, sharding, semantic bridge, source assertion review or iterative repair loops;
- a TC before the current matrix has passed native validation.

## Quality rules

- TC, matrix and source obligations use Russian in user-facing text.
- One OBL, one matrix row, one TC, one primary expected result.
- A finite list is not automatically one TC: split items that trigger distinct transitions or results; keep one TC only for a same-action, same-logic composition/value check.
- Missing UI/data/observability is an execution status, not invented behavior or a blocker unless the source assertion itself cannot be represented. Use `candidate-ui-calibration`, `needs-test-data` or `blocked-observability` as applicable. A source contradiction is a blocker and no TC may be invented for it.
- Compare the selected section heading with nearby tables and source assertions. Record a terminology discrepancy as a gap; ground the working scope subject in the content, not a contradictory heading.
- Before `workflow-state.json`, call the stdout-only `validate_practical_obligations.py` and call its result only an obligations-structure check. Call `validate_practical_scope.py` only after the workflow state and matrix exist.
- A confirmed BA answer is not free prose: bind its support file and SHA-256 in the linked GAP, resolve only its linked GAP/OBL and update only affected downstream matrix/TC artifacts. Do not mutate the package-wide source manifest for a scope-local answer.
- Figma/mockups clarify visible UI only and never override DOCX.
- Do not add a generic form-isolation test because a create form exists. Add it only when a source obligation explicitly requires isolation, preservation, reset or non-leakage of values.

## Independent review

The reviewer is a separate top-level `codex-thread`, read-only for reviewed matrix/TC. Give it only the immutable review manifest, source inputs, scope obligations, matrix/TC and review format. It must independently reconstruct obligations before comparing author artefacts. A subagent does not satisfy this requirement.
