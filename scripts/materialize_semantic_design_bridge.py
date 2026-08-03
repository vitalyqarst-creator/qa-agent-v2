from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.bounded_scope_materializer import (  # noqa: E402
    materialize_semantic_design_bridge,
    write_json_fresh,
)
from test_case_agent.semantic_design_bridge import (  # noqa: E402
    load_approved_clarifications,
)


def _load(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def _resolve(root: Path, value: Path) -> Path:
    return (value if value.is_absolute() else root / value).resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _prepare_summary_output(
    path: Path,
    *,
    protected_inputs: Sequence[Path],
    handoff_dir: Path,
) -> None:
    resolved = path.resolve()
    if resolved in {item.resolve() for item in protected_inputs}:
        raise ValueError("summary output must not alias a materialization input")
    if _is_within(resolved, handoff_dir) or _is_within(handoff_dir, resolved):
        raise ValueError("summary output must not overlap the atomic handoff path")
    if resolved.exists():
        raise FileExistsError(f"summary output must be fresh: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)


def _print_best_effort(payload: Mapping[str, Any], *, error: bool = False) -> None:
    try:
        print(
            json.dumps(payload, ensure_ascii=False, indent=2),
            file=sys.stderr if error else sys.stdout,
        )
    except Exception:
        # Publication/result status is authoritative; a closed or incompatible
        # console must not turn an already-published handoff into a failure.
        pass


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Validate semantic-design v3 against authoritative scope boundary v2 "
            "and transactionally publish one compiler-v3 handoff."
        )
    )
    result.add_argument("--repo-root", type=Path, required=True)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--semantic-design", type=Path, required=True)
    result.add_argument("--handoff-dir", type=Path, required=True)
    result.add_argument("--publication-owner-token", required=True)
    result.add_argument("--summary-output", type=Path)
    result.add_argument("--canonical-test-cases-override", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    summary_path: Path | None = None
    summary_ready_for_failure = False
    try:
        context_path = _resolve(root, args.context)
        boundary_path = _resolve(root, args.scope_boundary_decision)
        design_path = _resolve(root, args.semantic_design)
        handoff_dir = _resolve(root, args.handoff_dir)
        canonical_test_cases_override = (
            _resolve(root, args.canonical_test_cases_override)
            if args.canonical_test_cases_override is not None
            else None
        )
        if args.summary_output is not None:
            summary_path = _resolve(root, args.summary_output)
            _prepare_summary_output(
                summary_path,
                protected_inputs=(context_path, boundary_path, design_path),
                handoff_dir=handoff_dir,
            )
            summary_ready_for_failure = True
        context = _load(context_path)
        boundary = _load(boundary_path)
        design = _load(design_path)
        clarifications = load_approved_clarifications(root, context)
        result = materialize_semantic_design_bridge(
            repo_root=root,
            context=context,
            scope_boundary_decision=boundary,
            semantic_design=design,
            approved_clarifications=clarifications,
            publication_owner_token=args.publication_owner_token,
            handoff_dir=handoff_dir,
            success_summary_path=summary_path,
            canonical_test_cases_override=canonical_test_cases_override,
        )
    except Exception as exc:  # noqa: BLE001 - terminal CLI boundary.
        failure = {
            "status": "blocked",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if (
            summary_path is not None
            and summary_ready_for_failure
            and not summary_path.exists()
        ):
            try:
                write_json_fresh(summary_path, failure)
            except Exception:
                pass
        _print_best_effort(failure, error=True)
        return 2
    _print_best_effort(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
