# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `visual-assessment-medium-scope-benchmark` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/prompt.iteration-to-medium-scope.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | H20 source selection | Use only `FT4AutoFinFinal` DOCX/XHTML/PDF | Current source family is mandatory | `source-selection.md` | high | applied |
| `DEC-002` | 2 | `scope-boundary` | H21 expanded matrix | Select full visual-assessment criteria scope | 13 OBL, complete dictionary, zero active gaps; closest valid medium target | `scope-contract.md` | high | applied |
| `DEC-003` | 3 | `scope-boundary` | H47 blockers | Reject employment scope | Driver alias and dictionary divergence remain unresolved | session log | high | applied |
| `DEC-004` | 4 | `source-boundary` | `resolve_sections()` and FT4 parity | Replace legacy anchors with section-16/20, XHTML 182-184, PDF 34/40-41, BSR 311-317 | Direct current-source evidence | parity/inventory | high | applied |
| `DEC-005` | 5 | `test-design` | BSR 313 and 314 | Keep two obligations but map both to one visibility TC | One action produces one main observable result; avoids duplicate TC | benchmark projection | high | applied |
| `DEC-006` | 6 | `coverage` | BSR 316/317 lack exact UI mechanism | Route two requiredness checks as candidate UI calibration | Policy forbids invented messages/highlights/transitions | requiredness inventory | high | applied |
| `DEC-007` | 7 | `artifact-write` | 52-row inventory | Use manifest helper before target write | Mandatory table-heavy write strategy | source-row inventory | high | applied |
| `DEC-008` | 8 | `routing` | Scope gates prepared | Route to `ft-test-case-iteration` | Full loop is the benchmark under test | workflow/prompt | high | applied |
| `DEC-009` | 9 | `test-design` | Prepared compiler grouping gate | Use one shared plan row for `ATOM-003; ATOM-004` and retain separate obligations | Compiler proves the only merged case has one action and one expected result | compiler projection | high | applied |
| `DEC-010` | 10 | `execution` | Validate-only and regression evidence | Permit checkpoint preparation but keep live blocked | Runtime identity/capacity/oracles pass; live still needs pushed checkpoint and separate authorization | `pre-live-test-report.md`; `pre-live-stop-gate.md` | high | applied |
| `DEC-011` | 11 | `risk` | Full validator suite | Treat two absent `ui-evidence-policy` fixture tests as recorded infrastructure debt, not a benchmark blocker | 389 tests passed; failures reproduce a missing untracked fixture directory and do not exercise changed code or selected scope | `pre-live-test-report.md` | medium | applied |
| `DEC-012` | 12 | `execution` | Pushed checkpoint `ab67a274...` matches origin | Authorize exactly one hash-bound exec dispatcher invocation | User authorized the complete plan; separate authorization preserves stop/replay safety | `pre-live-authorization.md` | high | applied |
| `DEC-013` | 13 | `execution` | One dispatcher completed | Consume authorization and close V1 as `changes-required-not-promoted` | Terminal rule forbids retry regardless of semantic outcome | `live-result.v1.json`; `stop-gate.md` | high | applied |
| `DEC-014` | 14 | `quality` | Reviewer F-001 | Do not promote or manually repair draft | Two dictionary obligations lack executable leaf values despite deterministic pass | findings; iteration summary | high | applied |
| `DEC-015` | 15 | `quality-feedback` | Blocking defect has exact structured oracle | Create one eval candidate for DICT leaf-value materialization/completeness | Failure is mechanically testable from immutable package data | eval candidate | high | applied |
| `DEC-016` | 16 | `routing` | Performance targets pass; quality gate false-negative remains | Route next stage to agent-layer architecture/remediation, not another live run | Root problem is compiler/runner/gate contract, not source scope or one-off case wording | next prompt | high | applied |
| `DEC-017` | 17 | `infrastructure` | Full validator had two missing-fixture failures and diagnostics could pollute the repository | Restore the tracked UI evidence fixture and bind diagnostic output to a temporary directory | Removes false infrastructure noise before measuring the process change | commit `f91b476` | high | applied |
| `DEC-018` | 18 | `execution` | Dictionary/calibration regressions and full suites are green | Compile V2 from the same H52 scope as package v7 and keep the production target absent | Isolates the prepared-package remediation from source/scope changes | V2 prepared-input; benchmark protocol | high | applied |
| `DEC-019` | 19 | `architecture` | Validate-only rejected a hard-coded package number in the writer runtime profile | Require runner-validated digest/fingerprint without naming a numeric package version | Version ownership belongs to the runner; instruction text must survive future package bumps | runtime profile; regression test | high | applied |
| `DEC-020` | 20 | `execution` | V2 validate-only, exec dry-run, 460-test suite and 61-check audit pass | Prepare immutable checkpoint but keep live blocked until a separate hash-bound authorization | Preserves stop/replay safety and prevents package drift | `pre-live-test-report.v2.md`; `pre-live-stop-gate.v2.md` | high | applied |
| `DEC-021` | 21 | `execution` | Pushed checkpoint `8223d580...` matches origin | Authorize exactly one hash-bound V2 exec dispatcher invocation | User authorized the planned iteration; separate authorization preserves one-shot replay safety | `pre-live-authorization.v2.md` | high | applied |
