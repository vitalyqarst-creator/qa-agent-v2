from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from test_case_agent.quality_proof import (  # noqa: E402
    QualityProofContractError,
    run_quality_proof,
    write_quality_proof_result,
)


DEFAULT_MANIFEST = PROJECT_ROOT / "evals" / "quick-quality-proof" / "manifest.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the offline quick quality proof and emit JSON metrics."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        result = run_quality_proof(
            args.manifest.resolve(),
            repo_root=args.repo_root.resolve(),
        )
    except (OSError, QualityProofContractError) as error:
        print(str(error), file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
    else:
        write_quality_proof_result(args.output.resolve(), result)
        print(args.output.resolve())
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
