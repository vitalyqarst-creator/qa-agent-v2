Findings summary:

- **Scoped-validator evidence is not valid evidence.** `scoped-validator-profile.writer-r1.json` is parseable JSON, but its `command` says it is a bootstrap profile that “must be overwritten” by the real validator run. Treat `current_scope_findings: []` and `unresolved_warning_error_count: 0` as unproven.

- **TC numbering is structurally continuous:** `TC-CDUA-001` through `TC-CDUA-018`, no gaps or duplicate TC IDs found.

- **Stale summary range:** the test-case file’s Coverage Summary declares executable cases as `TC-CDUA-001`..`TC-CDUA-012`, but the file contains `TC-CDUA-001`..`TC-CDUA-018`.

- **Runtime fields:** all 18 TC blocks contain the expected runtime fields/sections.

- **Duplicate wrapper headings:** none detected.

- **Parseability:** Markdown structure and validator JSON are parseable under the checked structural rules.