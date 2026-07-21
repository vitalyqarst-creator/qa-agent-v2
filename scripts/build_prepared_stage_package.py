from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.prepared_package import (  # noqa: E402
    EvidenceInput,
    PreparedObligationSet,
    PreparedPackageBuilder,
    PreparedReleaseStatus,
    StageInstructionConfig,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError  # noqa: E402


def _load_spec(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"cannot load package build spec: {path}") from exc
    if not isinstance(payload, dict):
        raise StageRuntimeError("package build spec must be a JSON object")
    return payload


def build_from_spec(spec_path: Path, repo_root: Path) -> Path:
    spec = _load_spec(spec_path)
    required = {
        "package_id",
        "ft_slug",
        "scope_slug",
        "section_id",
        "output_root",
        "max_package_bytes",
        "source_registry",
        "evidence_inputs",
        "obligations",
        "instructions",
        "execution_profile",
        "unsupported_dimensions",
        "forbidden_evidence_roots",
        "release_status",
    }
    if set(spec) != required:
        raise StageRuntimeError(
            f"invalid package build spec fields: missing={sorted(required - set(spec))}, "
            f"unknown={sorted(set(spec) - required)}"
        )
    obligations_payload = spec["obligations"]
    if not isinstance(obligations_payload, dict):
        raise StageRuntimeError("spec obligations must be a JSON object")
    obligations = PreparedObligationSet.from_dict(obligations_payload)
    release_status_payload = spec["release_status"]
    if not isinstance(release_status_payload, dict):
        raise StageRuntimeError("spec release_status must be a JSON object")
    release_status = PreparedReleaseStatus.from_dict(release_status_payload)
    instruction_payload = spec["instructions"]
    if not isinstance(instruction_payload, dict):
        raise StageRuntimeError("spec instructions must be a JSON object")
    try:
        instructions = StageInstructionConfig(**instruction_payload)
        sources = [
            (repo_root / item["path"], item["role"], item["locator"])
            for item in spec["source_registry"]
        ]
        evidence = [
            EvidenceInput(
                repo_root / item["path"],
                item["title"],
                selectors=tuple(item.get("selectors", ())),
                include_full=item.get("include_full", False),
                max_bytes=item.get("max_bytes", 8192),
            )
            for item in spec["evidence_inputs"]
        ]
    except (KeyError, TypeError) as exc:
        raise StageRuntimeError("invalid source/evidence/instruction build spec entry") from exc
    builder = PreparedPackageBuilder(repo_root, max_package_bytes=spec["max_package_bytes"])
    package = builder.build(
        output_root=repo_root / spec["output_root"],
        package_id=spec["package_id"],
        ft_slug=spec["ft_slug"],
        scope_slug=spec["scope_slug"],
        section_id=spec["section_id"],
        source_registry=sources,
        evidence_inputs=evidence,
        obligations=obligations,
        instructions=instructions,
        execution_profile=spec["execution_profile"],
        unsupported_dimensions=spec["unsupported_dimensions"],
        forbidden_evidence_roots=spec["forbidden_evidence_roots"],
        release_status=release_status,
    )
    return repo_root / spec["output_root"] / "stage-package.json"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build and validate a compact prepared stage package")
    result.add_argument("--spec", required=True)
    result.add_argument("--repo-root", default=".")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        output = build_from_spec((repo_root / args.spec).resolve(), repo_root)
    except StageRuntimeError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "built", "stage_package": output.relative_to(repo_root).as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
