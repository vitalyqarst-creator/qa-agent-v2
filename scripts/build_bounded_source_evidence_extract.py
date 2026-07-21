from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_source_assertion_reviewer import (
    BOUNDED_EXTRACT_METHODS,
    BOUNDED_EXTRACT_VERSION,
    SourceReviewerRunnerError,
    load_bounded_evidence_extract,
    load_json_object,
    resolve_under,
    sha256_file,
)


SELECTION_SPEC_VERSION = 1


def _exact_keys(payload: Mapping[str, Any], expected: set[str], *, label: str) -> None:
    actual = set(payload)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise SourceReviewerRunnerError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def build_descriptor(
    *,
    root: Path,
    selection_spec_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    selection_spec_path = resolve_under(
        root, selection_spec_path, label="selection_spec"
    )
    payload = load_json_object(selection_spec_path, label="bounded extract selection spec")
    _exact_keys(
        payload,
        {"version", "source_path", "extraction_method", "selections"},
        label="bounded extract selection spec",
    )
    if type(payload["version"]) is not int or payload["version"] != SELECTION_SPEC_VERSION:
        raise SourceReviewerRunnerError(
            f"bounded extract selection spec.version must equal {SELECTION_SPEC_VERSION}"
        )
    source_path = payload["source_path"]
    if not isinstance(source_path, str) or not source_path.strip():
        raise SourceReviewerRunnerError("selection spec.source_path must be non-empty text")
    source_path = source_path.strip()
    source_file = resolve_under(root, Path(source_path), label="selection source_path")
    method = payload["extraction_method"]
    if method not in BOUNDED_EXTRACT_METHODS:
        raise SourceReviewerRunnerError(
            "selection spec.extraction_method must be one of "
            + ", ".join(sorted(BOUNDED_EXTRACT_METHODS))
        )
    raw_selections = payload["selections"]
    if not isinstance(raw_selections, list) or not raw_selections:
        raise SourceReviewerRunnerError("selection spec.selections must be non-empty")
    fragments: list[dict[str, str]] = []
    for index, selection in enumerate(raw_selections):
        if not isinstance(selection, Mapping):
            raise SourceReviewerRunnerError(
                f"selection spec.selections[{index}] must be an object"
            )
        _exact_keys(
            selection,
            {"source_locator", "exact_source_text"},
            label=f"selection spec.selections[{index}]",
        )
        locator = selection["source_locator"]
        text = selection["exact_source_text"]
        if not isinstance(locator, str) or not locator.strip():
            raise SourceReviewerRunnerError(
                f"selection spec.selections[{index}].source_locator must be non-empty"
            )
        if not isinstance(text, str) or not text.strip():
            raise SourceReviewerRunnerError(
                f"selection spec.selections[{index}].exact_source_text must be non-empty"
            )
        fragments.append(
            {
                "source_locator": locator.strip(),
                "exact_source_text": text.strip(),
                "exact_source_text_sha256": hashlib.sha256(
                    text.strip().encode("utf-8")
                ).hexdigest(),
            }
        )
    return {
        "version": BOUNDED_EXTRACT_VERSION,
        "source_path": source_path,
        "source_sha256": sha256_file(source_file),
        "extraction_method": method,
        "fragments": fragments,
    }


def write_validated_descriptor(
    *,
    root: Path,
    output_path: Path,
    payload: Mapping[str, Any],
) -> None:
    root = root.resolve()
    output_path = resolve_under(root, output_path, label="output")
    if output_path.exists():
        raise SourceReviewerRunnerError(
            f"bounded evidence descriptor already exists: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        load_bounded_evidence_extract(temporary_path, root=root)
        try:
            os.link(temporary_path, output_path)
        except FileExistsError as exc:
            raise SourceReviewerRunnerError(
                f"bounded evidence descriptor appeared concurrently: {output_path}"
            ) from exc
    finally:
        temporary_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build one immutable, source-verified bounded evidence descriptor from "
            "an exact literal-fragment selection spec."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--selection-spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = build_descriptor(
            root=args.repo_root,
            selection_spec_path=args.selection_spec,
        )
        write_validated_descriptor(
            root=args.repo_root,
            output_path=args.output,
            payload=payload,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - one terminal helper result.
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
