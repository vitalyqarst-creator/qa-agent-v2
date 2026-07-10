from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

AGENT_LAYER_MODULES = [
    "tests.test_agent_architecture",
    "tests.test_agent_audit_script",
    "tests.test_agent_artifact_validator",
    "tests.test_codex_exec_review_cycle_runner",
    "tests.test_codex_review_cycle_runner",
    "tests.test_instruction_context_resolver",
    "tests.test_iteration_contracts",
    "tests.test_probe_environment",
    "tests.test_prepared_stage_package",
    "tests.test_qa_rules",
    "tests.test_review_cycle_stage_contract",
    "tests.test_review_cycle_runtime",
    "tests.test_review_cycle_backends",
    "tests.test_review_cycle_attempts",
    "tests.test_review_cycle_metrics",
    "tests.test_review_cycle_backend_matrix",
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
ARTIFACT_VALIDATOR_TEST_CASE = "tests.test_agent_artifact_validator.AgentArtifactValidatorTests"
ARTIFACT_VALIDATOR_MODULE = "tests.test_agent_artifact_validator"
DEFAULT_ARTIFACT_VALIDATOR_SHARDS = 7

AGENT_LAYER_FAST_MODULES = [
    module for module in AGENT_LAYER_MODULES if module != ARTIFACT_VALIDATOR_MODULE
]
EXCLUDED_FULL_DISCOVERY_MODULES = {ARTIFACT_VALIDATOR_MODULE}


def run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=ROOT_DIR, check=False, env=utf8_subprocess_env())
    return result.returncode


def utf8_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def write_stdout(text: str) -> None:
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(
            encoding,
            errors="replace",
        )
        sys.stdout.write(safe_text)


def run_unittest_modules(modules: list[str]) -> int:
    if not modules:
        return 0
    return run_command([sys.executable, "-m", "unittest", *modules])


def discover_test_modules(excluded_modules: set[str] | None = None) -> list[str]:
    excluded = excluded_modules or set()
    modules = [
        f"tests.{path.stem}"
        for path in (ROOT_DIR / "tests").glob("test_*.py")
        if f"tests.{path.stem}" not in excluded
    ]
    return sorted(modules)


def iter_suite_tests(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            tests.extend(iter_suite_tests(item))
        else:
            tests.append(item)
    return tests


def run_artifact_validator_tests(shard_index: int, shard_count: int) -> int:
    if shard_count < 1:
        raise SystemExit("--shard-count must be >= 1")
    if shard_index < 1 or shard_index > shard_count:
        raise SystemExit("--shard-index must be between 1 and --shard-count")

    loader = unittest.defaultTestLoader
    all_tests = iter_suite_tests(loader.loadTestsFromName(ARTIFACT_VALIDATOR_TEST_CASE))
    selected_tests = [
        test
        for offset, test in enumerate(all_tests)
        if offset % shard_count == shard_index - 1
    ]
    print(
        f"Running {len(selected_tests)} of {len(all_tests)} artifact-validator tests "
        f"(shard {shard_index}/{shard_count})",
        flush=True,
    )
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected_tests))
    return 0 if result.wasSuccessful() else 1


def run_artifact_validator_sharded_tests(shard_count: int) -> int:
    if shard_count < 1:
        raise SystemExit("--shard-count must be >= 1")

    failed_shards: list[int] = []
    with tempfile.TemporaryDirectory(prefix="artifact-validator-shards-") as log_dir:
        processes = []
        for shard_index in range(1, shard_count + 1):
            log_path = Path(log_dir) / f"shard-{shard_index}.log"
            log_handle = log_path.open("w", encoding="utf-8", errors="replace")
            print(
                f"Starting artifact-validator shard {shard_index}/{shard_count}",
                flush=True,
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--suite",
                    "artifact-validator",
                    "--shard-count",
                    str(shard_count),
                    "--shard-index",
                    str(shard_index),
                ],
                cwd=ROOT_DIR,
                env=utf8_subprocess_env(),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            processes.append((shard_index, process, log_path, log_handle))

        for shard_index, process, log_path, log_handle in processes:
            process.wait()
            log_handle.close()
            output = log_path.read_text(encoding="utf-8", errors="replace")
            write_stdout(
                f"\n=== artifact-validator shard {shard_index}/{shard_count} output ===\n"
            )
            write_stdout(output)
            if not output.endswith("\n"):
                write_stdout("\n")
            if process.returncode != 0:
                failed_shards.append(shard_index)

    if failed_shards:
        print(
            "Failed artifact-validator shards: "
            + ", ".join(str(index) for index in failed_shards)
        )
        return 1
    print(f"All artifact-validator shards passed ({shard_count}/{shard_count}).")
    return 0


def run_agent_layer_tests(shard_count: int) -> int:
    fast_result = run_unittest_modules(AGENT_LAYER_FAST_MODULES)
    if fast_result != 0:
        return fast_result
    return run_artifact_validator_sharded_tests(shard_count)


def run_full_tests(shard_count: int) -> int:
    fast_modules = discover_test_modules(EXCLUDED_FULL_DISCOVERY_MODULES)
    fast_result = run_unittest_modules(fast_modules)
    if fast_result != 0:
        return fast_result
    return run_artifact_validator_sharded_tests(shard_count)


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
            "artifact-validator",
            "artifact-validator-sharded",
        ),
        default="full",
        help="Select which unittest suite to run. Default: full.",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=1,
        help="1-based shard index for --suite artifact-validator.",
    )
    parser.add_argument(
        "--shard-count",
        type=int,
        default=None,
        help=(
            "Total shard count for artifact-validator suites. Defaults to 1 for "
            "artifact-validator and 7 for artifact-validator-sharded."
        ),
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
    elif args.suite == "artifact-validator":
        return run_artifact_validator_tests(args.shard_index, args.shard_count or 1)
    elif args.suite == "artifact-validator-sharded":
        return run_artifact_validator_sharded_tests(
            args.shard_count or DEFAULT_ARTIFACT_VALIDATOR_SHARDS
        )
    elif args.suite == "agent-layer-fast":
        return run_unittest_modules(AGENT_LAYER_FAST_MODULES)
    elif args.suite == "agent-layer":
        return run_agent_layer_tests(args.shard_count or DEFAULT_ARTIFACT_VALIDATOR_SHARDS)
    else:
        return run_full_tests(args.shard_count or DEFAULT_ARTIFACT_VALIDATOR_SHARDS)

    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())
