# Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `prepared-fast-standard-comparison` |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-fast-standard-comparison` |
| started_from | `work/stage-handoffs/23-prepared-live-canary-contract-drift/workflow-state.yaml` |
| status_after | `blocked-input` for broader rollout; widget fast path accepted |

## Inputs Read

- `AGENTS.md` — project policy and routing.
- `skills/ft-test-case-iteration/SKILL.md` — separate-session iteration contract.
- `skills/agent-architecture-auditor/SKILL.md` — final architecture audit contract.
- `references/agent/instruction-loading-manifest.md` — exact standard role contexts and budgets.
- `references/qa/test-case-runtime-format.md` — canonical `## TC-*` requirement.
- `work/stage-handoffs/18-iteration-smoke-widget-selection-types/*` — matched widget source/scope inputs.
- `work/stage-handoffs/20-prepared-autofin-cross-scope/compiler-inputs/*` — cross-scope compiler matrix.
- Prepared cycles v13-v15 and standard controls v1-v4 — immutable runtime evidence.
- `AGENT-NOTES.md` — mandatory AutoFin package context.

## Inputs Not Used

- Existing/generated files under `fts/AutoFin/test-cases/` — excluded as requirement evidence and not modified.
- `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md` — unrelated untracked user file.
- Untracked `evals/sdk-turn-diagnostics/**` — unrelated diagnostics preserved unchanged.
- Neighboring `fts/*` packages and `AutoFinPreFinal.*` — not used as source evidence.

## Key Decisions

- Fast path retained only for compiler-proven `simple-field-property`; see `agent-decision-log.md`.
- Standard control remained a comparison/fallback diagnostic and was not treated as quality-equivalent after structural pass.
- Production promotion stayed disabled; v15 used dry-run only.
- Broader rollout stopped at real upstream obligation-closure defects.

## Risks And Fallbacks

- Standard context is extremely expensive: v4 reviewer alone reported about 2.9M tokens.
- Standard writer command count varied from 59 to 65; default raised to 80, but standard exec remains diagnostic rather than the preferred full workflow.
- Three compiler inputs require upstream artifact remediation before another matrix can be fully green.
- Audit helper emitted mojibake in possible-duplication text; corrupted text was not used as semantic evidence.

## Validation

- `python -m unittest tests.test_codex_exec_review_cycle_runner` — 53 tests passed before later additions.
- `python -m unittest tests.test_codex_exec_review_cycle_runner tests.test_prepared_workflow_compiler` — 80 tests passed.
- `python -m unittest tests.test_prepared_workflow_compiler tests.test_prepared_stage_package tests.test_codex_exec_review_cycle_runner` — 99 tests passed.
- Live prepared v14 — `accepted-not-promoted`.
- Live prepared v15 — `accepted-promotion-dry-run`; no production write.
- Common-actions routing — blocked before LLM as `standard-required`.
- Canonical `scripts/run_tests.py` — 486 tests passed, 1 skipped; artifact-validator 388/388 passed across 7 shards.
- AutoFin audit/strict validator — 0 findings for `work/stage-handoffs/24-prepared-fast-standard-comparison/*`; package-wide legacy baseline remains 1937 historical findings.
- `agent-architecture-auditor` — 0 confirmed findings, 0 warnings/errors; all instruction budgets pass.

## Contamination Check

- Production test-case target `test-cases/3-iteration-smoke-widget-selection-types.md` remained absent.
- Unrelated untracked files were neither staged nor modified.
- Existing test cases, prior drafts and neighboring FT packages were not used as requirements/templates.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `evals/prepared-fast-standard-comparison/20260711/widget-selection-routing-runtime-report.md` | `medium report` | `targeted apply_patch` | `yes` | `apply_patch` | `yes` |
| `work/stage-handoffs/24-prepared-fast-standard-comparison/*` | `small handoff bundle` | `targeted apply_patch` | `yes` | `apply_patch` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Diagnosed standard v2 validator block | Writer had six `### TC-*`; canonical format was not loaded | v2 validator/draft |
| 2 | Added scenario resolver preflight | Exact writer/reviewer instruction contexts enforced | commit `464c82b` |
| 3 | Ran standard v3/v4 controls | v3 exposed budget defect; v4 returned six semantic findings | v3/v4 cycle states |
| 4 | Added package notes and route budgets | Both routes preserve mandatory context; fast cap remains strict | commits `14aa96a`, `090f0c4` |
| 5 | Ran prepared v14/v15 | Both accepted; v15 dry-run wrote no production | v14/v15 cycle states |
| 6 | Ran cross-scope matrix | One fast, five standard, three upstream blockers | `iteration-summary.md` |
| 7 | Initial large patch context did not match exact runner line | Patch split into smaller verified edits; no partial file mutation | `TF-001` |
| 8 | Architecture audit stdout contained mojibake in possible duplication lines | Relevant files reread with explicit UTF-8; corrupted text excluded from semantic decisions | `TF-002` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Obligation closure | pass for widget | v14/v15 obligation gate and reviewer | retain regression |
| Gap preservation | pass | OBL-001/003/006 gap-preserved | do not weaken |
| Fresh sessions | pass | distinct backend session IDs | retain contract test |
| Idempotency | pass | repeated v14 rejected; state hash unchanged | retain contract test |
| Promotion guard | pass | v15 dry-run, no target/temp file | no real promotion in eval |
| Cross-scope readiness | fail | three upstream compiler blockers | remediate next iteration |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | apply-patch context mismatch in scenario replacement | one combined multi-hunk patch | smaller exact-context `apply_patch` edits plus compile/tests | `n/a` | `n/a` | partial edit | verified with `py_compile`, diff and tests |
| `TF-002` | PowerShell stdout mojibake for Russian duplication candidates | console-rendered audit text | explicit UTF-8 reads of canonical skill/reference files; corrupted stdout discarded | `n/a` | `n/a` | source-fidelity risk | mojibake text was not used for coverage, routing or expected-result decisions |

## Handoff Notes For Next Session

- Remediate client-addresses and document-files by restoring one coverage-obligation row per ledger atom or explicitly classifying atoms out of the compiler input.
- Replace invalid `OBL-N/A-001` in document-recognition with a valid stable OBL id and rerun compiler checks.
- Do not expand fast eligibility while those upstream defects remain.
- Re-run full compiler matrix after remediation; no LLM live run is needed until deterministic compilation is green.
