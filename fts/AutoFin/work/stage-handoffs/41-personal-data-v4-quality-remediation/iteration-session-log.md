# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `prepared-standard-v4-quality-remediation` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| started_from | `work/stage-handoffs/40-personal-data-v3-reviewer-recovery/workflow-state.yaml` |
| status_after | `blocked-input` |

## Inputs Read

- `skills/ft-test-case-iteration/SKILL.md` and `fts/AutoFin/AGENT-NOTES.md`.
- Handoff 40 workflow, next-stage prompt, V3 state/draft/findings and eval candidate.
- Handoff 38 compiler inputs and handoff 29 coverage gaps/clarifications.
- Prepared compiler, exec runner and focused regression tests.

## Inputs Not Used

- V1/V2/V3 drafts as requirement evidence or templates.
- `fts/AutoFin/test-cases/**` as prepared-package evidence.
- User-owned `evals/sdk-turn-diagnostics/**` and untracked neighboring test-case file.

## Key Decisions

- Add prevention at compiler input and post-writer draft gates.
- Preserve handoff 38 and V1-V3; build new V4 inputs under handoff 41.
- Use explicit fixture contracts and evidence-capture oracles where exact UI reaction remains unknown.
- Authorize at most one V4 live only after bad/corrected eval, regressions, context and integrity gates pass.
- Stop after the only V4r1 writer reports missing registered fixture data; do not retry or start reviewer.
- Route the successor work to fixture-catalog resolution plus a fresh V5 package.

## Risks And Fallbacks

- `GAP-001..003` remain open; remediation must not convert calibration evidence into invented product behavior.
- The first canonical lookup for `coverage-obligation-table.md` used the test-design root, but that file exists only in the handoff 38 compiler snapshot; the missing lookup produced no evidence (`TF-001`).
- The first focused runner eval omitted mandatory `unsupported_dimensions` for a `standard-required` test package; both tests stopped before writer execution and were corrected (`TF-002`).
- The first bad-draft detection assertion exposed a punctuation gap: the generic-fixture regex did not accept the comma in the exact V3 phrase; the detector was narrowed to allow only punctuation between the fixture subject and qualifier (`TF-003`).
- The third focused run exposed truncated Russian subsection literals in the new gate (`Тестовые данны`, `Итоговый ожидаемый результ`); they were corrected to exact canonical headings (`TF-004`).
- The fourth focused run then exposed the same truncated expected-result heading inside both eval fixtures; this had hidden the expected-result detector and allowed the corrected fixture to pass without exercising that section (`TF-005`).
- The first H38 rejection probe used an output path with an extra `guard-probe` level and was stopped by output-layout validation before semantic checks; it created no output (`TF-006`).
- The first remediated V4 compile exceeded the standard compiled-evidence budget by 1 018 bytes (`50 170 > 49 152`); no package was published. Repeated execution-contract wording was compacted without removing fixtures, actions, observables or gaps (`TF-007`).
- Direct validate-only splatting of dispatcher argument pairs made argparse treat the `--sandbox` value as a new option; validation stopped before configuration loading and created no attempts (`TF-008`).
- The argparse-safe direct validate-only command then omitted the dispatcher's verified-capability assertion; the runner correctly returned `blocked-configuration` before attempts (`TF-009`).
- Semantic inspection of the first successful V4 package found cross-TC intent contamination for shared atoms (`OBL-028/029` and `OBL-026`); compiler selection was corrected to the obligation's exact planned TC token before continuing.
- Post-compaction immutable-tree verification first used stale V1/V2/V3 suffixes and the parent H38 compiler directory; failed lookups were discarded and exact paths/subtree were verified (`TF-010`).
- The live writer proved that a named fixture contract without registered concrete data is still not draft-ready; the compiler currently does not resolve fixture IDs into a catalog.
- The blocked cycle declares a draft path although no draft file exists; structured writer/cycle state remains complete, but the dangling alias is runner-state debt (`TF-011`).
- A package-wide validator run wrote a 122 191-line full report after its initial output was not surfaced; the oversized debug dump was excluded and deleted, and the handoff was rechecked with the scoped canonical validator (`TF-012`).

## Validation

- Focused bad/corrected eval and compiler guards: 6 tests, pass.
- Full runner/compiler regression: 124 tests, pass in 30.355 seconds.
- Original H38 input: rejected by `undefined-execution-action` before package write.
- V4r1 package/hash/seed: pass, 42 atoms / 65 obligations / 47 TC / 3 gaps / 1 dictionary.
- Writer context: 97 507 / 131 072 bytes; reviewer conservative envelope: 126 150 / 131 072.
- Dispatcher dry-run: verified exec, no fallback.
- Pre-live checkpoint: `a9c05bb079d8f650181b4c3e474ea15ffab722d4`.
- V4r1 live: exactly one writer attempt, `blocked-input`; reviewer absent; no draft or production output.
- Performance: 17.172 seconds, 38 379 total tokens, 0 commands, 0 writer file changes.
- Scoped canonical artifact validation: 0 errors, 0 warnings, 3 source-extraction info findings.
- Final boundary check: V1/V2/V3/H38 hashes match; V4/V4r1 prepared inputs have 0 post-checkpoint diffs; one live attempt only.

