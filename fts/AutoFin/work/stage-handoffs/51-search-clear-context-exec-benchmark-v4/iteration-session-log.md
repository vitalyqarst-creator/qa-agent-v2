# V4 Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `runtime-contract-remediation` |
| ft_slug | `AutoFin` |
| scope_slug | `search-clear-context-exec-benchmark-v1` |
| started_from | `work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/prompt.scope-to-iteration.md` |
| status_after | `accepted-not-promoted` |

## Inputs Read

- `fts/AutoFin/AGENT-NOTES.md` — mandatory package context.
- H48 source/scope/parity/row/gap artifacts — confirmed unchanged scope and source boundary.
- H50 V3 terminal result, blocker analysis, performance and next prompt — exact protocol failure evidence.
- V3 writer prompt/stage evidence — confirmed v6 metadata, stale v5 profile and missing digest.
- Prepared package, exec orchestration and runtime-profile contracts — implementation boundary.

## Inputs Not Used

- V2 draft was not used as requirement evidence or repair input.
- Existing production test cases and the user-owned untracked section 4.3 draft were not used or modified.
- `evals/sdk-turn-diagnostics/**` was not read, staged or modified.

## Key Decisions

- Centralize package identity metadata for compact writer/reviewer prompts.
- Keep runtime eligibility version-neutral and fail numeric profile allowlists before exec.
- Reuse unchanged H50 design artifacts and compile a new immutable V4 package/cycle.
- Preserve exactly-once checkpoint and authorization boundaries.
- Route the next experiment to medium-scope scaling; do not repeat the accepted small scope.

## Risks And Fallbacks

- V4 remains a four-obligation small-scope benchmark and does not prove medium-scope scaling.
- A clean protocol preflight does not guarantee semantic reviewer acceptance.
- The saved runtime probe reports cp1251 console output; all semantic reads use explicit UTF-8.
- Token cost remains high: V4 used `10,364.5` uncached tokens per obligation.

## Validation

- Exec runner suite after contract remediation: `105 passed`.
- Prepared package/compiler/obligation, backend and architecture group: `123 passed`.
- Prepared reviewer/evidence/migration group: `26 passed`.
- Clean non-overlapping total: `254 passed`.
- V4 validate-only: runtime identity pass; state-change/oracle `4/4`; no attempts.
- Dispatcher dry-run: verified exec, contract v2, no fallback.
- H51 strict artifact validation: 0 errors, 0 warnings, 3 inherited source-quality info findings.
- Live writer: draft-ready, `35.078 s`, `21,533` tokens, 0 commands.
- Live reviewer: accepted `4/4`, `31.484 s`, `22,002` tokens, 0 commands.
- Fresh backend session ids differ; no retry, fallback, rebind or promotion.

## Contamination Check

- Protected baselines and absent promotion target will be checked before checkpoint and after live.
- Pre-checkpoint hashes match the protected values; promotion target is absent.
- Post-live hashes match the same protected values; promotion target remains absent.
- User-owned untracked diagnostics and section 4.3 draft remain outside the change set.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Loaded V3 terminal evidence and V4 routing | Root cause confirmed as duplicated/stale runtime identity contract | H50 blocker analysis; V3 prompt |
| 2 | Centralized writer/reviewer identity metadata | Version, id and digest now come from one runner helper | exec runner |
| 3 | Made runtime profiles version-neutral | Numeric package allowlists are rejected before attempt creation | profiles; runner preflight |
| 4 | Added cross-contract regressions | Stale v5 and missing digest block before attempt; both prompts receive exact identity | runner tests |
| 5 | Compiled immutable V4 | Package v6 with four reset obligations and new V4 identity | V4 prepared package |
| 6 | Ran validate-only and target suites | Runtime identity, state/oracle/capacity and 254 tests pass; no attempts | pre-live report |
| 7 | Verified exec dry-run and production boundary | Exec available; no fallback; baselines unchanged; target absent | dry-run; pre-live report |
| 8 | Applied pre-live stop gate | Live waits for pushed checkpoint and separate authorization | `pre-live-stop-gate.md` |
| 9 | Pushed checkpoint and verified remote equality | Local and origin SHA both `40641ad...` | Git remote evidence |
| 10 | Created separate one-shot authorization | One V4 dispatcher is permitted only after authorization push | `pre-live-authorization.md` |
| 11 | Pushed authorization and invoked dispatcher once | Writer produced four TC; reviewer accepted all four obligations | V4 cycle; `live-result.v4.json` |
| 12 | Verified runtime identity in both live prompts | Version 6, V4 id and exact digest match; no stale v5 allowlist | writer/reviewer prompts |
| 13 | Applied terminal stop gate | V4 cannot be repeated or promoted inside this benchmark | `stop-gate.md` |
| 14 | Compared V2/V3/V4 performance | Quality and latency improved; tokens per obligation did not | `performance-analysis.v4.md` |
| 15 | Prepared medium-scope successor | Next stage is scope analysis, not another small live run | `prompt.iteration-to-medium-scope.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Runtime identity single source | pass | centralized runner helper | preserve in suite |
| Stale numeric profile rejection | pass | negative runner test | include in pre-live report |
| Missing digest rejection | pass | negative runner test | include in pre-live report |
| V4 immutable package | pass | v6 package digest `5a118072...` | preserve immutable |
| Validate-only runtime identity | pass | version/id/digest exact; no numeric allowlists | preserve in report |
| Production boundary | pass | protected hashes; target absent | recheck after live |
| Live runtime identity | pass | exact version/id/digest in both prompts | none |
| Deterministic draft gates | pass | structure/seed/obligation/quality/evidence all clean | none |
| Semantic reviewer | pass | accepted `4/4`, no blocking findings | keep unsigned evidence |
| Session isolation | pass | two distinct backend session ids | none |
| Token-efficiency target | fail | `10,364.5` uncached tokens/OBL | medium-scope benchmark |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `scripts/**`, `tests/**`, `references/**` | `small targeted` | `bounded apply_patch` | `yes; announced before edits` | `apply_patch` | `yes` |
| `work/stage-handoffs/51-*/**` | `small handoff` | `bounded apply_patch` | `yes` | `apply_patch` | `yes` |
| `work/review-cycles/*-v4-*/prepared-input/**` | `small bounded capsule` | `canonical compiler` | `yes` | `scripts/compile_prepared_stage_package.py` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |

## Handoff Notes For Next Session

- V4 is terminal `accepted-not-promoted`; its authorization is consumed and dispatcher must not run again.
- Start with `ft-scope-analyzer` using `prompt.iteration-to-medium-scope.md`.
- Preserve V4 draft/evidence and both FT-first baselines; promotion requires a separate explicit task.
- V3 must not be retried, resumed, rebound or edited.
