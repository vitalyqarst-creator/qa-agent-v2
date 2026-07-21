from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.obligation_gate import (  # noqa: E402
    test_case_sections,
    validate_draft_obligation_coverage,
)
from test_case_agent.review_cycle.production_tc_gate import (  # noqa: E402
    validate_production_tc_content,
)


TITLE_RE = re.compile(r"(?mi)^\*\*Название:\*\*[^\S\r\n]*(.+?)\s*$")


def _resolve(root: Path, value: Path) -> Path:
    return (value if value.is_absolute() else root / value).resolve()


def _duplicate_title_findings(text: str) -> list[dict[str, object]]:
    titles: dict[str, list[str]] = {}
    for test_case_id, section in test_case_sections(text):
        match = TITLE_RE.search(section)
        if match is None:
            continue
        normalized = " ".join(match.group(1).split()).casefold()
        titles.setdefault(normalized, []).append(test_case_id)
    return [
        {
            "id": "duplicate-title",
            "severity": "error",
            "test_case_ids": test_case_ids,
            "message": "Production test-case titles must be unique within the suite.",
        }
        for test_case_ids in titles.values()
        if len(test_case_ids) > 1
    ]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Re-run the current deterministic obligation gate against an immutable "
            "prepared draft and publish a hash-bound fresh report."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--draft", type=Path, required=True)
    result.add_argument("--obligations", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--include-production-quality", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    draft = _resolve(root, args.draft)
    obligations = _resolve(root, args.obligations)
    output = _resolve(root, args.output)
    if output.exists():
        raise FileExistsError(f"revalidation output must be fresh: {output}")
    result = validate_draft_obligation_coverage(
        draft_path=draft,
        obligations_path=obligations,
        strict_runtime_contract=True,
    )
    payload = result.as_dict()
    if args.include_production_quality:
        draft_text = draft.read_text(encoding="utf-8")
        production = validate_production_tc_content(
            draft_text,
            checked_path=str(draft),
        )
        title_findings = _duplicate_title_findings(draft_text)
        findings = [*result.findings, *title_findings, *production.findings]
        payload = {
            "passed": not findings,
            "validator": "prepared-draft-quality-revalidation-v1",
            "package_id": result.package_id,
            "test_case_count": result.test_case_count,
            "testable_obligations": result.testable_obligations,
            "covered_obligations": list(result.covered_obligations),
            "checked_paths": list(result.checked_paths),
            "obligation_gate": result.as_dict(),
            "production_runtime_gate": production.as_dict(),
            "duplicate_title_findings": title_findings,
            "findings": findings,
        }
    payload.update(
        {
            "revalidation_version": 1,
            "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest(),
            "obligations_sha256": hashlib.sha256(obligations.read_bytes()).hexdigest(),
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
