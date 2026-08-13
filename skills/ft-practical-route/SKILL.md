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
2. Create `scope-obligations.json` with one source-backed `OBL-*` per independent assertion, explicit `CTX-*` execution contexts and one shared `SETUP-*` prerequisite catalog. Before this, find every document-global rule referenced by a scope field's type, format, dictionary or cross-reference and include its applicable subrules in the OBL/scenario set. Before an `ui-calibration` gap, inspect related FT figures, PDF and visual-only inputs: transfer a resolved control identity/name/location into `visual_binding`; retain only a documented residual runtime uncertainty in the gap. Record every gap in `clarifications`; if a business answer is required, create the linked `scope-clarification-requests.md` in the same run. Do not create TC yet.
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
- One `SCN-*` normally has one TC and one primary expected result. Before matrix review, scan only possible one-action/one-reaction groups and document every candidate in `workflow-state.json.scenario_consolidation`: merge it as a parameterized TC, cover an internal check through an observable result, or document why the scenarios remain separate. Do not auto-merge prose. Different create/edit flows, field editability versus manual input, different initial states and different primary oracles are separate. One OBL/CTX may have several SCN only for independent source-backed classes, boundaries or initial states; do not duplicate one check.
- Matrix declares initial state, its formation and the checked action separately. Test data are concrete values/files or precise properties plus a preparation method; never restate the checked rule as data. Before declaring `needs-test-data`, exhaust literals from FT, approved BA decisions, closed dictionaries, saved DaData fixtures and allowed synthetic fixtures. Reuse one verified data profile for equivalent checks when it is stable; do not invent data diversity. In each TC retain only literals used by steps/oracle or needed to complete a save/transition, not a copied full integration profile. Do not write «подготовлена строка запроса», «доступны указанные предпосылки», «параметры, указанные в тестовых данных» or any equivalent circular placeholder. A trigger-state action is a concrete user action with a screen, field and value; never use meta-steps such as «Сформировать исходное состояние» or «Выполнить подготовку состояния». Put every trigger-state action in its own numbered step and add a follow-up observation when checking absence of persistence. For a one-file limit, attach an allowed file before attempting a distinct second file. If FT prescribes exact message text, reproduce it verbatim in the expected result. A source-only internal action without an oracle does not become a standalone `blocked-observability` TC: link it to a source-backed observable outcome using `covered-by-observable-result`; if no outcome exists, record a source blocker instead of inventing a check.
- Preserve source modifiers in OBL and review reconstruction: execution contexts, quantifiers, boundaries, conditions and exceptions. Split them if they create distinct flows or results.
- Do not treat a local field row as the complete rule when it names a data type, format, dictionary or cross-reference. Independently locate the document-global definition and cover every applicable explicit subrule. A field of type «Дата», for example, requires the format, ranges, calendar validity and persistence rules if the FT defines them globally; one accepted date is not sufficient.
- A finite list is not automatically one TC: split items that trigger distinct transitions or results; keep one TC only for a same-action, same-logic composition/value check.
- Missing UI/data/observability is an execution status, not invented behavior or a blocker unless the source assertion itself cannot be represented. Derive it from all linked SETUP prerequisites. A source-only internal assertion without an oracle is not an execution status of its own: it is covered by an observable result or escalated as a source blocker. A missing setup otherwise makes `ready` invalid. Apply the primary-status order defined in the canonical route reference: `needs-test-data` never becomes only `candidate-ui-calibration`. `blocked-observability` is not an external blocker by itself. A source contradiction is a blocker and no TC may be invented for it.
- Compare the selected section heading with nearby tables and source assertions. Record a terminology discrepancy as a gap; ground the working scope subject in the content, not a contradictory heading.
- Before `workflow-state.json`, call the stdout-only `validate_practical_obligations.py` and call its result only an obligations-structure check. Call `validate_practical_scope.py` only after the workflow state and matrix exist.
- Если активный scope использует legacy matrix schema, сначала составь read-only plan через `migrate_practical_matrix_contract.py`. Не мигрируй и не сбрасывай revision budgets без явного разрешения пользователя; migration сохраняет snapshot, изолирует structural matrix conversion и требует последующей синхронизации TC по canonical route.
- Обычный подтверждённый scope-local ответ БА связывай с GAP и SHA-256. Решение БА, прямо отменяющее или изменяющее ФТ, регистрируй package-level по `practical-v0.9-ba-decision-registry-format.md`: оно имеет приоритет только в явно указанной области действия, исключает связанные OBL из matrix/TC и делает затронутые scope stale. При противоречии без готового решения обязательно создай CLR-вопрос в том же запуске.
- Figma/mockups clarify visible UI only and never override DOCX. FT figures, PDF and visual-only inputs must nevertheless be checked before UI-calibrating a control identity, label or location; record the checked sources and residual runtime uncertainty in `visual_evidence_check`.
- Для извлечения scope сначала используй `scripts/inspect_practical_scope_sources.py`; не создавай source-specific debug parser до зафиксированного ограничения штатного helper.
- Do not add a generic form-isolation test because a create form exists. Add it only when a source obligation explicitly requires isolation, preservation, reset or non-leakage of values.

## Independent review

The reviewer is a separate top-level `codex-thread`, read-only for reviewed matrix/TC. If the thread mechanism is available, dispatch it directly without searching external documentation. Before dispatch, prove every manifest input exists with the same SHA-256 in the target checkout; otherwise create and verify one immutable review-input snapshot and give only that snapshot to the reviewer. It must independently reconstruct obligations before comparing author artefacts. For a large scope, use the manifest’s compact digest-bound receipt contract and return it in the first raw JSON response; do not ask the reviewer to compress a completed verdict. Reviewer JSON is captured byte-for-byte by the controller; a subagent does not satisfy this requirement.
