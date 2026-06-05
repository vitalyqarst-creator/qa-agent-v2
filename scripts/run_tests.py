from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

AGENT_LAYER_MODULES = [
    "tests.test_agent_architecture",
    "tests.test_agent_audit_script",
    "tests.test_agent_artifact_validator",
    "tests.test_codex_review_cycle_runner",
    "tests.test_instruction_context_resolver",
    "tests.test_iteration_contracts",
    "tests.test_qa_rules",
    "tests.test_reviewer_contracts",
    "tests.test_session_based_review_cycle_contracts",
    "tests.test_source_parsing_quality",
    "tests.test_task_start_skill_routing",
    "tests.test_update_markdown_section",
]

ARCHITECTURE_AUDIT_SCRIPT = (
    ROOT_DIR
    / "skills"
    / "agent-architecture-auditor"
    / "scripts"
    / "audit_agent_architecture.py"
)


def run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=ROOT_DIR, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the canonical unittest commands for this repository."
    )
    parser.add_argument(
        "--suite",
        choices=("full", "agent-layer", "architecture"),
        default="full",
        help="Select which unittest suite to run. Default: full.",
    )
    args = parser.parse_args()

    if args.suite == "architecture":
        command = [
            sys.executable,
            str(ARCHITECTURE_AUDIT_SCRIPT),
            "--text",
            "--fail-on",
            "warning",
        ]
    elif args.suite == "agent-layer":
        command = [sys.executable, "-m", "unittest", *AGENT_LAYER_MODULES]
    else:
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]

    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
