"""Create a compact v0.9 source-package manifest from explicit package inputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import (
    APPROVED_CLARIFICATION_FILENAME_RE,
    ROUTE_VERSION,
    ROUTE_TOOL_VERSION,
    SOURCE_MANIFEST_RELATIVE_PATH,
    SOURCE_CONTRACT_VERSION,
    PracticalV09Error,
    relative_to_package,
    sha256_file,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create source-package-manifest.json for practical v0.9.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--xhtml", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--support",
        type=Path,
        action="append",
        default=[],
        help="Stable package support only; do not pass scope-local approved BA clarifications.",
    )
    return parser.parse_args(argv)


def document(package_root: Path, path: Path, role: str) -> dict[str, str]:
    resolved = path.resolve()
    try:
        resolved.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error(f"{role} is outside FT package: {resolved}") from exc
    if not resolved.is_file():
        raise PracticalV09Error(f"{role} does not exist: {resolved}")
    return {"role": role, "path": relative_to_package(package_root, resolved), "sha256": sha256_file(resolved)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    output = args.output.resolve()
    if not package_root.is_dir():
        raise PracticalV09Error(f"FT package root does not exist: {package_root}")
    try:
        output.relative_to(package_root)
    except ValueError as exc:
        raise PracticalV09Error("output must be inside FT package root") from exc
    if relative_to_package(package_root, output) != SOURCE_MANIFEST_RELATIVE_PATH:
        raise PracticalV09Error(
            "source manifest must use the shared package-level path "
            f"{SOURCE_MANIFEST_RELATIVE_PATH}"
        )
    if output.exists():
        raise PracticalV09Error(f"Refusing to overwrite existing manifest: {output}")
    for support_path in args.support:
        relative = relative_to_package(package_root, support_path.resolve())
        if APPROVED_CLARIFICATION_FILENAME_RE.search(relative):
            raise PracticalV09Error(
                "scope-local approved clarification must be bound through the related GAP-* "
                "in scope-obligations.json, not added to source-package-manifest.json"
            )
    payload: dict[str, object] = {
        "schema_version": 1,
        "route_version": ROUTE_VERSION,
        "tool_version": ROUTE_TOOL_VERSION,
        "source_contract_version": SOURCE_CONTRACT_VERSION,
        "documents": [
            document(package_root, args.docx, "main-docx"),
            document(package_root, args.xhtml, "main-xhtml"),
        ],
        "support_inputs": [document(package_root, path, "support") for path in args.support],
    }
    if args.pdf is not None:
        payload["documents"].append(document(package_root, args.pdf, "pdf-cross-check"))
    notes = package_root / "AGENT-NOTES.md"
    if notes.is_file():
        payload["agent_notes"] = {"path": "AGENT-NOTES.md", "sha256": sha256_file(notes)}
    else:
        payload["agent_notes"] = "not-applicable"
    write_json(output, payload)
    print(output.relative_to(package_root).as_posix())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
