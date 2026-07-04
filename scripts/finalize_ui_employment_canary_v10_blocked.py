from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v10-agent-gate-regression"
TD = FT / "work" / "test-design" / SCOPE
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
REL_TC = "test-cases/2-1-1-1-1-2-ui-employment-canary-v10-agent-gate-regression.md"


FINDINGS = [
    ("artifact-write-strategy-unsafe-or-vague", "warning", REL_TC, "Canonical artifact strategy is still too vague for validator."),
    ("coverage-obligation-table-no-table", "warning", REL_TC, "Validator does not find canonical coverage obligation table in accepted shape."),
    ("source-row-inventory-no-table", "warning", REL_TC, "Validator does not find canonical source-row inventory in accepted shape."),
    ("test-case-requiredness-without-empty-or-marker-check", "warning", REL_TC, "Validator flags TC-007, TC-013, TC-026, TC-030 requiredness parsing."),
    ("test-case-split-artifact-duplicated-sections", "warning", REL_TC, "Canonical file duplicates split artifact sections."),
    ("test-design-review-missing-columns", "warning", REL_TC, "Test Design Review table lacks canonical columns."),
    ("test-design-review-missing-required-items", "warning", REL_TC, "Test Design Review lacks required review items."),
    ("test-design-review-no-table", "warning", REL_TC, "Validator does not parse Test Design Review as canonical table."),
    ("writer-quality-gate-failed", "warning", REL_TC, "Writer gate is failing by design after current validator findings."),
    ("writer-quality-gate-invalid-blocks-value", "warning", REL_TC, "Initial gate used invalid blocking flag semantics."),
    ("writer-quality-gate-invalid-status", "warning", REL_TC, "Initial gate used noncanonical statuses."),
    ("writer-quality-gate-missing-columns", "warning", REL_TC, "Gate lacks affected_package/required_action columns."),
    ("writer-quality-gate-missing-required-items", "warning", REL_TC, "Gate lacks required regression gate rows."),
]


