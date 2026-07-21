from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.semantic_design_bridge import (  # noqa: E402
    load_approved_clarifications,
    normalize_semantic_design_transport,
    semantic_design_completeness_diagnostics,
    semantic_design_transport_diagnostics,
    validate_semantic_design_binding,
)


def _load(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def _resolve(root: Path, path: Path) -> Path:
    return (path if path.is_absolute() else root / path).resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Aggregate semantic-design transport findings, preview deterministic "
            "repairs, and replay the complete strict binding validator offline."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--semantic-design", type=Path, required=True)
    result.add_argument("--output", type=Path)
    result.add_argument("--require-ready", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    context_path = _resolve(root, args.context)
    boundary_path = _resolve(root, args.scope_boundary_decision)
    design_path = _resolve(root, args.semantic_design)
    context = _load(context_path)
    boundary = _load(boundary_path)
    raw_design = _load(design_path)

    transport = semantic_design_transport_diagnostics(
        raw_design,
        context=context,
        boundary=boundary,
    )
    normalized, receipt = normalize_semantic_design_transport(
        raw_design,
        context=context,
        boundary=boundary,
        repo_root=root,
    )
    completeness = semantic_design_completeness_diagnostics(
        context,
        boundary,
        normalized,
    )
    strict_validation: dict[str, Any]
    try:
        clarifications = load_approved_clarifications(root, context)
        validation_summary = validate_semantic_design_binding(
            context,
            boundary,
            normalized,
            clarifications=clarifications,
            require_ready=args.require_ready,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic terminal boundary.
        strict_validation = {
            "status": "blocked",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    else:
        strict_validation = {
            "status": "passed",
            "summary": validation_summary,
        }

    report = {
        "version": 1,
        "status": (
            "passed" if strict_validation["status"] == "passed" else "blocked"
        ),
        "inputs": {
            "context": context_path.relative_to(root).as_posix(),
            "scope_boundary_decision": boundary_path.relative_to(root).as_posix(),
            "semantic_design": design_path.relative_to(root).as_posix(),
        },
        "transport_diagnostics": transport,
        "completeness_diagnostics": completeness,
        "normalization_receipt": receipt,
        "strict_validation": strict_validation,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        output = _resolve(root, args.output)
        if output.exists():
            raise FileExistsError(f"diagnostic output must be fresh: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
