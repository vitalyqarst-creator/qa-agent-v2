from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ARCHITECTURE_AUDIT_SCRIPT = (
    ROOT_DIR
    / "skills"
    / "agent-architecture-auditor"
    / "scripts"
    / "audit_agent_architecture.py"
)
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


# The clean production build does not ship legacy route tests.  Keep the
# agent-layer suite derived from the files that are actually packaged, rather
# than retaining a stale inventory from the development repository.
AGENT_LAYER_MODULES = discover_test_modules()
AGENT_LAYER_FAST_MODULES = AGENT_LAYER_MODULES


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
