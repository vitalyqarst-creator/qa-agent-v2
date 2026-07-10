from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT_DIR / "scripts" / "codex_exec_review_cycle_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "codex_exec_review_cycle_runner_schema_probe", RUNNER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runner module: {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def last_agent_payload(events_text: str, runner: Any) -> dict[str, Any] | None:
    messages: list[str] = []
    for line in events_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = runner.agent_message_from_event(event)
        if message:
            messages.append(message)
    if not messages:
        return None
    try:
        payload = json.loads(messages[-1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_probe(*, codex_command: str, output_dir: Path, timeout_seconds: int) -> dict[str, Any]:
    if output_dir.exists():
        raise RuntimeError(f"probe output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    runner = load_runner_module()
    schema = runner.CodexExecReviewCycleRunner._review_contract_schema(
        SimpleNamespace(_prepared_package=object())
    )
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    schema_path = output_dir / "review-contract.schema.json"
    write_text(schema_path, schema_text)
    prompt = """Return exactly one JSON object matching the supplied response schema.
Use contract_version 2, decision accepted, reviewed_draft_sha256 as 64 zero characters,
one obligation review for ATOM-PROBE-001 with verdict covered and TC-PROBE-001,
an empty findings array, and a short non-empty summary. Do not run commands or read files.
"""
    write_text(output_dir / "prompt.txt", prompt)

    version = subprocess.run(
        [codex_command, "--version"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=15,
    )
    command = [
        codex_command,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--cd",
        str(ROOT_DIR),
        "--json",
        "--output-schema",
        str(schema_path),
        "-",
    ]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout_seconds,
    )
    duration_seconds = time.monotonic() - started
    write_text(output_dir / "stdout.ndjson", completed.stdout)
    write_text(output_dir / "stderr.txt", completed.stderr)
    payload = last_agent_payload(completed.stdout, runner)
    expected_fields = {
        "contract_version",
        "decision",
        "reviewed_draft_sha256",
        "obligation_reviews",
        "findings",
        "summary",
    }
    passed = (
        completed.returncode == 0
        and payload is not None
        and set(payload) == expected_fields
        and payload.get("contract_version") == 2
    )
    result = {
        "status": "passed" if passed else "blocked",
        "codex_version": version.stdout.strip(),
        "schema_sha256": hashlib.sha256(schema_text.encode("utf-8")).hexdigest(),
        "schema_bytes": len(schema_text.encode("utf-8")),
        "exit_code": completed.returncode,
        "duration_seconds": round(duration_seconds, 3),
        "response_fields": sorted(payload) if payload is not None else [],
        "invalid_json_schema": "invalid_json_schema" in completed.stdout,
    }
    write_text(output_dir / "result.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe the live codex exec response-format capability with the exact prepared reviewer schema."
    )
    parser.add_argument("--codex-command", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_probe(
            codex_command=args.codex_command,
            output_dir=(ROOT_DIR / args.output_dir).resolve(),
            timeout_seconds=args.timeout_seconds,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
