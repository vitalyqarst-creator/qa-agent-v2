# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `prepared-standard-full-scope-recovery-v2` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| started_from | `work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/workflow-state.yaml` |
| status_after | `ready-for-next-stage` |

## Inputs Read

- `skills/ft-test-case-iteration/SKILL.md` — lifecycle и separate-session guardrails.
- `fts/AutoFin/AGENT-NOTES.md` — package-specific context.
- Handoff 38 workflow, recovery prompt и stop gate — V2 recovery contract.
- Handoff 38 compiler-input directory — immutable deterministic V2 inputs.
- Session lifecycle, orchestration, workflow-state, handoff, session-log и decision-log references — canonical process contract.

## Inputs Not Used

- V1 blocked draft — не используется как requirement evidence и не переносится в V2 writer output.
- Production `fts/AutoFin/test-cases/**` — не используется как evidence и не изменяется.
- `evals/sdk-turn-diagnostics/**` и соседние FT packages — вне текущего scope.

## Key Decisions

- Создать новый immutable V2 cycle/package; V1 не продолжать и не исправлять на месте.
- Повторно использовать уже проверенные compiler inputs без generic input-preparation agent.
- Выполнить ровно один dispatcher live без SDK fallback, promotion и overwrite.
- Полный журнал решений: `agent-decision-log.md`.

## Risks And Fallbacks

- Seed order подтверждён live writer, но semantic reviewer не запускался из-за context-budget blocker.
- `GAP-001..003` остаются non-blocking calibration/evidence risks.
- Runtime probe показал cp1251 stdout и искажённую Cyrillic probe; все русские файлы перечитываются с явным UTF-8, искажённый stdout не используется как evidence.
- Pre-fix V2 `cycle-state.yaml` противоречит завершённому writer result; он сохранён неизменным и quarantined отдельным machine-readable warning.

## Validation

- V2 compile: 65 obligations, 3 gaps, 1 dictionary reference; `standard-required`.
- Numeric seed preflight: 47 TC, exact `TC-ACPD-001..047`, pass.
- Targeted runner/compiler regression: 117 tests, pass.
- Validate-only: pass; writer context 96 886 / 131 072 bytes; production target absent.
- Exec capability dry-run: verified, contract v2, no fallback.
- V2 live writer: 47 ordered TC; structure, 65/65 obligations, quality, overlap, seed and evidence gates pass.
- V2 reviewer preflight: blocked at 183 402 / 131 072 bytes; reviewer session not launched.
- Post-fix reviewer transport replay: 117 439 / 131 072 bytes, pass.
- Post-fix targeted runner/compiler regression: 118 tests, pass.
- Agent-layer-fast: 421 pass, 1 skip.
- Architecture: 61 checks, 0 findings.
- Scoped artifact validator: pass, 0 findings for handoff 39 / V2 cycle across 12 978 checks. The full AutoFin package still has 78 errors and 2 640 warnings inherited outside this scope.
- Independent consistency audit: one P2 stale-state finding mitigated by `v2-cycle-integrity-warning.yaml`; all links, hashes, gates and boundaries otherwise match evidence.

## Contamination Check

