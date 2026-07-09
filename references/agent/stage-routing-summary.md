# Stage Routing Summary

Use this only for orchestration. It tells a dispatcher which stage scenario to start, not how to perform that stage.

| stage need | scenario | primary skill | required handoff evidence |
|---|---|---|---|
| locate FT package and sources | `source_locator.discovery` | `ft-source-locator` | selected source package or blocked source ambiguity |
| analyze user-provided scope | `scope.manual` | `ft-scope-analyzer` | scope contract, gaps, active next prompt |
| review scope gaps before writer | `reviewer.scope_gap_review` | `ft-test-case-reviewer` | gap review verdict and routing |
| write first cycle draft | `writer.session_initial_draft` | `ft-test-case-writer` | canonical TC, split artifacts if required, Writer Quality Gate |
| structure preflight | `reviewer.structure_preflight` | `ft-test-case-reviewer` | parseability and handoff blockers |
| semantic review | `reviewer.semantic_traceability_test_design` | `ft-test-case-reviewer` | findings, traceability matrix, semantic verdict |
| semantic revision | `writer.session_semantic_revision` | `ft-test-case-writer` | writer response and updated affected artifacts |
| final format review | `reviewer.structure_format_final` | `ft-test-case-reviewer` | final format findings or format pass |
| format-only revision | `writer.session_format_revision` | `ft-test-case-writer` | format-only writer response |
| semantic regression after format change | `reviewer.semantic_regression` | `ft-test-case-reviewer` | coverage/traceability unchanged verdict |
| runner orchestration | `sdk_orchestration.review_cycle` | runner | cycle state, session map, version snapshots |

Terminal statuses for the cycle are `signed-off`, `round-cap-reached` and `blocked-input`. Do not sign off from orchestration alone; sign-off requires the stage artifacts and validator gates defined by the stage-specific scenario.
