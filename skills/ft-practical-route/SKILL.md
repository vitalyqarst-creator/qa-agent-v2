---
name: ft-practical-route
description: Compact default route for producing source-traceable, executable test cases from one confirmed FT scope.
---

# Compact practical route v0.9

Use this skill for a normal request to write test cases from a selected FT scope. It replaces v0.8 as the default. Use v0.8 only to resume an already existing v0.8 run or when the user explicitly requests it.

Read [../../references/agent/practical-test-case-route-v0.9.md](../../references/agent/practical-test-case-route-v0.9.md) and the matching format reference before work.

## Входы

Подтверждённый scope ФТ, DOCX, XHTML, support, package-level утверждённые решения БА, `AGENT-NOTES.md`, visual references и PDF, если он доступен для structural/visual cross-check.

## Выходы

Только канонические артефакты v0.9, перечисленные в маршруте: пакетный source manifest, обязательства scope, conditional вопросы к БА, matrix, TC и независимые review-артефакты при требуемых переходах.

## Ограничения

Не заменяет UI-калибровку; не создаёт фиктивный review или `accepted`; подробные контракты остаются в canonical reference.

## Route

1. Resolve DOCX, XHTML, stable support, existing package-level approved BA decision registry, `AGENT-NOTES.md`, visual references and an available PDF. Create `source-package-manifest.json`: support, BA decisions и visual-only inputs регистрируй раздельно.
2. Create `scope-obligations.json` with one source-backed `OBL-*` per independent assertion, explicit `CTX-*` execution contexts and one shared `SETUP-*` prerequisite catalog. Record every gap in `clarifications`; if a business answer is required, create the linked `scope-clarification-requests.md` in the same run. Do not create TC yet.
3. Create `workflow-state.json`, then write one Russian `test-design-matrix.md`.
4. Run `validate_practical_scope.py` exactly once for the frozen stage. After any permitted revision, run it again for the new frozen inputs before the next review manifest.
5. Run independent matrix review only when the deterministic v0.9 complexity rule requires it.
6. Write canonical TC after accepted/skipped matrix review; run one fresh scoped validation; then set `phase: review`, `final_verdict: not-finalized` and next action to the independent final TC review.
7. Run final independent TC review in a separate top-level Codex session. One targeted revision plus one fresh final review is the maximum.

## Do not create

- writer self-check, TC self-check, WQG, stage summary, dispatch/preflight receipts, parking prompts, duplicated coverage ledgers or full-route artifacts;
- benchmark, sharding, semantic bridge, source assertion review or iterative repair loops;
- a TC before the current matrix has passed native validation.

## Quality rules

- TC, matrix and source obligations use Russian in user-facing text.
- One OBL/CTX pair, one matrix row, one TC, one primary expected result. Different create/edit or other user flows are separate CTX and separate TC.
- Test data are concrete values/files or precise properties plus a preparation method; never restate the checked rule as data. Put every action that creates the assertion's trigger state in its own numbered step. For a one-file limit, attach the first allowed file before attempting the second.
- Preserve source modifiers in OBL and review reconstruction: execution contexts, quantifiers, boundaries, conditions and exceptions. Split them if they create distinct flows or results.
- A finite list is not automatically one TC: split items that trigger distinct transitions or results; keep one TC only for a same-action, same-logic composition/value check.
- Missing UI/data/observability is an execution status, not invented behavior or a blocker unless the source assertion itself cannot be represented. Derive it from all linked SETUP prerequisites; a missing actor, fixture, integration or initial state makes `ready` invalid. Apply the primary-status order defined in the canonical route reference: `needs-test-data` never becomes only `candidate-ui-calibration`. `blocked-observability` is not an external blocker by itself. A source contradiction is a blocker and no TC may be invented for it.
- Compare the selected section heading with nearby tables and source assertions. Record a terminology discrepancy as a gap; ground the working scope subject in the content, not a contradictory heading.
- Before `workflow-state.json`, call the stdout-only `validate_practical_obligations.py` and call its result only an obligations-structure check. Call `validate_practical_scope.py` only after the workflow state and matrix exist.
- Обычный подтверждённый scope-local ответ БА связывай с GAP и SHA-256. Решение БА, прямо отменяющее или изменяющее ФТ, регистрируй package-level по `practical-v0.9-ba-decision-registry-format.md`: оно имеет приоритет только в явно указанной области действия, исключает связанные OBL из matrix/TC и делает затронутые scope stale. При противоречии без готового решения обязательно создай CLR-вопрос в том же запуске.
- Figma/mockups clarify visible UI only and never override DOCX.
- Для извлечения scope сначала используй `scripts/inspect_practical_scope_sources.py`; не создавай source-specific debug parser до зафиксированного ограничения штатного helper.
- Do not add a generic form-isolation test because a create form exists. Add it only when a source obligation explicitly requires isolation, preservation, reset or non-leakage of values.

## Independent review

The reviewer is a separate top-level `codex-thread`, read-only for reviewed matrix/TC. If the thread mechanism is available, dispatch it directly without searching external documentation. Before dispatch, prove every manifest input exists with the same SHA-256 in the target checkout; otherwise create and verify one immutable review-input snapshot and give only that snapshot to the reviewer. It must independently reconstruct obligations before comparing author artefacts. Reviewer JSON is captured byte-for-byte by the controller; a subagent does not satisfy this requirement.
