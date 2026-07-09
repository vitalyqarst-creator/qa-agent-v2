# Persistence calibration evaluation report

| item | value |
|---|---|
| branch | `audit/stabilize-testcase-agent-persistence-calibration-handoff` |
| commit | to be recorded after commit |
| source artifacts checked | `FT4AutoFinFinal.docx`; `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.pdf`; `fts/AutoFin/AGENT-NOTES.md` |
| exact save action found | no |
| save success oracle found | no |
| exit-after-save flow found | no |
| reopen path found | partial: `BSR 35` opens a selected application card |
| cleanup/isolation found | no |
| current date source `D` found | no |
| terminology decision found | yes: section 4.3 uses `Отношение к заявителю` |
| TC still candidate | 7 |
| TC convertible now | 0 |
| v4 field-level canary overwritten | no |

## Remaining blockers

- `BA-PS-001`: exact save action.
- `BA-PS-002`: save success oracle.
- `BA-PS-003`: exit-after-save flow.
- `BA-PS-004`: exact route to reopen the same saved application, beyond the source-backed `BSR 35` open-selected-card action.
- `BA-PS-005`: cleanup/isolation policy.
- `BA-PS-006`: authoritative current application date `D`.
- `BA-PS-007`: BA/UI confirmation that UI label should follow FT term `Отношение к заявителю`.

## Conversion decision

No TC was converted to executable. Placeholder save wording remains allowed only because every persistence smoke TC remains `candidate-persistence-calibration` and is linked to BA/UI calibration questions.
