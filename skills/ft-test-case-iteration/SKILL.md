---
name: ft-test-case-iteration
description: Run one source-qualified test-case iteration for an already selected FT package and confirmed scope through the public `ft-agent run` command.
---

# FT Test Case Iteration

Use this skill only after an FT package is selected and the external scope is confirmed. The production profile has one public entrypoint: schema-v2 config → fresh immutable attempt → source-bound writer route → deterministic gates → exactly one independent reviewer → `accepted-shadow`, honest `accepted-with-calibration-pending`, or explicit terminal failure.

## Входы

Before launch, these inputs must exist:

- package-local `scope-registry.json` with the selected scope, stable `tc_prefix`, structural XHTML boundary, and complete DOCX/XHTML/PDF/support/mockups registry;
- DOCX as source of truth and matching XHTML as mandatory extraction source;
- source evidence with manifest v4 and an independent accepted review receipt for the exact digest; a semantic compiler projection is optional and belongs only to an explicitly requested bridge route;
- compiler-v3 obligations;
- package `AGENT-NOTES.md`, when present.

The new `run-config.json` uses schema v2. Base required fields:

```json
{
  "schema_version": 2,
  "registry": "fts/example-ft/scope-registry.json",
  "ft_root": "fts/example-ft",
  "scope": "confirmed-scope",
  "source_evidence": "fts/example-ft/work/handoff-001/source-evidence.md",
  "obligations": "fts/example-ft/work/handoff-001/obligations.json",
  "writer_mode": "model-runtime-prose"
}
```

For new production attempts, `writer_mode: model-runtime-prose` is mandatory. Allowed route fields: `writer_mode`, `mockup_label_aliases`, `revision_findings`. If `writer_mode` is absent or different, stop before the attempt; do not fall back to a compatibility or deterministic-only route. Do not add `ft_slug`, design context, ready derivations, `tc_prefix`, source/canonical allowlists, model responses, publication target, or lifecycle status. The runner derives slug and context from accepted contracts and builds derivations itself.

If an input is missing, stale, ambiguous, or not hash-bound, do not bypass the check: route back to `ft-source-locator` / `ft-scope-analyzer` or close the scope as `blocked-input`.

## Workflow

1. Read package `AGENT-NOTES.md`, if present, and verify that selected `ft_root` and `scope` match the user request.
2. Choose a new attempt directory under `fts/<ft-slug>/work/`. The directory must not exist. Do not use previous-attempt results as model input.
3. Run the only public command:

```powershell
ft-agent run `
  --config fts/<ft-slug>/work/<handoff>/run-config.json `
  --output-dir fts/<ft-slug>/work/iterations/<new-attempt-id>
```

4. Do not run manual writing or review in parallel. The runner compiles the source set, builds graph/context/seed cases, calls the writer exactly once in `model-runtime-prose` only for runtime prose, then runs gates, builds `ReviewerEvidencePack` v2, sends the draft to exactly one independent reviewer, and rechecks run/source/canonical hashes.
5. Treat `accepted-shadow` or `accepted-with-calibration-pending` with a real reviewer receipt and closed gates as success. In the second case, calibration candidates have reviewer status `calibration-pending`, and the full suite is explicitly ineligible for promotion. This is not publication: canonical and workflow state are not changed.
6. On terminal failure, preserve diagnostic output as the attempt result. Repair is done separately; rerun only in a new directory.

## Выходы

One immutable attempt contains scope/contract bindings, generated derivations, coverage graph, bound context, shadow Markdown, production gate, full `reviewer-evidence-basis.json`, hash-bound `reviewer-evidence-pack.json`, writer/reviewer receipts for the actually used route, and terminal summary with phase time, attempts, artifact sizes, and token metrics.

Allowed successful statuses are `accepted-shadow` and `accepted-with-calibration-pending`; the latter always contains `promotion_eligible=false` and `non_promotable_reason=calibration-pending`. Blocking contract/input/design, review findings, and infrastructure failure remain honest terminal outcomes.

If terminal findings are passed to a separate remediation cycle, the handoff preserves `affected_traceability_refs`; traceability-gap closure is checked by `traceability_ref` / `atom_id`. That handoff is stored in `stage-handoffs/`, and its only process status remains `workflow-state.yaml`; do not change it inside the current immutable production attempt.

After a separate signed-off handoff, real UI verification is a post-iteration entry into `ft-ui-automation-prep` with a separate automation-ready release; do not run that skill inside the current immutable production attempt.

## Out of Profile

Incremental FT-version updates, benchmarks, UI automation, and historical session/cycle orchestration are outside this production profile. They require a separate qualification/development environment; do not mix their procedures, artifacts, or fallback routes into the current attempt.

Semantic-design bridge materialization, semantic sharding, full-process observation, benchmark wrappers, overnight controllers, and legacy deterministic-only writer/reviewer routes are also forbidden by the production allowlist. See `references/agent/production-route-allowlist.md`.

## Canonical References

- Production instruction context: [../../references/agent/production-instruction-loading.md](../../references/agent/production-instruction-loading.md)
- Production global rules: [../../references/agent/production-global-rules.md](../../references/agent/production-global-rules.md)
- Source-qualified iteration contract: [../../references/agent/lean-v2-iteration.md](../../references/agent/lean-v2-iteration.md)
- UI calibration candidates: [../../references/agent/negative-ui-calibration-policy.md](../../references/agent/negative-ui-calibration-policy.md)

## Ограничения

- Do not discover the FT package or choose the primary scope inside this skill.
- Do not pass old test cases, benchmark/history, or arbitrary unregistered files to the reviewer.
- Do not set a hard model timeout and do not perform internal retry.
- Do not edit canonical, source files, or workflow state.
- Do not present offline/precomputed acceptance as a real reviewer result.