- V1 cycle, production test cases и пользовательские untracked artifacts остались неизменными.
- Новые runtime writes ограничены V2 cycle и handoff 39; V2 reviewer attempt отсутствует.
- Production shadow target отсутствует после live.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/review-cycles/application-card-client-personal-data-shadow-v2-20260713/prepared-input/application-card-client-personal-data-v2/` | `bounded compiler output` | deterministic per-file compiler writes | `yes` | `scripts/compile_prepared_stage_package.py` | `yes` |
| `work/review-cycles/application-card-client-personal-data-shadow-v2-20260713/attempts/` | `bounded immutable runtime output` | exec runner per-file writes | `yes` | `scripts/codex_exec_review_cycle_runner.py` | `yes` |
| `work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/*` | `small structured` | `apply_patch` | `yes` | `n/a` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Runtime probe | Windows/PowerShell confirmed; cp1251 stdout detected | `scripts/probe_environment.py`; `TF-001` |
| 2 | Skill and recovery inputs read | V2 boundary and stop conditions confirmed | handoff 38; canonical references |
| 3 | V2 write strategy declared | New cycle only; no baseline write | this log |
| 4 | V2 package compiled | 65 obligations, 3 gaps, 1 dictionary reference | V2 `stage-package.json` |
| 5 | Seed preflight first helper expression | Regex escaping returned no IDs; result discarded | `TF-002` |
| 6 | Seed preflight corrected | Exact numeric sequence `001..047` confirmed | `seed-preflight-report.v2.json` |
| 7 | Validate-only and exec dry-run | Both pass; no fallback; target absent | `validate-only-report.v2.json`; backend selection |
| 8 | Single V2 dispatcher live | Writer passes all gates; reviewer blocked before launch at 183 402 bytes | V2 cycle; `reviewer-context-blocker-report.md` |
| 9 | Reviewer transport remediation | Context reduced to 117 439 bytes; state persistence hardened | commit `15889ad`; remediation report |
| 10 | Full regression | 421 pass, 1 skip; architecture 61/0 | project test runners |
| 11 | Scoped artifact validation | Initial TF-001 wording warning fixed; rerun has 0 findings in handoff 39 / V2 | `scripts/validate_agent_artifacts.py` |
| 12 | Final artifact inventory | Unsupported legacy .NET relative-path helper was discarded; inventory completed with repository-native/file APIs | `TF-004`; `rg --files`; Python `pathlib` |
| 13 | Independent consistency audit | Stale V2 machine state quarantined without modifying V2; V3 remains the only allowed continuation | `v2-cycle-integrity-warning.yaml`; `DEC-009` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Compiler mapping | pass | 65 obligations / 47 planned TC from unchanged inputs | none |
| Numeric seed order | pass | `seed-preflight-report.v2.json` | none |
| Writer live | pass | 47 ordered TC; all deterministic gates pass | none |
| Reviewer live | blocked | preflight 183 402 > 131 072; no session started | new V3 cycle after code fix |
| Reviewer transport replay | pass | 117 439 / 131 072 bytes | confirm in V3 live |
| Production boundary | pass | target absent before and after live | retain no-promotion config |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Runtime probe printed Cyrillic through cp1251 as mojibake | Default console decoding | Set `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` and re-read source files using `Get-Content -Encoding UTF8` | `scripts/probe_environment.py` | `yes` | `none`; distorted stdout was discarded and was not used as evidence for analysis or traceability | Continue explicit UTF-8 reads/writes |
| `TF-002` | Inline seed-check regex was over-escaped and returned an empty ID list | Regex extraction in a nested command string | Extract canonical heading lines with `splitlines()` and compare the exact 47-ID array | `seed-preflight-report.v2.json` | `yes` | `none`; failed read-only result was discarded before live | Keep the regression test and saved passing report |
| `TF-003` | Reviewer prompt exceeded the hard context budget after writer completion | Full obligations and calibration lifecycle duplicated inside compact reviewer prompt | Replace duplicated payloads with digest-bound exact indexes and preserve immutable V2 as blocker evidence | `reviewer-context-remediation-report.md` | `yes` | `post-fix reviewer not live-confirmed` | Compile a new V3 package/cycle; do not resume V2 |
| `TF-004` | Legacy PowerShell/.NET runtime did not provide `System.IO.Path.GetRelativePath` during a read-only artifact inventory | PowerShell relative-path formatting helper | Discard failed formatting output; enumerate with `rg --files` and calculate counts using Python `pathlib` | `iteration-session-log.md` | `yes` | `none`; failed output was not used as evidence | Keep runtime-compatible inventory commands |
| `TF-005` | Legacy PowerShell did not support `Get-Date -AsUTC` while timestamping the integrity warning | PowerShell `Get-Date -AsUTC` | Use `[DateTime]::UtcNow.ToString('o')` | `v2-cycle-integrity-warning.yaml` | `yes` | `none`; failed command produced no timestamp evidence | Keep runtime-compatible UTC timestamp helper |

## Handoff Notes For Next Session

- V2 is not accepted; its writer draft is unsigned regression evidence only.
- Read `v2-cycle-integrity-warning.yaml`; do not trust the raw stale V2 cycle state as resumable process status.
- Do not reuse or mutate V1/V2 cycles.
- Start V3 only from commit `15889ad` or later and require reviewer `accepted`.
- Broader input-preparation optimization remains conditional on an accepted V3 full cycle.
