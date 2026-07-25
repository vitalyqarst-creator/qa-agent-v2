# Production Global Rules

This file is the self-contained production projection of the full repository's global rules. The production bundle loads it through `production-instruction-loading.md`; the root `AGENTS.md` of the full development repository is not part of the bundle.

## Sources and Boundaries

- DOCX is the source of truth; matching XHTML is mandatory for machine-readable extraction. Without XHTML, the scope is blocked as `blocked-input`.
- PDF is used only for structural/visual cross-check. Support files and mockups do not create business rules.
- After FT package selection, package-local `AGENT-NOTES.md` is mandatory when present.
- Do not invent behavior, fields, values, or integrations. Record ambiguity as a coverage gap with an exact source locator.
- Extract a dictionary or fixed value list completely; concrete test data must be source-backed and reproducible.

## Result Quality

- One test case verifies one obligation and has one main expected result; independent atomic statements are not merged.
- Preserve exact requirement codes and full traceability to source assertions and obligations.
- The result must be suitable for manual execution. Do not present a UI-calibration candidate as an executable production case.
- Old test cases, benchmark/history, and arbitrary unregistered files are not model input.
- The reviewer receives literal elements of the whole confirmed scope, including rows without obligations, the complete relevant dictionary slice, and only registered hash-bound mockup images; evidence must not be silently truncated.
- Before reviewer, runtime must prove bounded semantic parity of each XHTML-backed literal element with a unique DOCX occurrence and, when a PDF is registered, with the text of a concrete PDF page or a minimal code-bounded page range. DOCX occurrences preserve document order; all rows/cells of one XHTML table stay in one DOCX table, different XHTML tables are not merged, and hash-bound section headings are proven in the preceding DOCX region. For table rows that the PDF extractor splits across adjacent pages, one cell fragment may be split into exact prefix/suffix continuations: cell anchors preserve original order, all occurrences are unique and non-overlapping, but the previous-page suffix does not have to precede the next-column anchors in the extraction stream. This is a semantic/structural cross-check, not proof of PDF table geometry. A short cell merged by the PDF extractor with neighbors is allowed only when its raw substring exactly fills the empty gap between the proven end of the previous fragment and the start of the next cell fragment; global token-boundary disabling is forbidden. Requirement codes inside scope are checked separately and with full token boundaries; identical codes do not replace semantic row/boundary parity. A normal accepted source receipt does not replace parity.
- The complete registered coverage-gap artifact and supporting cross-row bindings enter the pack literally. Gap ID mismatch with the registry blocks the run; temporary handling and downstream do-not-test rules are mandatory.
- Primary coverage mapping keeps one owner per TC. A sibling obligation actually used in setup, action, or cleanup is published separately as a role-tagged design-support chain; a finding must name the exact binding role.
- `reference-only` does not mean `external-dynamic`: dependency provenance must unambiguously bind `DICT-*` to `DEP-*`. Version/effective date are extracted from a qualified source only when an exact unambiguous declaration exists; conflict or unstructured declaration blocks the pack. SHA-256 source/content bindings are always recorded.
- Fixture values of a closed dictionary without a separate fixture artifact are allowed only as an exact subset of the full qualified value set: every value must have an exact-token binding to at least one registered source row. An external-dynamic/DaData fixture separately binds dictionary/fixture identity, response snapshot, source verification receipt, and lifecycle catalog row. The reviewer receives exact request/expected response, and runtime does not perform routine live revalidation.

## Execution

- Before shell commands, use a saved environment probe or `scripts/probe_environment.py`; follow the UTF-8 policy and do not assume the shell.
- This downstream bundle does not perform discovery or source qualification. Before start, it receives an independently accepted manifest v4, compiler-v3 obligations, hash-bound semantic projection, and registered scope boundary.
- Load only scenario `iteration.deterministic_production` from `production-instruction-loading.md`.
- `ft-agent run` works only with a closed schema-v2 config and a new immutable output directory. Canonical, source files, and workflow state are not changed.
- Allowed successful terminal statuses: `accepted-shadow` for a fully executable suite and `accepted-with-calibration-pending` when the reviewer explicitly confirms calibration candidates as `calibration-pending`. The second status always has `promotion_eligible=false`; publication is not part of a production run.
