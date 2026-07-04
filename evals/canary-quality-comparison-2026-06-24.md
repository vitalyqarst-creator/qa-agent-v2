# Canary quality comparison before broader test-case writing

## Purpose

Оценить, можно ли переходить от точечных canary-прогонов к более широкому написанию тест-кейсов агентом.

Критерии привязаны к основной цели: тест-кейсы должны максимально покрывать функциональные требования, оставаться проходимыми вручную и быть понятными.

## Compared Runs

| canary | scope type | terminal status | terminal validation on 2026-06-24 | coverage signal | residual uncertainty |
| --- | --- | --- | --- | --- | --- |
| `history-editing-fresh-canary-v2` | table/history behavior | `signed-off` | `valid=true`; `blocking_unwaived_count=0`; `scoped_findings_count=0` | `12/12` atoms covered; `10` TC | none in final R2 |
| `application-card-common-actions-flow-canary-v2` | action/dialog/status flow | `signed-off` | `valid=true`; `blocking_unwaived_count=0`; `scoped_findings_count=0` | `6/7` atoms covered; one source-backed unclear | `GAP-002`: no visible oracle for post-refusal edit prohibition |
| `document-print-form-tags-fresh-canary-v2` | document/tag table generation | `signed-off` | `valid=true`; `blocking_unwaived_count=0`; `scoped_findings_count=2` | `52/52` atoms covered by `16` TC | `GAP-001`: DOCX/PDF exact template mismatch; `GAP-002`: inverse `<previous_full_name>` oracle undefined |

## Quality Findings

The current agent version is materially better than the earlier runs:

- It no longer treats full-package historical validator noise as a terminal blocker for the active scope.
- It keeps source ambiguity as `GAP-*` / `unclear` instead of inventing deterministic UI or document-generation behavior.
- It closes semantic reviewer findings in a second writer round without losing traceability in split artifacts.
- It can produce readable manual TC sets for three different scope shapes: table behavior, action/dialog flow, and document/tag mapping.

The remaining weakness is not broad FT coverage. It is operational reliability and evidence hygiene:

- SDK runner execution still depends on using the correct Python environment.
- Long child sessions and stale locks need continued monitoring in real runs.
- Reviewer artifacts can still suffer encoding/display damage unless sessions consistently use explicit UTF-8 handling.
- Some older builder/regression artifacts still contain stale scoped-profile references; they should not be used as quality evidence for new runs.

## Decision

Do not start full-document generation yet.

Recommended next step is a limited pilot:

- choose `2-3` real, user-relevant scopes from the same FT package;
- run full writer-reviewer cycles with `.venv\Scripts\python.exe scripts\codex_review_cycle_runner.py run-until-terminal --session-timeout-seconds -1`;
- require terminal `valid=true`, `blocking_unwaived_count=0`, no unresolved semantic findings, and explicit `GAP-*` for every source ambiguity;
- review resulting TC manually for execution clarity before allowing a larger batch.

## Readiness Verdict

Current status: `limited-pilot-ready`, not `full-scale-ready`.

The evidence is strong enough to test quality on real production-like scopes, but not strong enough to trust unsupervised broad generation across a large FT without manual sampling and runner stability observation.
