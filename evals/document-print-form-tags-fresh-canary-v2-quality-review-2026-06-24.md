# Fresh canary v2 quality review: document print form tags

## Scope

- Date: `2026-06-24`
- FT package: `ft-2-OF_17`
- Review cycle: `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags-fresh-canary-v2/`
- Canonical test cases: `fts/ft-2-OF_17/test-cases/2-1-1-1-1-4-4-document-print-form-tags-fresh-canary-v2.md`
- Split test design: `fts/ft-2-OF_17/work/test-design/2-1-1-1-1-4-4-document-print-form-tags-fresh-canary-v2/`
- Runner command used for terminal verification: `.venv\Scripts\python.exe scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\document-print-form-tags-fresh-canary-v2\cycle-state.yaml`

## Result

The fresh canary v2 reached terminal `signed-off`.

Key terminal evidence:

- `cycle-state.yaml`: terminal status is `signed-off`; no runnable next session remains.
- `codex_review_cycle_runner.py validate`: `valid = true`, `terminal_validator_gate.checked = true`, `scoped_findings_count = 2`, `blocking_unwaived_count = 0`.
- `semantic-regression-final-findings.md`: semantic regression passed after final format review.
- `semantic-review-r2-findings.md`: R2 semantic review has `0 error`, `0 warning`, `0 info`.
- `coverage-metrics.md`: `52` atoms covered by `16` canonical test cases; `GAP-001` and `GAP-002` remain explicit residual uncertainty, not executable coverage.

## Test Design Quality

The produced set is a strong positive signal for a table/document-generation scope:

- The final canonical file contains `TC-DPFT-001` through `TC-DPFT-016`.
- R1 semantic review found three real issues and R2 closed all three:
  - unsupported inverse branch oracle for `<previous_full_name>` was removed from executable coverage and retained as `GAP-002`;
  - `TC-DPFT-004` now directly traces `ATOM-011`;
  - coverage metrics and writer self-check were synchronized with the actual 16-case canonical set.
- The agent avoided inventing a deterministic exact template value where DOCX and PDF source extracts disagree; `GAP-001` remains visible.
- The final semantic regression confirmed no semantic drift after format review.

## Guardrail Regression Checks

The canary exercised the current runner/reviewer guardrails:

- Terminal scoped validator gate checked active-scope artifacts and did not block on historical package noise.
- Writer/reviewer artifacts kept residual `GAP-001` and `GAP-002` visible across canonical TC summary, coverage map, coverage metrics, Package Test Design Plan and applicability matrix.
- The reviewer did not normalize source ambiguity into a fake executable assertion.
- R2 matrix reports `52 covered`, `0 gap`, `2 unclear`; this is the correct outcome for current source quality.

## Residual Risks

- Two source/input ambiguities remain by design:
  - `GAP-001`: DOCX/PDF mismatch for exact generated-template value.
  - `GAP-002`: no source-backed observable mechanism for the inverse `<previous_full_name>` dependency when `Клиент менял ФИО != Да`.
- Runner lifecycle was not fully clean during the canary. There were stale-lock recoveries around child sessions; this is an execution-stability issue and should be fixed before broad canary scaling.
- Running through system `python` can fail because `openai-codex` is not installed there. Real SDK runs should use `.venv\Scripts\python.exe`, and the runner must fail before lock acquisition when the SDK runtime is unavailable.
- Some reviewer Markdown evidence contains mojibake in Russian explanatory cells. The final decision did not rely on distorted stdout or mojibake cells as source evidence, but artifact encoding still needs a stricter guard.

## Recommendation

Treat this canary as a positive quality signal, not as permission for full-scale generation yet.

Next mandatory work before a larger test-case writing pilot:

- harden runner SDK preflight, lock/recover-only and child timeout behavior;
- make scoped validator profile flow the canonical terminal gate path;
- add an encoding/mojibake regression check for reviewer artifacts;
- run one more canary on a different scope shape and compare metrics uniformly against this run.
