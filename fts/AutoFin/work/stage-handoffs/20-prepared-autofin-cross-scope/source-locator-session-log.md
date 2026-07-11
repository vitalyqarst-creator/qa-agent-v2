# Source Locator Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-source-locator` |
| mode | `clean AutoFin-only compiler matrix` |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-autofin-cross-scope` |
| started_from | `user-authorized continuation plan` |
| status_after | `ready-for-next-stage` |

## Inputs Read

- `source/FT4AutoFinFinal.docx/xhtml/pdf` selection metadata and existing FT4 parity artifacts — confirm source family.
- Existing FT4 scope/design artifacts for matrix candidates — classify compiler route and reject unsafe legacy dictionary duplication.
- `evals/prepared-cross-scope-validation/20260711/blocker-report.md` — preserve prior wrong-package run as historical evidence.

## Inputs Not Used

- `source/AutoFinPreFinal.*` — older source family excluded.
- Neighboring `fts/*` packages — outside authorized package boundary.
- Existing production test cases and previous cycle drafts — forbidden as requirement evidence.

## Key Decisions

- Pin every matrix candidate to `FT4AutoFinFinal` and `fts/AutoFin`.
- Keep complex dimensions as `standard-required`; do not expand the prepared fast path in this iteration.
- Use widget selection only as the eligible control canary; replace visual assessment with search-clear after duplicate dictionary IDs were detected.

## Risks And Fallbacks

- Legacy widget design artifacts required canonical normalization before compiler use; semantics were aligned with already accepted prepared-package evidence.
- Print-form gap inventory and atomic ledger are inconsistent; live continuation stopped before any LLM session.

## Validation

- Source stems and XHTML confirmation checked through explicit UTF-8 file reads.
- Architecture audit baseline: 59 checks, no findings.

## Contamination Check

- No neighboring FT source or old AutoFinPreFinal requirement text was used to select or populate matrix evidence.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Confirmed source boundary | AutoFin / FT4 family selected | `source-selection.md` |
| 2 | Classified existing FT4 design sets | One fast control and two standard-required scopes; visual dictionary candidate rejected | `scope-matrix.md` |
| 3 | Ran compiler preflight | Two packages built; print-form blocked on orphan gaps | `evals/prepared-cross-scope-validation/20260711/autofin-compiler-matrix-report.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Source boundary | pass | exact DOCX/XHTML/PDF stems | compiler path/hash gates |
| Scope route classification | pass | applicability matrices | compile all three snapshots |
| Gap fidelity | fail | print-form orphan gaps | semantic remediation required before live |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | CLI rejected incomplete immutable output and execution directory shapes | First rerun supplied cycle-level directories instead of leaf directories | Retried with the canonical package leaf and writer execution leaf | `not-applicable: command-argument correction only` | no | none; compiler rejected both invocations before reading semantic inputs | Use the canonical directory shape for subsequent reruns |

## Handoff Notes For Next Session

- Live fast path is paused despite `MATRIX-001` eligibility because matrix-wide fidelity preflight found a real print-form blocker.
