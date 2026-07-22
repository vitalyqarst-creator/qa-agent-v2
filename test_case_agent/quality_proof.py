from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.review_cycle.runtime import write_json_atomic


MANIFEST_SCHEMA_VERSION = 2
RESULT_SCHEMA_VERSION = 2

_PROOF_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}\Z")
_CHECK_ID = re.compile(r"QP-[0-9]{3}\Z")
_RISK = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
_SELECTOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_TEST_PATH = re.compile(r"tests/[A-Za-z0-9_./-]+\.py\Z")


class QualityProofContractError(ValueError):
    """Raised when a quality-proof manifest is unsafe or malformed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class QualityProofCheck:
    check_id: str
    risk: str
    nodeid: str


@dataclass(frozen=True)
class QualityProofManifest:
    proof_id: str
    description: str
    target_duration_seconds: float
    hard_duration_ceiling_seconds: float
    checks: tuple[QualityProofCheck, ...]
    sha256: str


def _exact_keys(
    payload: Mapping[str, Any],
    expected: set[str],
    *,
    location: str,
) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise QualityProofContractError(
            "quality-proof-schema",
            f"{location} keys differ; missing={missing}, unknown={unknown}",
        )


def _nonempty_text(value: Any, *, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QualityProofContractError(
            "quality-proof-schema",
            f"{location} must be a non-empty string",
        )
    return value.strip()


def _validated_nodeid(nodeid: Any, *, repo_root: Path) -> str:
    value = _nonempty_text(nodeid, location="check.nodeid")
    parts = value.split("::")
    if len(parts) not in {2, 3}:
        raise QualityProofContractError(
            "quality-proof-nodeid",
            f"nodeid must select one test function, received {value!r}",
        )
    test_path, *selectors = parts
    if not _TEST_PATH.fullmatch(test_path) or any(
        not _SELECTOR.fullmatch(selector) for selector in selectors
    ):
        raise QualityProofContractError(
            "quality-proof-nodeid",
            f"unsafe or unsupported pytest nodeid {value!r}",
        )

    tests_root = (repo_root / "tests").resolve()
    resolved = (repo_root / test_path).resolve()
    try:
        resolved.relative_to(tests_root)
    except ValueError as error:
        raise QualityProofContractError(
            "quality-proof-nodeid",
            f"test path escapes tests/: {test_path!r}",
        ) from error
    if not resolved.is_file():
        raise QualityProofContractError(
            "quality-proof-nodeid",
            f"selected test file does not exist: {test_path!r}",
        )
    return value


def load_quality_proof_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
) -> QualityProofManifest:
    """Load a closed-schema manifest and validate every selected pytest node."""

    raw = manifest_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualityProofContractError(
            "quality-proof-json",
            f"manifest is not valid UTF-8 JSON: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise QualityProofContractError(
            "quality-proof-schema",
            "manifest root must be an object",
        )
    _exact_keys(
        payload,
        {
            "schema_version",
            "proof_id",
            "description",
            "target_duration_seconds",
            "hard_duration_ceiling_seconds",
            "checks",
        },
        location="manifest",
    )
    if payload["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise QualityProofContractError(
            "quality-proof-version",
            f"expected schema_version={MANIFEST_SCHEMA_VERSION}",
        )

    proof_id = _nonempty_text(payload["proof_id"], location="manifest.proof_id")
    if not _PROOF_ID.fullmatch(proof_id):
        raise QualityProofContractError(
            "quality-proof-schema",
            f"invalid proof_id {proof_id!r}",
        )
    description = _nonempty_text(
        payload["description"],
        location="manifest.description",
    )
    target = payload["target_duration_seconds"]
    ceiling = payload["hard_duration_ceiling_seconds"]
    if isinstance(target, bool) or not isinstance(target, (int, float)):
        raise QualityProofContractError(
            "quality-proof-schema",
            "target_duration_seconds must be a number",
        )
    if isinstance(ceiling, bool) or not isinstance(ceiling, (int, float)):
        raise QualityProofContractError(
            "quality-proof-schema",
            "hard_duration_ceiling_seconds must be a number",
        )
    target = float(target)
    ceiling = float(ceiling)
    if not 0 < target <= 60:
        raise QualityProofContractError(
            "quality-proof-schema",
            "target_duration_seconds must be greater than 0 and at most 60",
        )
    if not target < ceiling <= 120:
        raise QualityProofContractError(
            "quality-proof-schema",
            "hard_duration_ceiling_seconds must exceed the target and be at most 120",
        )

    raw_checks = payload["checks"]
    if not isinstance(raw_checks, list) or not raw_checks:
        raise QualityProofContractError(
            "quality-proof-schema",
            "checks must be a non-empty array",
        )
    checks: list[QualityProofCheck] = []
    seen_ids: set[str] = set()
    seen_nodeids: set[str] = set()
    for index, item in enumerate(raw_checks):
        if not isinstance(item, dict):
            raise QualityProofContractError(
                "quality-proof-schema",
                f"checks[{index}] must be an object",
            )
        _exact_keys(item, {"id", "risk", "nodeid"}, location=f"checks[{index}]")
        check_id = _nonempty_text(item["id"], location=f"checks[{index}].id")
        risk = _nonempty_text(item["risk"], location=f"checks[{index}].risk")
        if not _CHECK_ID.fullmatch(check_id):
            raise QualityProofContractError(
                "quality-proof-schema",
                f"invalid check id {check_id!r}",
            )
        if not _RISK.fullmatch(risk):
            raise QualityProofContractError(
                "quality-proof-schema",
                f"invalid risk code {risk!r}",
            )
        nodeid = _validated_nodeid(item["nodeid"], repo_root=repo_root)
        if check_id in seen_ids:
            raise QualityProofContractError(
                "quality-proof-duplicate",
                f"duplicate check id {check_id!r}",
            )
        if nodeid in seen_nodeids:
            raise QualityProofContractError(
                "quality-proof-duplicate",
                f"duplicate nodeid {nodeid!r}",
            )
        seen_ids.add(check_id)
        seen_nodeids.add(nodeid)
        checks.append(QualityProofCheck(check_id, risk, nodeid))

    return QualityProofManifest(
        proof_id=proof_id,
        description=description,
        target_duration_seconds=target,
        hard_duration_ceiling_seconds=ceiling,
        checks=tuple(checks),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _junit_identity(nodeid: str) -> tuple[str, str]:
    path, *selectors = nodeid.split("::")
    module = path[:-3].replace("/", ".")
    test_name = selectors[-1]
    class_name = ".".join((module, *selectors[:-1]))
    return class_name, test_name


def _testcase_outcome(element: ET.Element) -> str:
    if element.find("failure") is not None:
        return "failed"
    if element.find("error") is not None:
        return "error"
    if element.find("skipped") is not None:
        return "skipped"
    return "passed"


def _parse_junit(
    junit_path: Path,
    checks: Sequence[QualityProofCheck],
) -> list[dict[str, Any]]:
    by_identity: dict[tuple[str, str], list[ET.Element]] = {}
    if junit_path.is_file():
        root = ET.parse(junit_path).getroot()
        for testcase in root.findall(".//testcase"):
            identity = (
                testcase.attrib.get("classname", ""),
                testcase.attrib.get("name", ""),
            )
            by_identity.setdefault(identity, []).append(testcase)

    results: list[dict[str, Any]] = []
    for check in checks:
        identity = _junit_identity(check.nodeid)
        matches = by_identity.get(identity, [])
        if len(matches) != 1:
            outcome = "not-run" if not matches else "ambiguous-result"
            duration_seconds: float | None = None
        else:
            testcase = matches[0]
            outcome = _testcase_outcome(testcase)
            try:
                duration_seconds = round(float(testcase.attrib.get("time", "0")), 6)
            except ValueError:
                duration_seconds = None
        results.append(
            {
                "id": check.check_id,
                "risk": check.risk,
                "nodeid": check.nodeid,
                "outcome": outcome,
                "duration_seconds": duration_seconds,
            }
        )
    return results


def summarize_quality_proof_outcome(
    *,
    pytest_exit_code: int,
    check_results: Sequence[Mapping[str, Any]],
    duration_seconds: float,
    target_duration_seconds: float,
    hard_duration_ceiling_seconds: float,
) -> dict[str, Any]:
    """Classify correctness and timing without making the target a flaky gate."""

    counts = {
        outcome: sum(item.get("outcome") == outcome for item in check_results)
        for outcome in (
            "passed",
            "failed",
            "error",
            "skipped",
            "not-run",
            "ambiguous-result",
        )
    }
    target_met = duration_seconds <= target_duration_seconds
    hard_ceiling_met = duration_seconds <= hard_duration_ceiling_seconds
    passed = (
        pytest_exit_code == 0
        and counts["passed"] == len(check_results)
        and hard_ceiling_met
    )
    if not hard_ceiling_met:
        performance_status = "hard-ceiling-exceeded"
    elif target_met:
        performance_status = "target-met"
    else:
        performance_status = "target-missed"
    return {
        "status": "passed" if passed else "failed",
        "target_met": target_met,
        "hard_ceiling_met": hard_ceiling_met,
        "performance_status": performance_status,
        "counts": counts,
    }


def run_quality_proof(
    manifest_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Run the immutable pytest selection once and return compact JSON metrics.

    The subprocess has no model backend and receives no application source paths.
    Both timing limits are evaluated after pytest exits; neither is a kill timeout.
    Missing the target is diagnostic. Only exceeding the hard ceiling fails the proof.
    """

    repo_root = repo_root.resolve()
    manifest = load_quality_proof_manifest(manifest_path, repo_root=repo_root)
    with tempfile.TemporaryDirectory(prefix="qa-quality-proof-") as temp_dir:
        temp_root = Path(temp_dir)
        junit_path = temp_root / "pytest-junit.xml"
        pytest_temp = temp_root / "pytest-temp"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "-p",
            "no:cacheprovider",
            f"--rootdir={repo_root}",
            f"--basetemp={pytest_temp}",
            f"--junitxml={junit_path}",
            *(check.nodeid for check in manifest.checks),
        ]
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "0",
                "PYTHONIOENCODING": "utf-8",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            }
        )
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        duration_seconds = round(time.perf_counter() - started, 6)
        check_results = _parse_junit(junit_path, manifest.checks)

    outcome = summarize_quality_proof_outcome(
        pytest_exit_code=completed.returncode,
        check_results=check_results,
        duration_seconds=duration_seconds,
        target_duration_seconds=manifest.target_duration_seconds,
        hard_duration_ceiling_seconds=manifest.hard_duration_ceiling_seconds,
    )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "proof_id": manifest.proof_id,
        "manifest_sha256": manifest.sha256,
        "status": outcome["status"],
        "execution_mode": "offline-pytest",
        "model_calls": 0,
        "pytest_exit_code": completed.returncode,
        "target_duration_seconds": manifest.target_duration_seconds,
        "hard_duration_ceiling_seconds": manifest.hard_duration_ceiling_seconds,
        "duration_seconds": duration_seconds,
        "target_met": outcome["target_met"],
        "hard_ceiling_met": outcome["hard_ceiling_met"],
        "performance_status": outcome["performance_status"],
        "check_count": len(manifest.checks),
        "counts": outcome["counts"],
        "checks": check_results,
    }


def write_quality_proof_result(
    path: Path,
    result: Mapping[str, Any],
    *,
    require_fresh: bool = False,
) -> None:
    """Write a result atomically, optionally with create-only semantics.

    ``require_fresh`` materializes a complete temporary inode and links it to the
    destination only if that destination is still absent. This preserves both the
    no-overwrite contract and atomic visibility under concurrent invocations.
    """

    if not require_fresh:
        write_json_atomic(path, result)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp"
    )
    rendered = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise QualityProofContractError(
                "quality-proof-output-exists",
                f"result path must be fresh: {path}",
            ) from error
    finally:
        temporary.unlink(missing_ok=True)
