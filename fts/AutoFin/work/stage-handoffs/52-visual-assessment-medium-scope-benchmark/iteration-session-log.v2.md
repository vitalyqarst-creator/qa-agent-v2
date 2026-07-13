# Medium-Scope Benchmark V2 Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `one-shot prepared exec benchmark v2` |
| ft_slug | `AutoFin` |
| scope_slug | `visual-assessment-medium-scope-benchmark` |
| started_from | `work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/prompt.iteration-to-dictionary-projection-remediation.md` |
| status_after | `ready-for-live-authorization` |

## Inputs Read

- `AGENT-NOTES.md` and the active H52 workflow, scope, parity, row, oracle and decision artifacts.
- V1 immutable package, draft, findings and performance only as benchmark-comparison evidence.
- V2 compiler input, package v7, atomic obligations, protocol and dispatcher config.
- Canonical workflow, decision-log, session-log and runtime-environment policies.

## Inputs Not Used

- Existing production visual-assessment test cases were used only for SHA-256 protection, not as requirement evidence.
- User-owned untracked `test-cases/4.3-application-card-client-addresses-contacts.md` was not read or modified.
- User-owned `evals/sdk-turn-diagnostics/**` was not read, staged or modified.
- No V1 draft or reviewer wording was copied into V2 source evidence or package inputs.

## Key Decisions

- Continue H52 instead of creating a competing workflow-state for the same `scope_slug`.
- Preserve the exact V1 scope and performance protocol while changing only the prepared-package/runtime contracts under test.
- Remove hard-coded package version from the writer runtime profile; package-version ownership belongs to the runner.
- Require an immutable pushed checkpoint and a separate hash-bound authorization before one live invocation.

## Risks And Fallbacks

- V1 failed semantic review because complete dictionary values were not materialized; V2 must prove both deterministic and semantic closure.
- V1 lost two source-backed calibration candidates; V2 must preserve them without inventing UI behavior.
- PowerShell/Python console uses cp1251; all important Russian artifacts were read with explicit UTF-8 and distorted probe stdout was not used as evidence.
- A live result can still expose a semantic gap not covered by deterministic gates; the one-shot terminal rule intentionally preserves that evidence.

## Validation

- Package compiler: version 7, 13 obligations, 12 planned TC, 9 dictionary references, zero active gaps.
- Validate-only: runtime identity, context/output capacity and 13/13 observable oracles passed; no attempt created.
- Exec dry-run: contract v2 selected, capability verified, no missing flags, no SDK fallback.
- Full agent-layer suite: 460 passed, 1 skipped.
- Focused prepared/compiler/runner/backend suite: 242 passed.
- Architecture audit: 7 skills, 61 checks, zero findings, all budgets pass.
- Six dictionary/calibration negative-mutation regressions passed.
- Three protected baseline hashes unchanged; promotion target absent.

## Contamination Check

- V2 has no live attempt, cycle state, writer draft or reviewer findings before authorization.
- Package source registry contains only the current AutoFin DOCX/XHTML/PDF family.
- V1 output is comparison evidence only and is not listed as V2 source evidence.
- User-owned untracked files remain outside the staged write set.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Restored missing validator fixture and isolated diagnostic output | full suite green; no repository pollution | commit `f91b476` |
| 2 | Confirmed H52 continuation rule | no competing workflow-state created | `workflow-state.yaml` |
| 3 | Compiled V2 immutable package | v7; 13 OBL; 0 gaps | V2 prepared-input |
| 4 | Checked dictionary/calibration projections and negative mutations | required value counts and calibration markers enforced | regression tests |
| 5 | Ran exec capability dry-run | exec selected; fallback false | `backend-selection.dry-run.json` |
| 6 | Initial validate-only exposed a stale hard-coded package version | live was not invoked | runner preflight error |
| 7 | Moved version ownership back to runner and reran validation | validate-only pass | runtime profile; regression test |
| 8 | Initial architecture command used a nonexistent generic script path | no audit result accepted from failed command | terminal error |
| 9 | Used the skill-owned canonical auditor | 61/61 checks pass | architecture audit summary |
| 10 | Initial ad-hoc unittest list contained two nonexistent modules | result rejected as operator selection error | unittest import errors |
| 11 | Used the canonical agent-layer suite | 460 passed, 1 skipped | `scripts/run_tests.py --suite agent-layer` |
| 12 | Prepared pre-live stop gate | live remains blocked pending two pushes | `pre-live-stop-gate.v2.md` |
| 13 | Pushed immutable V2 checkpoint | local/origin `8223d580...` match | Git evidence |
| 14 | Created hash-bound one-shot authorization | invocation budget `1`; live still awaits authorization push | `pre-live-authorization.v2.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Source/package identity | pass | package id/digest/fingerprint and three source hashes exact | bind in authorization |
| Dictionary projection | pass pre-live | OBL-006=47 hierarchy values; OBL-007=39 leaf values | verify writer draft and reviewer |
| Calibration lifecycle | pass pre-live | OBL-008/010 retain source-backed calibration state | verify runner lifecycle artifact |
| Deterministic regressions | pass | six positive/negative tests | preserve |
| Architecture | pass | 61 checks, zero findings | none |
| Production boundary | pass | three hashes unchanged; target absent | recheck post-live |
| Semantic reviewer | not-applicable before live | no V2 attempt exists | run once after authorization |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/stage-handoffs/52-*/**.v2.*` | `small handoff` | `bounded apply_patch` | `yes` | `apply_patch` | `yes` |
| `work/review-cycles/*-v2-*/prepared-input/**` | `bounded compiled capsule` | `canonical compiler` | `yes` | `compile_prepared_stage_package.py` | `yes` |
| `work/review-cycles/*-v2-*/attempts/**` | `runner-owned evidence` | `single authorized dispatcher` | `yes` | `review_cycle_backend_dispatcher.py` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-V2-001` | cp1251 console distorted the Cyrillic environment probe | console-rendered Cyrillic probe | explicit `Get-Content -Encoding UTF8` for important artifacts | `n/a` | `n/a` | `none: distorted stdout was discarded and never used as evidence` | preserve explicit UTF-8 reads |
| `TF-V2-002` | validate-only rejected hard-coded `package version 7` in the writer profile | version-specific instruction contract | runner validates current package metadata; profile requires digest/fingerprint without a numeric version | `n/a` | `n/a` | `none: live authorization not consumed` | regression prevents numeric package version in profile |
| `TF-V2-003` | generic architecture script path did not exist | `scripts/validate_agent_architecture.py` | skill-owned architecture audit helper | `skills/agent-architecture-auditor/scripts/audit_agent_architecture.py` | `yes` | `none: canonical helper produced the accepted result` | use skill helper first |
| `TF-V2-004` | ad-hoc unittest list named two nonexistent modules | manual module selection | canonical agent-layer suite | `scripts/run_tests.py` | `yes` | `none: failed selection was not treated as product evidence` | prefer suite aliases |

## Handoff Notes For Next Session

- Do not invoke live until checkpoint and separate authorization commits are both pushed and local/remote SHAs match.
- The first dispatcher invocation consumes V2 authorization regardless of outcome.
- Verify exact dictionary values, calibration lifecycle, reviewer verdict, performance targets and protected hashes after live.
- A second live cycle is prohibited unless one new defect is isolated, fixed and separately checkpointed/authorized.