def table(headers: list[str], rows: list[list[str] | tuple[str, ...]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out.extend("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join(out)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def finding_table() -> str:
    return table(
        ["finding_id", "severity", "path", "evidence_summary", "writer_disposition"],
        [[f"`{fid}`", sev, f"`{path}`", summary, "`unresolved-current-scope-blocker`"] for fid, sev, path, summary in FINDINGS],
    )


def main() -> int:
    gate_rows = [
        ["instruction-context", "pass", "Resolver completed: `pass (129.6 / 200.0 KiB)`.", "all", "none", "no"],
        ["required-inputs-read", "pass", "All selected required instruction files and v10 handoff inputs read.", "all", "none", "no"],
        ["artifact-write-strategy", "fail", "`artifact-write-strategy-unsafe-or-vague` remains current-scope validator warning.", "all", "Rewrite strategy evidence to canonical validator shape.", "yes"],
        ["source-row-inventory", "fail", "`source-row-inventory-no-table` remains current-scope validator warning.", "all", "Rewrite inventory to canonical parser shape or remove duplicate canonical section.", "yes"],
        ["coverage-obligation-table", "fail", "`coverage-obligation-table-no-table` remains current-scope validator warning.", "all", "Rewrite obligation table to canonical columns.", "yes"],
        ["test-design-review", "fail", "Missing canonical columns/items and parseable table warnings remain.", "all", "Rewrite Test Design Review to canonical format.", "yes"],
        ["tc-requiredness", "fail", "`test-case-requiredness-without-empty-or-marker-check` remains current-scope validator warning.", "WP-01; WP-02; WP-03; WP-04", "Revise requiredness TCs or add valid waiver evidence.", "yes"],
        ["writer-quality-gate", "fail", "Gate table itself has validator warnings and cannot be considered pass.", "all", "Rewrite gate with canonical columns/items/statuses.", "yes"],
        ["scoped-validator-findings", "fail", "13 current-scope warnings remain unresolved; no waiver recorded.", "all", "Keep cycle `blocked-input`.", "yes"],
    ]
    write(
        TD / "writer-quality-gate.md",
        "# Writer Quality Gate\n\n## Writer Quality Gate\n\n"
        + table(["item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows)
        + "\n\n## Current-Scope Validator Findings\n\n"
        + finding_table(),
    )

    write(
        TD / "writer-self-check.md",
        "# Writer Self-Check\n\n## Validation Command\n\n"
        "`python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_16 --json --session-log-policy audit --decision-log-policy strict`\n\n"
        "Filtered current-scope validator evidence was collected by parsing the JSON output for paths/evidence containing "
        f"`{SCOPE}` or `{REL_TC}`.\n\n"
        "## Result\n\n"
        "`blocked-input`: current-scope validator warnings remain unresolved, so writer-r1 must not advance to `writer-draft-ready`.\n\n"
        "## Current-Scope Findings\n\n"
        + finding_table()
        + "\n\n## Writer Disposition\n\n"
        "- No validator waiver is claimed.\n"
        "- `Writer Quality Gate` is `fail` because `scoped-validator-findings` is not clean.\n"
        "- The cycle remains blocked for writer remediation instead of routing to reviewer.\n",
    )

    write(
        OUT / "writer-session-log.writer-r1.md",
        "# Writer Session Log\n\n## Session Metadata\n\n"
        + table(
            ["field", "value"],
            [
                ["skill", "`ft-test-case-writer`"],
                ["mode", "`fresh-eval-run / writer.session_initial_draft`"],
                ["ft_slug", "`ft-2-OF_16`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["started_from", f"`work/review-cycles/{SCOPE}/cycle-state.yaml`"],
                ["status_after", "`blocked-input`"],
            ],
        )
        + "\n\n## Inputs Read\n\n"
        "- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.\n"
        "- Resolver budget status: `pass (129.6 / 200.0 KiB)`.\n"
        "- Selected required instruction files: `AGENTS.md`; `skills/README.md`; `references/agent/session-based-review-cycle-format.md`; `references/agent/codex-sdk-orchestration-format.md`; `skills/ft-test-case-writer/SKILL.md`; `references/agent/writer-runtime-workflow.md`; `references/agent/writer-runtime-contract.md`; `references/qa/test-case-runtime-format.md`; `references/qa/coverage-runtime-checklist.md`; `references/qa/traceability-rules.md`; `references/agent/writer-process-workflow.md`; `references/agent/workflow-state-format.md`; `references/agent/session-log-format.md`; `references/agent/agent-decision-log-format.md`; `references/agent/writer-handoff-format.md`.\n"
        "- Source/scope inputs: `AGENT-NOTES.md`; source selection; scope contract; coverage gaps; parity check; source-row inventory; mockup visual inventory; clarification requests; accepted scope-gap review findings; dictionary inventory; DOCX table 11 and table 12 extraction.\n\n"
        "## Inputs Not Used\n\n"
        "- Existing canary v1-v9 artifacts - excluded as requirement sources/templates.\n"
        "- Neighboring FT packages - out of selected package.\n\n"
        "## Key Decisions\n\n"
        "- Produced a fresh v10 medium-scope draft and split artifacts.\n"
        "- Preserved gap/context rows without routing them to executable standalone TC.\n"
        "- Stopped before reviewer handoff because current-scope validator warnings remain.\n\n"
        "## Risks And Fallbacks\n\n"
        "- Initial PowerShell stdout for Russian files displayed mojibake; sources were reread through explicit UTF-8 reads or DOCX path-glob extraction, and distorted stdout was not used as source evidence.\n\n"
        "## Validation\n\n"
        "- `python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_16 --json --session-log-policy audit --decision-log-policy strict` - executed; filtered current-scope warnings recorded in `writer-self-check.md`.\n"
        "- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v10-agent-gate-regression/cycle-state.yaml` - executed before final blocker update; state shape validated in blocked status.\n\n"
        "## Contamination Check\n\n"
        "- Broad `rg` surfaced old canary files, but they were excluded from requirement/source/template use after detection.\n\n"
        "## Event Timeline\n\n"
        + table(
            ["step", "event", "result", "artifact_or_evidence"],
            [
                ["1", "Resolved instruction context", "budget pass", "resolver output"],
                ["2", "Read required inputs", "scope confirmed", "handoff artifacts"],
                ["3", "Generated artifacts", "canonical and split files written", f"`work/test-design/{SCOPE}`; `{REL_TC}`"],
                ["4", "Ran validator", "current-scope warnings found", "`writer-self-check.md`"],
                ["5", "Routed state", "`blocked-input`", "`cycle-state.yaml`"],
            ],
        )
        + "\n\n## Quality Checkpoints\n\n"
        + table(
            ["checkpoint", "status", "evidence", "follow_up"],
            [
                ["Writer Quality Gate", "fail", "13 current-scope warnings", "writer remediation required"],
                ["Scoped validator findings", "fail", "`writer-self-check.md`", "do not start reviewer"],
                ["Cycle-state handoff", "blocked", "`blocked-input`", "runner stops"],
            ],
        )
        + "\n\n## Artifact Write Strategy\n\n"
        + table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [[REL_TC, "large generated", "file-based manifest write", "yes", "scripts/write_artifact_sections.py --manifest <manifest.json>", "yes"]],
        )
        + "\n\n## Technical Fallbacks\n\n"
        + table(
            ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
            [["`TF-001`", "Cyrillic stdout/path encoding issue", "PowerShell default stdout / literal Cyrillic path in inline Python", "Explicit UTF-8 reads and DOCX path glob extraction; distorted stdout discarded and not used as evidence", "n/a", "n/a", "none", "none"]],
        )
        + "\n\n## Handoff Notes For Next Session\n\n"
        "- This stage intentionally stops at `blocked-input`; reviewer must not be started until writer remediation resolves or validly waives the current-scope findings.\n",
    )

    write(
        OUT / "agent-decision-log.writer-r1.md",
        "# Agent Decision Log\n\n## Decision Log Metadata\n\n"
        + table(
            ["field", "value"],
            [["ft_slug", "`ft-2-OF_16`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", "`cycle-state.yaml`"]],
        )
        + "\n\n## Decision Log\n\n"
        + table(
            ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
            [
                ["`DEC-001`", "1", "`scope-boundary`", "`prompt.writer-r1.md`", "Use v10 medium scope only.", "Prompt excludes full section rerun.", "canonical and split artifacts", "high", "applied"],
                ["`DEC-002`", "2", "`coverage`", "`scope-gap-review-findings.md`", "Keep `GAP-001`-`GAP-004` as non-blocking residual gaps.", "Prior gap review accepted them.", "`coverage-gaps.md`", "high", "applied"],
                ["`DEC-003`", "3", "`validation`", "current-scope validator warnings", "Do not advance to reviewer.", "Writer gate cannot pass with unresolved current-scope warnings.", "`writer-self-check.md`; `cycle-state.yaml`", "high", "applied"],
                ["`DEC-004`", "4", "`routing`", "Writer Quality Gate failed", "Set `stage_status: blocked-input`.", "This is the only valid outcome without fixes/waivers.", "`cycle-state.yaml`", "high", "applied"],
            ],
        ),
    )

    blocking = [f"{fid} at {path}" for fid, _sev, path, _summary in FINDINGS[:8]]
    state = f"""cycle_id: ft-2-OF_16-ui-employment-canary-v10-agent-gate-regression
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: 2.1.1.1.1.2
current_stage: writer-r1
stage_status: blocked-input
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: {REL_TC}
test_design_dir: work/test-design/{SCOPE}
active_snapshot: none
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.writer-r1.md
sessions: []
latest_artifacts:
  - canonical_test_cases={REL_TC}
  - test_design_dir=work/test-design/{SCOPE}
  - writer_session_log=work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - decision_log=work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - writer_self_check=work/test-design/{SCOPE}/writer-self-check.md
  - writer_quality_gate=work/test-design/{SCOPE}/writer-quality-gate.md
blocking_reasons:
"""
    state += "\n".join(f"  - {item}" for item in blocking) + "\n"
    state += """blocking_findings:
"""
    state += "\n".join(f"  - {fid}" for fid, _sev, _path, _summary in FINDINGS) + "\n"
    state += """open_questions:
  - GAP-001
  - GAP-002
  - GAP-003
  - GAP-004
  - GAP-V10-001
  - GAP-V10-002
  - GAP-V10-003
  - GAP-V10-004
  - GAP-V10-005
accepted_risks:
  - Canary v10 is a medium agent-gate regression over the same selected employment UI rows as v9; it must not optimize for target test-case count or compactness.
  - Existing canary v1-v9 test cases and generated artifacts are regression comparison material only, not requirement sources or templates.
  - GAP-001 through GAP-004 remain accepted non-blocking pre-writer residual gaps by prior scope-gap review evidence unless new source evidence closes them.
"""
    write(CYCLE / "cycle-state.yaml", state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
