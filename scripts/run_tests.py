from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

AGENT_LAYER_MODULES = [
    "tests.test_agent_architecture",
    "tests.test_agent_audit_script",
    "tests.test_autofin_dadata_reference",
    "tests.test_verify_dadata_negative_fixture",
    "tests.test_verify_dadata_positive_fixture",
    "tests.test_bounded_scope_analyzer_v2",
    "tests.test_case_identity",
    "tests.test_cli",
    "tests.test_codex_exec_review_cycle_runner",
    "tests.test_codex_output_schema_probe",
    "tests.test_codex_review_cycle_runner",
    "tests.test_coverage_contract",
    "tests.test_coverage_graph",
    "tests.test_coverage_io",
    "tests.test_derivation_compiler",
    "tests.test_instruction_context_resolver",
    "tests.test_immutable_iteration",
    "tests.test_iteration_contract",
    "tests.test_iteration_contracts",
    "tests.test_lean_production",
    "tests.test_lean_v2_iteration",
    "tests.test_overnight_controller",
    "tests.test_incremental_update",
    "tests.test_probe_environment",
    "tests.test_prepared_stage_package",
    "tests.test_prepared_obligation_gate",
    "tests.test_prepared_evidence_access",
    "tests.test_prepared_reviewer_contract",
    "tests.test_promotion_adapter",
    "tests.test_qa_rules",
    "tests.test_quality_proof",
    "tests.test_review_cycle_stage_contract",
    "tests.test_review_cycle_runtime",
    "tests.test_review_cycle_backends",
    "tests.test_review_cycle_attempts",
    "tests.test_review_cycle_metrics",
    "tests.test_review_cycle_backend_matrix",
    "tests.test_reviewer_contracts",
    "tests.test_release_bundle",
    "tests.test_semantic_design_author",
    "tests.test_semantic_design_bridge",
    "tests.test_semantic_design_materializer",
    "tests.test_session_based_review_cycle_contracts",
    "tests.test_scope_compiler",
    "tests.test_scope_registry",
    "tests.test_source_parsing_quality",
    "tests.test_source_preparation",
    "tests.test_source_qualified_run",
    "tests.test_stage_backend",
    "tests.test_standard_production_iteration",
    "tests.test_standard_scope_bridge",
    "tests.test_task_start_skill_routing",
    "tests.test_test_design",
    "tests.test_update_markdown_section",
]

ARCHITECTURE_AUDIT_SCRIPT = (
    ROOT_DIR
    / "skills"
    / "agent-architecture-auditor"
    / "scripts"
    / "audit_agent_architecture.py"
)
AGENT_LAYER_FAST_MODULES = AGENT_LAYER_MODULES


def run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=ROOT_DIR, check=False, env=utf8_subprocess_env())
    return result.returncode


def utf8_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # Canonical test runs must be read-only with respect to repository sources.
    # Child interpreters do not inherit the parent's ``-B`` flag automatically.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_unittest_modules(modules: list[str]) -> int:
    if not modules:
        return 0
    return run_command([sys.executable, "-m", "unittest", *modules])


def discover_test_modules() -> list[str]:
    modules = [
        f"tests.{path.stem}"
        for path in (ROOT_DIR / "tests").glob("test_*.py")
    ]
    return sorted(modules)


def run_agent_layer_tests() -> int:
    return run_unittest_modules(AGENT_LAYER_MODULES)


def run_full_tests() -> int:
    return run_unittest_modules(discover_test_modules())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the canonical unittest commands for this repository."
    )
    parser.add_argument(
        "--suite",
        choices=(
            "full",
            "agent-layer",
            "agent-layer-fast",
            "architecture",
        ),
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
    elif args.suite == "agent-layer-fast":
        return run_unittest_modules(AGENT_LAYER_FAST_MODULES)
    elif args.suite == "agent-layer":
        return run_agent_layer_tests()
    else:
        return run_full_tests()

    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
