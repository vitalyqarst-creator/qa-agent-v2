# Формат `scope-coverage-gaps.md`

Этот документ задает канонический формат для `scope-coverage-gaps.md` в handoff-модели FT pipeline.

`scope-coverage-gaps.md` фиксирует ограничения покрытия внутри подтвержденного scope. Он не определяет границы scope и не заменяет `scope-contract.md`.

Каждый gap должен быть привязан к конкретному утверждению ФТ, а не только к общей теме scope. Если найден хотя бы один gap, вопросы и ответы хранятся в отдельном companion-файле `scope-clarification-requests.md`. Не добавляй поля для интерактивных ответов прямо в `scope-coverage-gaps.md`.

## Когда создавать

- для подтвержденного scope;
- как companion-артефакт к `scope-contract.md`;
- до handoff к writer, если внутри scope есть неоднозначности, missing rules или неразрешенные cross-FT зависимости.

## Обязательные секции

- `## Контекст`
- `## Summary`
- `## Coverage Gaps`
- `## Что Можно Покрывать Несмотря На Gaps`
- `## Что Нельзя Домысливать`
- `## Требуемые Уточнения`

## Правила формата

- `scope-coverage-gaps.md` не определяет границы scope, а только ограничения покрытия внутри подтвержденного scope.
- `blocking` влияет на допустимость старта writer-а и должен быть отражен в `Summary`.
- `Writer Rule` и `Reviewer Rule` обязательны, чтобы downstream этапы одинаково трактовали gap.
- Cross-FT зависимости без явной опоры фиксируй как gap, а не как расширение scope.
- Каждый `GAP-*` обязан содержать точную привязку к ФТ: раздел/подраздел, `GSR` или другой код требования при наличии, таблицу/строку, поле/условие, страницу PDF, цитату или краткое исходное утверждение.
- Если gap обнаружен после атомизации требований или review, указывай связанные `ATOM-*`, строки traceability matrix или явно пиши `not-yet-assigned`, если атом еще не создан.
- Не создавай gap без FT anchor. Если точный anchor не удается восстановить, это отдельный blocking gap о недостаточной трассировке источника.
- Если требование в целом покрыто, но gap ограничивает тест-дизайн для конкретной границы, округления, обязательности, видимости или редактируемости, все равно указывай affected FT statement и помечай `Coverage Impact` как `design-constraint-on-covered-atom`.
- Если gaps нет, сохрани файл с пустым списком и явным `Writing можно стартовать: yes`.
- Для пользовательских или аналитических ответов на gaps используй `scope-clarification-requests.md`, сохраняя привязку к `GAP-*` и краткую FT reference.

## Test-design Coverage Gap Fields

For any gap that limits test-design decisions, record these canonical fields in addition to the human-readable description:

- `gap_id`
- `source_ref`
- `affected_atom_id`
- `missing_behavior`
- `why_expected_result_not_derivable`
- `affected_test_design_dimension`
- `risk`
- `blocks_ready_for_review`
- `question_to_analyst`
- `temporary_handling`

Rules:

- `affected_test_design_dimension` must use the `coverage_dimension` vocabulary from `references/qa/review-findings-format.md`.
- `blocks_ready_for_review: yes` means writer must not set `stage_status: ready-for-review`; use `stage_status: blocked-input` until the missing behavior is clarified or explicitly deferred.
- `temporary_handling` must not invent expected behavior. It may say only what can still be covered safely, what is excluded, or which case is marked `unclear`.
- Explicit deferral requires `accepted_risks` in `workflow-state.yaml` with the same `GAP-*`, owner/role, rationale and revisit condition. Do not treat an open blocking gap as accepted risk just because it is listed in `open_questions`.

## Минимальный шаблон

```md
## Контекст

- `scope_slug`: `...`
- Основной FT: `...`

## Summary

- Найдено gaps: `N`
- Есть blocking gaps: `yes | no`
- Writing можно стартовать: `yes | partial | no`

## Coverage Gaps

### GAP-001
**FT Reference:** `section / GSR / table-row / field / condition / PDF page`
**Source Path:** `...`
**Related Atomic Statement(s):** `ATOM-001 | not-yet-assigned`
**Source Statement:** `краткая цитата или пересказ конкретного утверждения ФТ`
**Gap Type:** `ambiguity | missing-rule | cross-ft-dependency | missing-constraint | unconfirmed-shared-behavior`
**Description:** ...
**Impact:** `blocking | non-blocking`
**Coverage Impact:** `uncovered | unclear | partial | design-constraint-on-covered-atom`
**Affected Atom ID:** `ATOM-001 | not-yet-assigned`
**Missing Behavior:** `...`
**Why Expected Result Not Derivable:** `...`
**Affected Test-design Dimension:** `role-permission | status-lifecycle | decision-table | pairwise | boundary | equivalence | dependency | conditional-visibility | api-server-validation | integration | security | async | persistence | table-list | file-upload | calculation | numeric | date-time | length | scenario-use-case | performance | reliability | compatibility | usability | accessibility-ui | traceability | expected-result | atomarity | format | scope | other`
**Risk:** `high | medium | low`
**Blocks Ready For Review:** `yes | no`
**Question To Analyst:** `...`
**Temporary Handling:** `...`
**Writer Rule:** ...
**Reviewer Rule:** ...
**Needs User Input:** `yes | no`
**Status:** `open`

## Accepted-risk Deferral

Use only when a responsible owner explicitly permits review to proceed despite an unresolved blocking gap.

Rules:

- Keep the original `GAP-*` open.
- Keep `Impact: blocking` and `Blocks Ready For Review: yes`.
- Add matching `accepted_risks` entry to `workflow-state.yaml`.
- The accepted-risk entry must include `GAP-*`, `accepted-risk`, owner/role, rationale and revisit condition.
- Reviewer must include the deferred gap in residual risk / known unclear items.

## Что Можно Покрывать Несмотря На Gaps

- `...`

## Что Нельзя Домысливать

- `...`

## Требуемые Уточнения

- `...`
```

## Рекомендуемые значения `Gap Type`

- `ambiguity`
- `missing-rule`
- `cross-ft-dependency`
- `missing-constraint`
- `unconfirmed-shared-behavior`

## Что не включать

- подтвержденные границы scope;
- out-of-scope разделы как замену `scope-contract.md`;
- reviewer findings по уже написанным тест-кейсам.
- ответы пользователя / аналитика, которые должны храниться в `scope-clarification-requests.md`.
