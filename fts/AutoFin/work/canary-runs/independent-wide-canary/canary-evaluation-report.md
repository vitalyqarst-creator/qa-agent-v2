# Independent Wide Canary Evaluation Report

## Run Metadata

| item | value |
| --- | --- |
| branch | `audit/stabilize-testcase-agent-independent-wide-canary` |
| base branch | `audit/stabilize-testcase-agent-canary-output` |
| base commit at generation start | `bd83f5d` |
| final commit hash | `recorded in final response; a commit cannot contain its own final hash without changing that hash` |
| agent-layer changes before generation | `no` |
| production artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary.md` |
| work directory | `fts/AutoFin/work/canary-runs/independent-wide-canary/` |

## Source Artifacts Used

| artifact | role |
| --- | --- |
| `fts/AutoFin/source/FT4AutoFinFinal.docx` | Main FT, source of truth for meaning. |
| `fts/AutoFin/source/FT4AutoFinFinal.xhtml` | Mandatory machine-readable extraction source for table 7 rows and BSR anchors. |
| `fts/AutoFin/source/FT4AutoFinFinal.pdf` | Structural/visual cross-check source. |
| `fts/AutoFin/AGENT-NOTES.md` | Package-specific notes: `О` means requiredness, `Р` means editability; DaData context is auxiliary only. |

Forbidden previous canary/test-case artifacts were not used as source or template.

## Selected Scope

Selected: table 7 rows for address/contact fields in section 4.3, `BSR 115`-`BSR 189`.

| package_id | included source rows | included BSRs | rationale |
| --- | --- | --- | --- |
| `WP-01` | address registration rows | `BSR 115`-`BSR 137` | Core registration address behavior, DaData, manual input, apartment/private-house branch. |
| `WP-02` | actual residence address rows | `BSR 138`-`BSR 161` | Conditional actual address branch and manual actual-address fields. |
| `WP-03` | client contacts rows | `BSR 162`-`BSR 172` | Mobile, e-mail, home/work phone add/remove behavior. |
| `WP-04` | contact-person repeatable block rows | `BSR 173`-`BSR 189` | Wider than previous narrow focus: contact names, relation list, phone, birth date, add/delete row. |

Excluded from this canary: personal data rows before `BSR 115`, employment/income, documents, participants, visual assessment, and common card actions. These are separate 4.3 subareas and would push the run beyond the target 25-45 TC size.

## Counts

| metric | count |
| --- | ---: |
| selected normalized source rows | 17 |
| selected XHTML table rows | 39 |
| selected requirement codes | 75 |
| generated test cases | 38 |
| coverage gaps / BA questions | 9 gaps / 4 BA questions |

## TC Distribution

| dimension | count |
| --- | ---: |
| Positive | 34 |
| Negative | 4 |
| `WP-01` | 10 |
| `WP-02` | 11 |
| `WP-03` | 8 |
| `WP-04` | 9 |

## Coverage Summary

The artifact covers visible field presence, default values, source-backed DaData hints, address decomposition, manual address composition, phone/e-mail positive format examples, contact phone add/delete actions, contact-person repeatable block creation/deletion, relation list values, and the `Иное` dependency branch.

The artifact deliberately does not invent exact UI reactions for numeric/text/e-mail/date invalid values when the FT only states a restriction class. Those obligations are preserved as `GAP-AW-*` in `coverage-gaps.md`.

## Coverage Matrix

Detailed matrix: `fts/AutoFin/work/canary-runs/independent-wide-canary/coverage-matrix.md`.

High-level requirement-to-TC mapping:

| requirement range | covered by |
| --- | --- |
| `BSR 115`-`BSR 120` | `TC-AF43-AW-001`-`TC-AF43-AW-005` |
| `BSR 121`-`BSR 137` | `TC-AF43-AW-006`-`TC-AF43-AW-010`; `GAP-AW-002` |
| `BSR 138`-`BSR 145` | `TC-AF43-AW-011`-`TC-AF43-AW-016` |
| `BSR 146`-`BSR 161` | `TC-AF43-AW-017`-`TC-AF43-AW-021`; `GAP-AW-003` |
| `BSR 162`-`BSR 172` | `TC-AF43-AW-022`-`TC-AF43-AW-029`; `GAP-AW-004`; `GAP-AW-005`; `GAP-AW-006` |
| `BSR 173`-`BSR 189` | `TC-AF43-AW-030`-`TC-AF43-AW-038`; `GAP-AW-007`; `GAP-AW-008`; `GAP-AW-009` |

## BA Questions / Unresolved Assumptions

Source-backed gaps are listed in `coverage-gaps.md`.

Key BA questions:

1. Which UI oracle should be used for invalid numeric/text/e-mail/date values: filtering, clearing, highlighting, message, save rejection, or transition rejection?
2. Which artifact is allowed for `kladr` verification when DaData address decomposition is tested?
3. Are home/work phone default-hidden states expected to be separately checked, and what are the exact UI labels for add/remove widgets?
4. Is the relation list a closed dictionary with no extra values?

## Validator / Reviewer Results

| check | result | stdout/stderr summary |
| --- | --- | --- |
| `python scripts/run_tests.py --suite architecture` | passed | 59 checks, 0 findings; all instruction budgets passed. |
| `python scripts/run_tests.py --suite agent-layer-fast` | passed | 210 tests, 1 skipped. |
| `python scripts/run_tests.py --suite artifact-validator-sharded` | passed | 310 artifact-validator tests across 7 shards passed. |
| `git diff --check` | passed | no whitespace errors. |
| `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output .../validator-autofin.json` | package has historical findings | Package-wide scan: 1220 findings, 74 errors, 274 warnings, 872 info. Scoped to new canary artifact: 3 warnings. Raw package JSON was not committed because it is a 4.3 MB historical backlog dump; this report records the summary. |
| `python scripts/validate_agent_artifacts.py --root fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary.md --json --output .../validator-new-artifact.json` | completed with warnings | 1 test-case file checked, 0 errors, 3 warnings, 16 checks. |

## New Artifact Validator Findings

| finding | severity | evaluation |
| --- | --- | --- |
| `source-row-inventory-missing` | warning | The source inventory exists as `source-scope-inventory.md`, but not under the exact validator-recognized heading/file shape. This is a canary output defect. |
| `writer-quality-gate-missing` | warning | `reviewer-notes.md` and this report contain review notes, but no canonical `Writer Quality Gate` artifact was produced. This is a canary output defect. |
| `test-case-negative-type-without-negative-oracle` | warning | Validator flagged `TC-AF43-AW-003` and `TC-AF43-AW-014`. These cases use source-backed DaData-not-found messages, but validator output shows mojibake evidence and did not recognize them as negative oracles. Needs investigation: either artifact wording should be adjusted or validator encoding/oracle detection should be improved. |

## Major Defects Found

1. The workflow did not naturally create canonical split writer artifacts (`source-row-inventory.md`, `writer-quality-gate.md`) for a direct canary run under the custom work directory, so validator recognizes the production file as package-based but missing canonical support artifacts.
2. The agent did not create a formal negative-oracle inventory before writing; missing invalid-value oracles were captured as gaps after generation, but current workflow would benefit from making this an explicit pre-writer artifact.
3. Encoding handling remains fragile in terminal/Python stdout for Cyrillic source snippets; this affected diagnostic readability and appears in validator evidence for negative-oracle warnings.
4. Direct review found warnings and did not produce lifecycle `signed-off`; this canary should be treated as a generated artifact plus evaluation, not as approved baseline.

## Recommended Future Agent-Layer Fixes

1. Provide a clean diagnostic/eval route that still produces validator-recognized split artifacts under the canary work directory.
2. Require negative/requiredness oracle inventory for table-heavy UI scopes before writer output, even for one-pass canary generation.
3. Make validator path discovery configurable so custom canary work directories can satisfy `source-row-inventory` and `writer-quality-gate` expectations without copying full design artifacts into production files.
4. Harden Cyrillic encoding for Python CLI output and validator evidence rendering on Windows.
5. Add a package-level fixture catalog for AutoFin application-card field checks to avoid repeated generic setup through blank application creation.

## Remaining Risks

- Coverage is intentionally incomplete for invalid input enforcement where the FT does not define an observable UI reaction.
- The production artifact has not passed a full session-based writer/reviewer lifecycle.
- The package-wide validator still has many historical findings unrelated to this canary, so package-level pass/fail cannot be used as clean signal for this output.
- PDF cross-check was structural only; no PDF page-level row parity artifact was generated for this custom canary.
