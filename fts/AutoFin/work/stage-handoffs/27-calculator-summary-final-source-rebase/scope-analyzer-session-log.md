# Calculator Summary Final Source Rebase Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-scope-analyzer` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| started_from | `work/stage-handoffs/26-prepared-standard-calculator-summary/workflow-state.yaml` |
| status_after | `in-progress` |

## Inputs Read

- `AGENTS.md`, `skills/ft-scope-analyzer/SKILL.md`, `skills/ft-test-case-iteration/SKILL.md`.
- `AGENT-NOTES.md` and handoff 20 Final source selection.
- Historical canonical handoff 05 and active calculator test-design artifacts.
- Handoff 26 source-drift evidence and next-stage prompt.

## Inputs Not Used

- `source/AutoFinPreFinal.*` — historical source family, excluded from active requirement evidence.
- Historical `_artifact_write/**` and completed review-cycle snapshots — immutable evidence only.
- Untracked `test-cases/4.3-application-card-client-addresses-contacts.md` and `evals/sdk-turn-diagnostics/**` — user-owned and outside scope.

## Key Decisions

- Create a new numbered handoff instead of rewriting the signed-off historical handoff 05 in place.
- Rebase active scope evidence only from matching `FT4AutoFinFinal` DOCX/XHTML/PDF.
- Preserve the exact-mapping gap until an external calculator FT supplies an exhaustive oracle.

## Risks And Fallbacks

- The legacy package-wide BSR inventory is generated from PreFinal PDF and counts historical artifact mentions as mappings; it cannot be trusted as an active Final-source registry without changing its generator.

## Validation

- Reused saved runtime probe: Windows/PowerShell, repository Python 3.11.9, explicit UTF-8 reads.
- Starting tracked worktree was clean; unrelated untracked paths were enumerated and excluded.

## Contamination Check

- Production `fts/AutoFin/test-cases/**` is read-only and promotion remains disabled.
- New writes are limited to helper/tests, handoff 27, active calculator design artifacts, a new immutable live cycle and eval evidence.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Routed through scope analyzer then iteration | Final-source rebase precedes any writer/reviewer run | this log |
| 2 | Audited baseline | Handoff 05 and package BSR inventory are PreFinal-based; active design is already BSR 43–46 | handoffs 05, 20 and 26 |
| 3 | Extracted bounded Final evidence | DOCX semantic rows, XHTML codes/rows and PDF pages agree; BSR 35–38 are neighboring common actions, BSR 43–46 are calculator-summary | `final-bsr-evidence.json` |
| 4 | Built scope handoff and ran strict validation | Initial findings required canonical prompt headings, explicit empty oracle inventories and fresh visual inventory | handoff 27 validation |
| 5 | Regenerated package BSR inventory from Final | 329 codes; only active in-scope source-row mappings count; multiple mappings remain explicit conflicts | package BSR inventory |
| 6 | Ran gap-review attempt with configured default model | Backend rejected `gpt-5.6-sol` before reasoning because local Codex version is incompatible | failed start evidence; runnable state preserved |
| 7 | Ran gap-review with compatible `gpt-5.5` | Reviewer blocked on production TC mismatch after reading forbidden test-case/design inputs | immutable failed gap-review cycle |
| 8 | Corrected bounded scope-review data plane | Scope reviewer now receives only explicit handoff inputs; blocked review no longer routes to writer prompt | generic runner and regression tests |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Final XHTML availability | pass | handoff 20 has `xhtml_available: yes` | Extract bounded rows |
| Production mutation | pass | starting tracked diff under `test-cases/**` is empty | Recheck after each live run |
| Canonical scope rebase | pending | no new active handoff yet | Build from Final evidence |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/stage-handoffs/27-*/source-row-inventory.md` | `table-heavy source row inventory` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `work/stage-handoffs/autofin-bsr-source-inventory.md` | `large generated inventory` | `generated chunk then file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `work/stage-handoffs/27-*/*.md` | `bounded hand-authored Markdown` | `reviewable apply_patch` | `yes` | `n/a` | `yes` |
| `work/stage-handoffs/27-*/final-bsr-evidence.json` | `bounded JSON evidence` | `UTF-8 helper output` | `yes` | `scripts/extract_autofin_bsr_evidence.py` | `yes` |
| `work/review-cycles/codex-exec-prepared-standard-calculator-summary-final-*` | `machine runtime evidence` | `canonical runner writes` | `yes` | `scripts/codex_exec_review_cycle_runner.py` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | PowerShell quoting corrupted three inline extraction commands | inline `python -c` extraction | moved multiline extraction to a UTF-8 helper and require explicit UTF-8 artifact reread | `scripts/extract_autofin_bsr_evidence.py` | `yes` | `failed stdout was syntax errors only and was not used as source evidence` | Validate helper output against DOCX/XHTML/PDF and add focused tests |
| `TF-002` | artifact writer rejected a preamble-only empty-sections manifest | attempted to assemble the BSR inventory with `preamble_file` and `sections: []` | changed generator output to section content and used a non-empty level-1 manifest section | `work/stage-handoffs/27-calculator-summary-final-source-rebase/_artifact_write/bsr-inventory/manifest.json` | `yes` | `failed validation wrote no canonical artifact; previous legacy inventory remained unchanged` | Regenerate chunk, dry-run and assemble through canonical helper |
| `TF-003` | backend rejected configured default model before gap-review reasoning | start with `gpt-5.6-sol` inherited from local config | doctor confirmed runnable state and a new attempt used explicit compatible `gpt-5.5` | `work/review-cycles/calculator-summary-final-gap-review-20260711/runner-events.ndjson` | `yes` | `no reviewer verdict or source evidence was produced by the rejected turn` | Pin compatible model for remaining live runs and preserve failed start evidence |
| `TF-004` | compatible gap reviewer evaluated production TCs despite scope-only prompt | generic bounded reviewer always supplied canonical test cases and test-design directory | made allowed inputs scenario-specific and explicit for `reviewer.scope_gap_review` | `work/review-cycles/calculator-summary-final-gap-review-20260711/outputs/scope-gap-review-findings.md` | `yes` | `blocked verdict is invalid for scope-gap acceptance but exposes a real later writer/reviewer issue` | Never advance failed cycle; start new immutable gap review after regression tests |

## Handoff Notes For Next Session

- No writer/reviewer stage may start until the Final-source scope artifacts and non-blocking gap pass strict validation.
