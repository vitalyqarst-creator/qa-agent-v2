from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]


class ShadowConfigError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ShadowConfigError(f"path escapes repository root: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare an immutable schema-v2 shadow benchmark config."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--handoff-dir", required=True)
    parser.add_argument("--cycle-dir", required=True)
    parser.add_argument("--final-artifact", required=True)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--attempt-dir", type=Path)
    args = parser.parse_args()
    try:
        repo_root = args.repo_root.resolve()
        base_path = (
            args.base_config.resolve()
            if args.base_config.is_absolute()
            else (repo_root / args.base_config).resolve()
        )
        output_dir = (
            args.output_dir.resolve()
            if args.output_dir.is_absolute()
            else (repo_root / args.output_dir).resolve()
        )
        repo_relative(repo_root, base_path)
        repo_relative(repo_root, output_dir)
        if output_dir.exists() and any(output_dir.iterdir()):
            raise ShadowConfigError(f"output directory is not empty: {output_dir}")
        base = json.loads(base_path.read_text(encoding="utf-8"))
        if not isinstance(base, dict) or base.get("schema_version") != 2:
            raise ShadowConfigError("base config must be a schema-v2 JSON object")
        expected = base.get("expected_sha256")
        if not isinstance(expected, dict):
            raise ShadowConfigError("base expected_sha256 must be an object")
        for raw_path, digest in expected.items():
            path = (repo_root / str(raw_path)).resolve()
            if not path.is_file() or sha256(path) != digest:
                raise ShadowConfigError(f"base pinned input changed: {raw_path}")

        preparation = base.get("source_preparation")
        if not isinstance(preparation, dict):
            raise ShadowConfigError("base source_preparation must be an object")
        source_template = (repo_root / str(preparation["context_template"])).resolve()
        template = json.loads(source_template.read_text(encoding="utf-8"))
        if not isinstance(template, dict):
            raise ShadowConfigError("bounded context template must be an object")
        source_spec = (repo_root / str(template["source_row_extraction_spec"])).resolve()

        output_dir.mkdir(parents=True, exist_ok=True)
        target_spec = output_dir / "source-row-extraction-spec.json"
        target_spec.write_bytes(source_spec.read_bytes())
        target_template = output_dir / "bounded-context-template.json"
        template["canonical_test_cases"] = args.final_artifact
        template["source_row_extraction_spec"] = repo_relative(repo_root, target_spec)
        write_json(target_template, template)

        config = copy.deepcopy(base)
        config["benchmark_id"] = args.benchmark_id
        config["source_preparation"]["context_template"] = repo_relative(
            repo_root, target_template
        )
        config["outputs"] = {
            "handoff_dir": args.handoff_dir,
            "cycle_dir": args.cycle_dir,
            "final_artifact": args.final_artifact,
        }
        retained = {
            str(path): str(digest)
            for path, digest in expected.items()
            if (repo_root / str(path)).resolve() not in {source_template, source_spec}
        }
        retained[repo_relative(repo_root, target_template)] = sha256(target_template)
        retained[repo_relative(repo_root, target_spec)] = sha256(target_spec)
        config["expected_sha256"] = retained
        config_path = output_dir / "shadow-benchmark-config.json"
        write_json(config_path, config)

        if args.attempt_dir is not None:
            write_json(
                args.attempt_dir.resolve() / "attempt-result.json",
                {
                    "classification": "completed",
                    "reason": "immutable shadow benchmark config prepared",
                    "result_links": [
                        repo_relative(repo_root, config_path),
                        repo_relative(repo_root, target_template),
                        repo_relative(repo_root, target_spec),
                    ],
                },
            )
        print(
            json.dumps(
                {"status": "prepared", "config": str(config_path)},
                ensure_ascii=True,
            )
        )
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"shadow config error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
