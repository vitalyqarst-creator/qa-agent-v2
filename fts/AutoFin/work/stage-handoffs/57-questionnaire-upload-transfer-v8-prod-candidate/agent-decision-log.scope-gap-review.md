# Agent Decision Log — Scope Gap Review V8

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v8-prod-candidate` |
| stage | `ft-test-case-reviewer` |
| started_from | `prompt.scope-gaps-to-reviewer.exec.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DL-001` | 1 | `gap` | BSR 210 and `CR-QUT-001` | Keep `GAP-QUT-001` open-non-blocking. | Source defines 40 МБ but no byte convention. | `scope-gap-review.md` | `high` | `applied` |
| `DL-002` | 2 | `validation` | fidelity inputs | Accept literal, gap and oversize bindings. | Direct source and package artifacts agree. | `scope-gap-review.md` | `high` | `applied` |
| `DL-003` | 3 | `routing` | corrected H57 handoff | Route to immutable iteration with promotion off. | H56 routing conflict no longer exists. | `prompt.scope-to-iteration.md` | `high` | `applied` |
| `DL-004` | 4 | `fallback` | missing `pdftotext` | Use pypdf text cross-check and identical-hash prior visual evidence. | PDF remains structural support, not source truth. | reviewer session log | `medium` | `applied` |
| `DL-005` | 5 | `validation` | reviewer performance | Preserve passed semantic verdict but record performance debt. | Cost does not invalidate evidence, but blocks claims of efficient mass operation. | reviewer session log | `risk:171411 tokens` | `applied` |
