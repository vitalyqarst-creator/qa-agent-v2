"""Restore controller-owned practical state from a launch preflight snapshot.

This is an explicit controller-only recovery command.  It exists for the rare
case where a separate reviewer task modified ``workflow-state.yaml`` or the
package practical summary despite its read-only contract.  It never restores
test cases, sources, matrices or reviewer findings.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore controller-owned practical state from a launch receipt snapshot."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Perform the restore. Without this flag the command is a read-only verification.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def build_recovery_result(
    *,
    ft_package_root: Path,
    summary_path: Path,
    scope_ids: list[str],
    launch_receipt: Path,
    restore: bool,
) -> dict[str, object]:
    ft_package_root = ft_package_root.resolve()
    summary_path = summary_path.resolve()
    issues: list[str] = []
    try:
        receipt = json.loads(launch_receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        receipt = {}
        issues.append(f"cannot read review launch receipt: {exc}")
    if receipt.get("allowed") is not True:
        issues.append("review launch receipt is not allowed")

    descriptors, descriptor_issues = review_preflight.scope_descriptors(
        ft_package_root, scope_ids
    )
    issues.extend(descriptor_issues)
    targets: dict[str, dict[str, object]] = {}
    if not descriptor_issues:
        targets, snapshot_issues = review_preflight.verify_controller_snapshot(
            receipt,
            ft_package_root=ft_package_root,
            summary_path=summary_path,
            descriptors=descriptors,
        )
        issues.extend(snapshot_issues)

    changed_targets: list[str] = []
    expected_hashes = receipt.get("controller_artifact_hashes")
    if isinstance(expected_hashes, dict):
        for key, target in targets.items():
            source = Path(str(target["source_path"]))
            expected = str(target["sha256"])
            actual = review_preflight.sha256_file(source) if source.is_file() else ""
            if actual != expected:
                changed_targets.append(key)

    if restore and not issues:
        for target in targets.values():
            source = Path(str(target["source_path"]))
            snapshot = Path(str(target["snapshot_path"]))
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snapshot, source)
        for key, target in targets.items():
            source = Path(str(target["source_path"]))
            if review_preflight.sha256_file(source) != str(target["sha256"]):
                issues.append(f"restored controller state hash mismatch for {key}")

    return {
        "schema_version": 1,
        "status": "restored" if restore and not issues else "ready" if not issues else "blocked",
        "allowed": not issues,
        "restored": bool(restore and not issues),
        "launch_receipt": launch_receipt.resolve().as_posix(),
        "changed_controller_targets_before_restore": changed_targets,
        "targets": {
            key: {
                "source_path": str(value["source_path"]),
                "snapshot_path": str(value["snapshot_path"]),
                "sha256": str(value["sha256"]),
            }
            for key, value in targets.items()
        },
        "blocking_reasons": issues,
    }


def main() -> int:
    args = parse_args()
    scope_ids = list(dict.fromkeys(args.scope_id))
    result = build_recovery_result(
        ft_package_root=args.ft_package_root,
        summary_path=args.summary,
        scope_ids=scope_ids,
        launch_receipt=args.launch_receipt.resolve(),
        restore=args.restore,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":  # pragma: no cover - exercised through main tests
    raise SystemExit(main())
