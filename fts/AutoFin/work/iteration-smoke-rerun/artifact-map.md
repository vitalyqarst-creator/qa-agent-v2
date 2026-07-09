# Artifact Map

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Review-cycle directory: `work/review-cycles/iteration-smoke-search-clear-context`
- Terminal status: `blocked-input`

## Artifacts In This Rerun Folder

| artifact | status | note |
| --- | --- | --- |
| `historical-blocked-state-check.md` | present | Historical failed run now validates as terminal `blocked-input`. |
| `scope-proposal.md` | present | Source-backed scope proposal for `BSR 32`. |
| `source-scope-inventory.md` | present | Inventory of source, scope, and runner directories. |
| `timeout-recovery-diagnostic-report.md` | present | Root-cause diagnosis for stage-appropriate timeout recovery profile handling. |
| `validator-report.autofin-package.json` | present | Package-level validator report; includes legacy noise and current-scope findings. |
| `validator-report.review-cycle.json` | present | Scoped review-cycle validator report. |
| `validator-report.writer-draft.json` | present | Validator report for the writer draft. |
| `validator-report.review-cycle.after-timeout-fix.json` | present | Scoped review-cycle validator after timeout/draft-placement fix. |
| `validator-report.handoff.after-timeout-fix.json` | present | Handoff validator after timeout/draft-placement fix. |
| `validator-report.writer-draft.after-timeout-fix.json` | present | Work-dir draft validator after moving unsigned draft out of production `test-cases/`. |
| `sdk-diagnostic-dry-run/run.json` | present | Read-only rendered SDK diagnostic prompt for blocked current stage. |
| `blocked-runner-report.md` | present | Terminal blocked diagnosis for this rerun. |
| `iteration-process-report.md` | present | Final process report. |

## Runner-Owned Artifacts

| requested artifact | runner path | status |
| --- | --- | --- |
| cycle state | `work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml` | present; terminal `blocked-input` |
| session map | `work/review-cycles/iteration-smoke-search-clear-context/codex-session-map.yaml` | present; one writer session started |
| runner events | `work/review-cycles/iteration-smoke-search-clear-context/runner-events.ndjson` | present |
| writer draft | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md` | present as unsigned work-only draft; moved out of production `test-cases/` |
| writer response | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-response.md` | present |
| validator report | `work/review-cycles/iteration-smoke-search-clear-context/outputs/validator-report.writer-r1.latest.json` | present |
| writer completion manifest | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-completion.yaml` | present |
| timeout recovery report | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-timeout-recovery.md` | present |
| before snapshot | `work/review-cycles/iteration-smoke-search-clear-context/versions/before-writer-r1/snapshot-manifest.yaml` | present |
| after snapshot | `work/review-cycles/iteration-smoke-search-clear-context/versions/after-writer-r1/snapshot-manifest.yaml` | present |
| reviewer findings | none | not created because no reviewer stage started |
| revision | none | not applicable |
| final reviewer output/signoff | none | not applicable; no sign-off |