## Contamination Check

- Start commit: `e6d223fc081f24c9882868be746cadeacab88782`.
- V1 tree: `47b7d7354015e7dee7de4b27d7c5f29c265dcda9`.
- V2 tree: `42b1c7a0ad29a8f19a5b09a62fc71a0ccc56a093`.
- V3 tree: `f404a7c92c6820fd292354586fd08c0e08a903c4`.
- Handoff 38 compiler-input tree: `23ada54e92b0aeb3d5736eeb664673d62c740c76`.
- Production shadow target absent.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test_case_agent/review_cycle/prepared_compiler.py` | `small code patch` | `apply_patch` | `yes` | `n/a` | `yes` |
| `scripts/codex_exec_review_cycle_runner.py` | `small code patch` | `apply_patch` | `yes` | `n/a` | `yes` |
| focused tests and `evals/prepared-execution-oracle/20260713/` | `small fixtures/tests` | `apply_patch` | `yes` | `unittest` | `yes` |
| `work/stage-handoffs/41-personal-data-v4-quality-remediation/compiler-inputs/` | `bounded derived inputs` | exact mechanical copy, then `apply_patch` remediation | `yes` | `Copy-Item` for immutable source copies | `yes` |
| `work/review-cycles/application-card-client-personal-data-shadow-v4-20260713/` | `bounded multi-file compiler output` | compiler per-file writes | `yes` | prepared compiler | `yes` |
| `work/review-cycles/application-card-client-personal-data-shadow-v4r1-20260713/` | `bounded multi-file cycle output` | compiler/runner per-file writes | `yes` | prepared compiler and exec dispatcher | `yes` |
| `work/stage-handoffs/41-personal-data-v4-quality-remediation/*.md|yaml|json` | `small bounded handoff artifacts` | `apply_patch` or owning validator/runner | `yes` | `apply_patch`; validator/runner | `yes` |
| `test-cases/14-prepared-shadow-application-card-client-personal-data.md` | `production boundary` | no write; must remain absent | `yes` | `n/a` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Skill/runtime routing | Windows PowerShell with explicit UTF-8; V4 remediation selected | this log |
| 2 | Start boundary captured | tracked tree clean; user untracked files preserved; immutable tree hashes recorded | contamination check |
| 3 | Compiler/runner audit | Generic fixture accepted as concrete and quality bundle lacked execution-oracle checks | code and V3 evidence |
| 4 | Canonical obligation lookup | Wrong root path did not exist; no content read | `TF-001` |
| 5 | Corrected input lookup | Handoff 38 compiler snapshot read with explicit UTF-8 | compiler inputs |
| 6 | First focused eval run | Three compiler tests passed; two runner tests stopped at standard-route configuration before writer | `TF-002` |
| 7 | Second focused eval run | Corrected fixture passed; bad fixture detected two of three categories because of a comma variant | `TF-003` |
| 8 | Third focused eval run | Generic fixture still absent because subsection heading literals were truncated | `TF-004` |
| 9 | Fourth focused eval run | Generic/action findings present; expected-result finding absent because eval fixture headings were truncated | `TF-005` |
| 10 | First H38 compiler guard probe | Blocked by invalid output-root layout; no output directory created | `TF-006` |
| 11 | Corrected H38 guard probe | Original input rejected as `undefined-execution-action` at `PLAN-022`; no output | compiler diagnostic |
| 12 | First V4 compile | Blocked by compiled-evidence budget, actual 50 170 bytes | `TF-007` |
| 13 | Compacted V4 compile | Built, 65 obligations / 3 gaps / 1 dictionary; evidence 46 376 bytes | V4 package |
| 14 | Compiled obligation inspection | Shared-atom obligations contained sibling TC intents | compiler mapping correction |
| 15 | V4r1 compile | Built after exact TC-row compiler correction; affected 11 obligations inspected clean | V4r1 package |
| 16 | First direct validate-only | Argparse rejected option-looking flag value; no attempts created | `TF-008` |
| 17 | Second direct validate-only | CLI contract assertion missing; runner blocked before attempts | `TF-009` |
| 18 | Third validate-only | `validated`; writer context 97 507 bytes; no attempts | validate-only report |
| 19 | Full targeted regression | 124 tests pass | pre-live test report |
| 20 | Dispatcher dry-run | Verified exec selected, contract v2, no fallback | V4r1 backend selection dry-run |
| 21 | Pre-live decision | All bounded conditions pass; one live allowed after checkpoint | pre-live authorization |
| 22 | Pre-live checkpoint | Whitelist-only commit created before live | `a9c05bb079d8f650181b4c3e474ea15ffab722d4` |
| 23 | Единственный V4r1 live | Writer вернул `blocked-input` по `FIX-ACPD-SAVE-001` и `FIX-ACPD-DADATA-001`; reviewer не запускался | cycle state; writer result |
| 24 | Post-live stop | Retry запрещён; создан fixture-registration/V5 handoff | stop gate; next-stage prompt |
| 25 | Canonical handoff validation | 0 errors, 0 warnings; three inherited source-quality info findings | `validate_agent_artifacts.py` |
| 26 | Final integrity boundary | Immutable hashes match; prepared inputs unchanged; one attempt; reviewer/production absent | contamination check |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| V3 failure mapping | pass | 4 findings / 11 obligations / 9 TC | implement bounded gates |
| Bad fixture detection | pass | three exact error IDs | retain regression |
| Corrected fixture | pass | accepted-not-promoted simulated cycle | retain regression |
| V4r1 package | pass | hash/budget/intent inspection | checkpoint before live |
| V4r1 live | blocked-input | one writer attempt; reviewer absent; production absent | register safe fixtures and build fresh V5; no V4r1 retry |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Canonical test-design root has no top-level `coverage-obligation-table.md` | `Get-Content` from the assumed canonical root | Read handoff 38 compiler snapshot with `Get-Content -Encoding UTF8` | `n/a` | `n/a` | none; failed lookup returned no content, distorted stdout not used as evidence, and only explicit UTF-8 reread informed analysis | Use workflow-state artifact paths rather than inferred filenames |
| `TF-002` | Focused standard-route unit fixtures omitted required unsupported-dimension routing metadata | Build `standard-required` package with empty dimensions | Add explicit test-only unsupported dimensions matching each route | focused unit tests | `yes` | none; runner rejected configuration before starting a writer request | Rerun all five focused tests |
| `TF-003` | Exact V3 generic fixture contains a comma after `заявки` | Regex requiring whitespace only | Allow comma/semicolon/colon at that exact boundary | bad eval fixture | `yes` | low; change remains bounded to a known phrase shape | Require all three expected finding IDs on rerun |
| `TF-004` | New quality gate used truncated subsection headings | Extract `Тестовые данны` and shortened expected-result heading | Match exact canonical headings `Тестовые данные` and `Итоговый ожидаемый результат` | focused eval fixture | `yes` | none; focused eval prevented promotion of the faulty detector | Rerun all five focused tests |
| `TF-005` | Both new eval fixtures used the same shortened expected-result heading | Parse fixtures that never exposed an expected-result subsection | Correct both fixtures to the canonical heading before rerun | both eval fixtures | `yes` | none after correction; the false-positive corrected pass is discarded | Require bad finding and corrected pass with exact headings |
| `TF-006` | H38 rejection probe output included an extra directory below the cycle | `<cycle>/guard-probe/<package-id>` | Use a dedicated probe cycle with canonical `<cycle>/prepared-input/<package-id>` layout | `n/a` | `n/a` | none; compiler stopped before writing output | Rerun and require semantic diagnostic rather than layout diagnostic |
| `TF-007` | Remediated execution details expanded compiled evidence beyond the 49 152-byte standard budget | First verbose V4 plan/oracle wording | Compact repeated contracts into stable fixture/action/evidence tokens while preserving exact fields and limitations | V4 compiler inputs | `yes` | medium; requires semantic inspection of compiled obligations after successful build | Require package budget pass and verify all 11 affected obligations |
| `TF-008` | PowerShell splatted `--sandbox-flag`, `--sandbox` as separate tokens in a direct argparse invocation | Reuse dispatcher argument array verbatim with `--validate-only` | Use argparse-safe `--option=--value` syntax for option-looking flag values | `n/a` | `n/a` | none; parser stopped before runner configuration and no attempt artifacts exist | Rerun validate-only and require JSON status `validated` |
| `TF-009` | Direct runner invocation did not inherit the dispatcher's exec capability assertion | Run argparse-safe command without `--cli-contract-verified` | Add the verified flag set already proven by dispatcher capability preflight | `n/a` | `n/a` | none; runner stopped before attempts | Require validate-only `status=validated`; live still goes through dispatcher |
| `TF-010` | Post-compaction immutability probe used stale date suffixes and the parent H38 compiler directory | `git rev-parse` against non-existent V1/V2/V3 paths and parent H38 tree | Enumerate actual directories, then verify V1/V2/V3 and exact H38 package subtree | `n/a` | `n/a` | none; failed lookups were not used as evidence | Preserve corrected hashes in final validation |
| `TF-011` | Blocked-input cycle state declared a draft path although writer emitted no draft | Read the declared `stage-output/draft.md` | Read structured `writer-result.json`, `stage-status.json` and cycle state; record dangling path as runner-state debt | performance analysis | `yes` | low; blocker text and terminal state are complete and consistent | Add a separate runner-state regression in a later bounded iteration |
| `TF-012` | Package-wide validator output was too large for a bounded handoff and appeared after the initial command output was not surfaced | Retain `artifact-validation.full.json` under handoff 41 | Delete the transient full dump and run the canonical validator against handoff 41 with audit/strict log policies | `n/a` | `no` | none; the full dump was not used as scoped-pass evidence | Retain the scoped 0-error/0-warning result in Validation/Event Timeline only |

## Handoff Notes For Next Session

- Do not run, resume or mutate V4/V4r1; the single allowed V4r1 attempt is consumed.
- Register safe fixtures and add compiler catalog resolution before creating V5.
- Do not resume V3 or promote any unsigned draft.
