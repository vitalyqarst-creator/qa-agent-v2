# Reviewer Session Log: Structure Preflight R1

## Session Metadata

| field | value |
| --- | --- |
| mode | `structure_preflight` |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `client-documents-upload-and-actuality` |
| status_after | `structure-preflight-failed` |

## Inputs Read

- `fts/ft-2-OF_17/test-cases/section-31-client-documents-upload-and-actuality.md`
- `fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/outputs/writer-r1-response.md`
- `fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/outputs/writer-session-log.writer-r1.md`
- `fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.writer-r1.md`
- `fts/ft-2-OF_17/work/review-cycles/client-documents-upload-and-actuality/outputs/scoped-validator-profile.writer-r1.json`

## Inputs Not Read

- `validator-report.writer-r1.latest.json`
- Directories under `fts/`
- `cycle-state.yaml`

## Checks

| check | result | evidence |
| --- | --- | --- |
| parseability | `pass` | Markdown and JSON surfaces were readable/parseable. |
| TC runtime fields | `pass` | All 18 TC blocks include required runtime sections and fields. |
| continuous numbering | `pass` | `TC-CDUA-001`..`TC-CDUA-018`, no gaps. |
| duplicate wrapper headings | `pass` | No duplicate H2 wrappers or duplicate TC headings found. |
| scoped-validator evidence | `fail` | Profile is a bootstrap placeholder that says it must be overwritten by validate. |
| coverage summary consistency | `warn` | Summary says `TC-CDUA-001`..`TC-CDUA-012`; actual TC range is `TC-CDUA-001`..`TC-CDUA-018`. |

## Writes

- `evals/sdk-turn-diagnostics/reduced-05-write-evals-artifacts/reviewer-artifacts/structure-preflight-r1-findings.md`
- `evals/sdk-turn-diagnostics/reduced-05-write-evals-artifacts/reviewer-artifacts/reviewer-session-log.structure-preflight-r1.md`
- `evals/sdk-turn-diagnostics/reduced-05-write-evals-artifacts/reviewer-artifacts/agent-decision-log.structure-preflight-r1.md`
