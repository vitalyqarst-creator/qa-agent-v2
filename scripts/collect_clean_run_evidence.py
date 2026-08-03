from __future__ import annotations

import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.validate_agent_artifacts import (  # noqa: E402
    iter_test_case_files,
    iter_workflow_states,
    parse_workflow_state,
    parsed_source_row_inventory_rows,
    rel,
    test_case_validation_content,
    validate,
)


TC_ID_RE = re.compile(r"\bTC-[A-Za-z0-9_-]+\b")
ATOM_ID_RE = re.compile(r"\b(?:[A-Z0-9-]+-)?ATOM-\d{3,}\b")
GAP_ID_RE = re.compile(r"\bGAP-\d{3,}\b")

CLEAN_RUN_EVAL_PATH = ROOT_DIR / "evals" / "ft2-of11-clean-run-regression.md"
CLEAN_RUN_PROMPT_HEADINGS = {
    "Prompt 1: Source Locator": "Prompt 1: Source Locator",
    "Prompt 2: Scope Selection": "Prompt 2: Scope Selection",
    "Prompt 3: Confirm ui-main-info": "Prompt 3: Confirm `ui-main-info`",
    "Prompt 4: Writer Pass": "Prompt 4: Writer Pass",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect read-only evidence for the FT clean-run eval report."
    )
    parser.add_argument("--root", type=Path, required=True, help="FT package root, e.g. fts/ft-2-OF_11")
    parser.add_argument("--json", action="store_true", dest="json_only")
    parser.add_argument("--markdown", action="store_true", dest="markdown_only")
    parser.add_argument("--next-prompt", action="store_true", help="Print only the next clean-run prompt text.")
    parser.add_argument("--run-report-template", action="store_true", help="Print a clean-run report template prefilled with current evidence.")
    parser.add_argument(
        "--expect-stage",
        choices=["not-started", "source-locator", "agent-proposed-scope", "confirmed-scope", "writer-pass", "unknown"],
        help="Exit non-zero unless clean_run_assessment.stage matches this value.",
    )
    parser.add_argument(
        "--expect-status",
        choices=["pending", "pass", "fail", "inconclusive"],
        help="Exit non-zero unless clean_run_assessment.status matches this value.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_run_prompt_text(prompt_name: str | None) -> str | None:
    if not prompt_name:
        return None
    heading = CLEAN_RUN_PROMPT_HEADINGS.get(prompt_name)
    if not heading or not CLEAN_RUN_EVAL_PATH.exists():
        return None
    content = read_text(CLEAN_RUN_EVAL_PATH)
    pattern = re.compile(
        rf"^###\s+{re.escape(heading)}\s*\n\s*```text\n(?P<prompt>.*?)\n```",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return None
    return match.group("prompt").strip()


def files_under(root: Path, relative_dir: str) -> list[str]:
    directory = root / relative_dir
    if not directory.exists():
        return []
    return sorted(rel(path, root) for path in directory.rglob("*") if path.is_file())


def workflow_state_summaries(root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in iter_workflow_states(root):
        state = parse_workflow_state(path)
        summaries.append(
            {
                "path": rel(path, root),
                "current_stage": state.get("current_stage"),
                "stage_status": state.get("stage_status"),
                "next_skill": state.get("next_skill"),
                "current_round": state.get("current_round"),
            }
        )
    return summaries


def test_case_metrics(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    all_atoms: set[str] = set()
    all_tcs: set[str] = set()
    all_gaps: set[str] = set()
    for path in iter_test_case_files(root):
        content = test_case_validation_content(path, root)
        atoms = set(ATOM_ID_RE.findall(content))
        tcs = set(TC_ID_RE.findall(content))
        gaps = set(GAP_ID_RE.findall(content))
        all_atoms.update(atoms)
        all_tcs.update(tcs)
        all_gaps.update(gaps)
        files.append(
            {
                "path": rel(path, root),
                "atom_count": len(atoms),
                "tc_count": len(tcs),
                "gap_count": len(gaps),
            }
        )
    return {
        "atom_count": len(all_atoms),
        "tc_count": len(all_tcs),
        "gap_count": len(all_gaps),
        "files": files,
    }


def inventory_source_rows(path: Path) -> dict[str, Any]:
    content = read_text(path)
    rows = parsed_source_row_inventory_rows(content)
    source_row_ids: list[str] = []
    required_source_row_ids: list[str] = []
    for index, row in enumerate(rows, start=2):
        source_row_id = row.get("source_row_id", "").strip() or f"row {index}"
        source_row_ids.append(source_row_id)
        in_scope = row.get("in_scope", "").strip().strip("`").lower()
        if in_scope in {"yes", "unclear"}:
            required_source_row_ids.append(source_row_id)
    return {
        "path": str(path),
        "row_count": len(source_row_ids),
        "required_row_count": len(required_source_row_ids),
        "source_row_ids": sorted(set(source_row_ids)),
        "required_source_row_ids": sorted(set(required_source_row_ids)),
    }


def source_row_inventory_metrics(root: Path) -> dict[str, Any]:
    test_design_root = root / "work" / "test-design"
    handoff_paths = (
        sorted(
            path
            for path in (root / "work").rglob("source-row-inventory.md")
            if path.is_file() and test_design_root not in path.parents
        )
        if (root / "work").exists()
        else []
    )
    writer_paths = iter_test_case_files(root)

    handoff = []
    writer = []
    handoff_required_ids: set[str] = set()
    writer_ids: set[str] = set()

    for path in handoff_paths:
        metrics = inventory_source_rows(path)
        metrics["path"] = rel(path, root)
        handoff.append(metrics)
        handoff_required_ids.update(metrics["required_source_row_ids"])

    for path in writer_paths:
        content = test_case_validation_content(path, root)
        rows = parsed_source_row_inventory_rows(content)
        source_row_ids = []
        required_source_row_ids = []
        for index, row in enumerate(rows, start=2):
            source_row_id = row.get("source_row_id", "").strip() or f"row {index}"
            source_row_ids.append(source_row_id)
            in_scope = row.get("in_scope", "").strip().strip("`").lower()
            if in_scope in {"yes", "unclear"}:
                required_source_row_ids.append(source_row_id)
        metrics = {
            "path": str(path),
            "row_count": len(source_row_ids),
            "required_row_count": len(required_source_row_ids),
            "source_row_ids": sorted(set(source_row_ids)),
            "required_source_row_ids": sorted(set(required_source_row_ids)),
        }
        if metrics["row_count"] == 0:
            continue
        metrics["path"] = rel(path, root)
        writer.append(metrics)
        writer_ids.update(metrics["source_row_ids"])

    return {
        "handoff_files": handoff,
        "writer_files": writer,
        "handoff_required_row_count": len(handoff_required_ids),
        "writer_row_count": len(writer_ids),
        "missing_handoff_source_rows_in_writer": sorted(handoff_required_ids - writer_ids),
    }


def normalized_paths(report: dict[str, Any]) -> list[str]:
    paths = report["files"]["work"] + report["files"]["test_cases"]
    return [path.replace("\\", "/") for path in paths]


def has_path_suffix(report: dict[str, Any], suffix: str) -> bool:
    normalized_suffix = suffix.replace("\\", "/").lstrip("/")
    return any(path.endswith(normalized_suffix) for path in normalized_paths(report))


def matching_path_suffixes(report: dict[str, Any], suffixes: list[str]) -> list[str]:
    normalized_suffixes = [suffix.replace("\\", "/").lstrip("/") for suffix in suffixes]
    return sorted(
        path
        for path in normalized_paths(report)
        if any(path.endswith(suffix) for suffix in normalized_suffixes)
    )


def validator_blocks_stage(report: dict[str, Any]) -> bool:
    summary = report["validator"]["summary"]
    return summary["errors_count"] > 0 or summary["warnings_count"] > 0


def assess_required_paths(report: dict[str, Any], suffixes: list[str]) -> list[str]:
    return [suffix for suffix in suffixes if not has_path_suffix(report, suffix)]


def assess_forbidden_paths(report: dict[str, Any], suffixes: list[str]) -> list[str]:
    return matching_path_suffixes(report, suffixes)


def clean_run_assessment(report: dict[str, Any]) -> dict[str, Any]:
    workflows = report["workflow_states"]
    work_files = report["files"]["work"]
    test_case_files = report["files"]["test_cases"]
    validator_summary = report["validator"]["summary"]
    reasons: list[str] = []
    required_missing: list[str] = []
    forbidden_present: list[str] = []
    next_expected_prompt = None

    if not workflows and not work_files and not test_case_files:
        return {
            "stage": "not-started",
            "status": "pending",
            "next_expected_prompt": "Prompt 1: Source Locator",
            "reasons": ["No workflow-state, work artifacts, or test-case files found."],
            "required_missing": [],
            "forbidden_present": [],
        }

    if len(workflows) != 1:
        return {
            "stage": "unknown",
            "status": "inconclusive",
            "next_expected_prompt": None,
            "reasons": [f"Expected exactly one workflow-state for clean-run assessment, found {len(workflows)}."],
            "required_missing": [],
            "forbidden_present": [],
        }

    state = workflows[0]
    current_stage = state.get("current_stage")
    stage_status = state.get("stage_status")
    next_skill = state.get("next_skill")
    stage = "unknown"
    status = "inconclusive"

    if current_stage == "ft-source-locator":
        stage = "source-locator"
        next_expected_prompt = "Prompt 2: Scope Selection"
        required_missing = assess_required_paths(
            report,
            ["source-selection.md", "source-locator-session-log.md", "agent-decision-log.md", "workflow-state.yaml"],
        )
        forbidden_present = assess_forbidden_paths(
            report,
            [
                "scope-contract.md",
                "prompt.scope-to-writer.md",
                "prompt.scope-to-iteration.md",
            ],
        ) + test_case_files
    elif current_stage == "ft-scope-analyzer" and stage_status == "blocked-input":
        stage = "agent-proposed-scope"
        next_expected_prompt = "Prompt 3: Confirm ui-main-info"
        required_missing = assess_required_paths(
            report,
            [
                "scope-options.md",
                "scope-selection-prompts.md",
                "scope-analyzer-session-log.md",
                "agent-decision-log.md",
                "workflow-state.yaml",
            ],
        )
        forbidden_present = assess_forbidden_paths(
            report,
            [
                "scope-contract.md",
                "prompt.scope-to-writer.md",
                "prompt.scope-to-iteration.md",
            ],
        ) + test_case_files
    elif current_stage == "ft-scope-analyzer" and stage_status == "ready-for-next-stage":
        stage = "confirmed-scope"
        next_expected_prompt = "Prompt 4: Writer Pass"
        required_missing = assess_required_paths(
            report,
            [
                "scope-contract.md",
                "scope-coverage-gaps.md",
                "scope-analyzer-session-log.md",
                "agent-decision-log.md",
                "workflow-state.yaml",
            ],
        )
        if not (
            has_path_suffix(report, "prompt.scope-to-writer.md")
            or has_path_suffix(report, "prompt.scope-to-iteration.md")
        ):
            required_missing.append("prompt.scope-to-writer.md or prompt.scope-to-iteration.md")
        forbidden_present = test_case_files
    elif current_stage == "ft-test-case-writer":
        stage = "writer-pass"
        next_expected_prompt = "Independent full review"
        required_missing = assess_required_paths(
            report,
            ["writer-session-log.md", "agent-decision-log.md", "prompt.writer-to-reviewer.round-1.md", "workflow-state.yaml"],
        )
        if not test_case_files:
            required_missing.append("test-cases/*.md")
        if stage_status != "ready-for-review":
            reasons.append(f"Expected writer stage_status `ready-for-review`, got `{stage_status}`.")
        if next_skill != "ft-test-case-reviewer":
            reasons.append(f"Expected writer next_skill `ft-test-case-reviewer`, got `{next_skill}`.")
        if stage_status == "signed-off":
            reasons.append("Writer pass must not set `signed-off` before independent review.")
        missing_rows = report["source_row_inventory"]["missing_handoff_source_rows_in_writer"]
        if missing_rows:
            reasons.append(
                "Writer-side Source Row Inventory is missing handoff rows: "
                + ", ".join(missing_rows)
                + "."
            )
    else:
        reasons.append(
            f"Workflow state does not match a clean-run checkpoint: current_stage=`{current_stage}`, "
            f"stage_status=`{stage_status}`."
        )

    if validator_blocks_stage(report):
        reasons.append(
            "Validator has blocking findings for clean run: "
            f"errors={validator_summary['errors_count']}, warnings={validator_summary['warnings_count']}."
        )
    if required_missing:
        reasons.append("Required artifacts are missing: " + ", ".join(required_missing) + ".")
    if forbidden_present:
        reasons.append("Artifacts from a later stage are present: " + ", ".join(forbidden_present) + ".")

    if reasons:
        status = "fail" if stage != "unknown" else "inconclusive"
    else:
        status = "pass"

    return {
        "stage": stage,
        "status": status,
        "next_expected_prompt": next_expected_prompt,
        "reasons": reasons,
        "required_missing": required_missing,
        "forbidden_present": forbidden_present,
    }


def collect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    validator_report = validate(root, session_log_policy="audit", decision_log_policy="strict")
    report = {
        "root": root.as_posix(),
        "files": {
            "work": files_under(root, "work"),
            "test_cases": files_under(root, "test-cases"),
        },
        "workflow_states": workflow_state_summaries(root),
        "test_case_metrics": test_case_metrics(root),
        "source_row_inventory": source_row_inventory_metrics(root),
        "validator": {
            "summary": validator_report["summary"],
            "finding_ids": [finding["id"] for finding in validator_report["findings"]],
            "findings": validator_report["findings"],
        },
    }
    report["clean_run_assessment"] = clean_run_assessment(report)
    report["clean_run_assessment"]["next_prompt_text"] = clean_run_prompt_text(
        report["clean_run_assessment"].get("next_expected_prompt")
    )
    return report


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["validator"]["summary"]
    assessment = report["clean_run_assessment"]
    workflow_rows = "\n".join(
        f"| `{item['path']}` | `{item['current_stage']}` | `{item['stage_status']}` | `{item['next_skill']}` |"
        for item in report["workflow_states"]
    ) or "| - | - | - | - |"
    test_metrics = report["test_case_metrics"]
    inventory = report["source_row_inventory"]
    finding_ids = ", ".join(f"`{finding_id}`" for finding_id in report["validator"]["finding_ids"]) or "`none`"
    missing_rows = ", ".join(f"`{row_id}`" for row_id in inventory["missing_handoff_source_rows_in_writer"]) or "`none`"
    assessment_reasons = "\n".join(f"- {reason}" for reason in assessment["reasons"]) or "- none"
    next_prompt_text = assessment.get("next_prompt_text")
    next_prompt_block = (
        "\n".join(["```text", next_prompt_text, "```"])
        if next_prompt_text
        else "- none"
    )

    return "\n".join(
        [
            "# Clean Run Evidence",
            "",
            f"- root: `{report['root']}`",
            f"- validator: errors `{summary['errors_count']}`, warnings `{summary['warnings_count']}`, info `{summary['info_count']}`",
            f"- finding_ids: {finding_ids}",
            f"- clean_run_stage: `{assessment['stage']}`",
            f"- clean_run_status: `{assessment['status']}`",
            f"- next_expected_prompt: `{assessment['next_expected_prompt'] or 'none'}`",
            "",
            "## Clean Run Assessment",
            "",
            assessment_reasons,
            "",
            "## Next Prompt",
            "",
            next_prompt_block,
            "",
            "## Workflow States",
            "",
            "| path | current_stage | stage_status | next_skill |",
            "| --- | --- | --- | --- |",
            workflow_rows,
            "",
            "## Test Case Metrics",
            "",
            f"- atom_count: `{test_metrics['atom_count']}`",
            f"- tc_count: `{test_metrics['tc_count']}`",
            f"- gap_count: `{test_metrics['gap_count']}`",
            "",
            "## Source Row Inventory",
            "",
            f"- handoff_required_row_count: `{inventory['handoff_required_row_count']}`",
            f"- writer_row_count: `{inventory['writer_row_count']}`",
            f"- missing_handoff_source_rows_in_writer: {missing_rows}",
        ]
    )


def comma_or_none(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "`none`"


def run_report_template(report: dict[str, Any]) -> str:
    today = date.today().isoformat()
    summary = report["validator"]["summary"]
    assessment = report["clean_run_assessment"]
    test_metrics = report["test_case_metrics"]
    inventory = report["source_row_inventory"]
    work_files = report["files"]["work"]
    test_case_files = report["files"]["test_cases"]
    finding_ids = report["validator"]["finding_ids"]
    reasons = assessment["reasons"]
    next_prompt_text = assessment.get("next_prompt_text") or ""
    workflow_states = report["workflow_states"]
    workflow_summary = (
        "; ".join(
            f"{item['path']} => {item['current_stage']} / {item['stage_status']} / {item['next_skill']}"
            for item in workflow_states
        )
        if workflow_states
        else "none"
    )

    return "\n".join(
        [
            "# Eval Run Report: ft2-of11-clean-run-regression",
            "",
            "## Metadata",
            "",
            f"- run_id: `{today}-ft2-of11-clean-run-regression`",
            f"- run_date: `{today}`",
            "- eval_file: `evals/ft2-of11-clean-run-regression.md`",
            "- eval_case: `fts/ft-2-OF_11 / ui-main-info`",
            "- mode: `manual`",
            "- reviewed_skill: `ft-source-locator`, `ft-scope-analyzer`, `ft-test-case-writer`",
            "- runner: `external Codex agent session`",
            "- source_instructions: `AGENTS.md`, `skills/*/SKILL.md`, `references/agent/*`, `references/qa/*`",
            f"- repository_state: `clean_run_stage={assessment['stage']}; clean_run_status={assessment['status']}`",
            "",
            "## Prompt Inputs Used",
            "",
            "| stage | prompt_source | prompt_modified | notes |",
            "| --- | --- | --- | --- |",
            "| source-locator | `Prompt 1` from eval | `no` | `pending` |",
            "| scope-selection | `Prompt 2` from eval | `no` | `pending` |",
            "| confirmed-scope | `Prompt 3` from eval | `no` | `pending` |",
            "| writer-pass | `Prompt 4` from eval | `no` | `pending` |",
            "",
            "## Current Evidence Snapshot",
            "",
            f"- root: `{report['root']}`",
            f"- clean_run_assessment.stage: `{assessment['stage']}`",
            f"- clean_run_assessment.status: `{assessment['status']}`",
            f"- clean_run_assessment.next_expected_prompt: `{assessment['next_expected_prompt'] or 'none'}`",
            f"- clean_run_assessment.reasons: {comma_or_none(reasons)}",
            f"- clean_run_assessment.next_prompt_text: `{next_prompt_text.splitlines()[0] if next_prompt_text else 'none'}`",
            f"- workflow_states: `{workflow_summary}`",
            f"- work_files: {comma_or_none(work_files)}",
            f"- test_case_files: {comma_or_none(test_case_files)}",
            f"- validator_result: `errors={summary['errors_count']}; warnings={summary['warnings_count']}; info={summary['info_count']}`",
            f"- validator_finding_ids: {comma_or_none(finding_ids)}",
            "",
            "## Next Prompt Snapshot",
            "",
            "```text",
            next_prompt_text or "none",
            "```",
            "",
            "## Stage Results",
            "",
            "| stage | status | artifacts_created | validator_command | validator_result | finding_ids |",
            "| --- | --- | --- | --- | --- | --- |",
            "| source-locator | `pending` | `...` | `python scripts\\validate_agent_artifacts.py --root fts\\ft-2-OF_11 --json --fail-on warning --session-log-policy audit --decision-log-policy strict` | `...` | `...` |",
            "| scope-selection | `pending` | `...` | same | `...` | `...` |",
            "| confirmed-scope | `pending` | `...` | same | `...` | `...` |",
            "| writer-pass | `pending` | `...` | same | `...` | `...` |",
            "",
            "## Source / Mockup / Inventory Evidence",
            "",
            "| check | expected | actual | status | evidence |",
            "| --- | --- | --- | --- | --- |",
            "| source-selection content gate | required sections and `selection_status` | `...` | `pending` | `...` |",
            "| source-parity-check | present for DOCX+PDF | `...` | `pending` | `...` |",
            "| mockup-visual-inventory | present/opened for UI mockup scope | `...` | `pending` | `...` |",
            "| handoff source-row-inventory | present for row-level/table parity | `...` | `pending` | `...` |",
            "| writer source-row carry-over | writer inventory preserves handoff in-scope/unclear rows | `...` | `pending` | `...` |",
            "",
            "## Writer Output Metrics",
            "",
            f"- canonical_test_case_file: {comma_or_none([item['path'] for item in test_metrics['files']])}",
            f"- atom_count: `{test_metrics['atom_count']}`",
            f"- tc_count: `{test_metrics['tc_count']}`",
            f"- gap_count: `{test_metrics['gap_count']}`",
            f"- handoff_source_row_count: `{inventory['handoff_required_row_count']}`",
            f"- writer_source_row_count: `{inventory['writer_row_count']}`",
            f"- missing_handoff_source_rows_in_writer: {comma_or_none(inventory['missing_handoff_source_rows_in_writer'])}",
            "- writer_quality_gate_status: `pending`",
            "- artifact_write_strategy_status: `pending`",
            "- generic_tc_smell_findings: `pending`",
            "",
            "## Evaluation Result",
            "",
            "- status: `pending`",
            "- matched_expected_output: `pending`",
            "- pass_criteria_met:",
            "  - `pending`",
            "- fail_criteria_hit:",
            "  - `pending`",
            "",
            "## Residual Risk",
            "",
            "- Was this a real external agent run or a manual simulation: `pending`",
            "- Did the run use only the prompts from this eval: `pending`",
            "- Did the agent read local skills/references without direct reminders: `pending`",
            "- What semantic TC quality remains unverified before independent review: `pending`",
            "- Next remediation step if failed: `pending`",
        ]
    )


def assessment_gate_errors(report: dict[str, Any], args: argparse.Namespace) -> list[str]:
    assessment = report["clean_run_assessment"]
    errors: list[str] = []
    if args.expect_stage and assessment["stage"] != args.expect_stage:
        errors.append(f"Expected clean_run stage `{args.expect_stage}`, got `{assessment['stage']}`.")
    if args.expect_status and assessment["status"] != args.expect_status:
        errors.append(f"Expected clean_run status `{args.expect_status}`, got `{assessment['status']}`.")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    report = collect(args.root)
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    markdown_text = markdown_report(report)

    if args.next_prompt:
        output_text = report["clean_run_assessment"].get("next_prompt_text") or ""
    elif args.run_report_template:
        output_text = run_report_template(report)
    else:
        emit_json = args.json_only or not args.markdown_only
        output_text = json_text if emit_json else markdown_text

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text + "\n", encoding="utf-8")

    print(output_text)
    gate_errors = assessment_gate_errors(report, args)
    for error in gate_errors:
        print(error, file=sys.stderr)
    return 2 if gate_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
