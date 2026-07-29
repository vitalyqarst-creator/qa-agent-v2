from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
FT_ROOT = ROOT / "fts" / "AutoFin" / "PostFinal-v2-rc5"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "07-4.3-client-addresses"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def upsert(items: list[dict[str, object]], record: dict[str, object]) -> None:
    path = record["path"]
    for index, item in enumerate(items):
        if item.get("path") == path:
            items[index] = record
            return
    items.append(record)


def main() -> int:
    registry_path = FT_ROOT / "scope-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    scope_clar = "work/stage-handoffs/07-4.3-client-addresses/scope-clarification-requests.md"
    for scope in registry["scopes"]:
        if scope.get("scope_id") == "4-3-client-addresses":
            refs = scope.setdefault("reference_paths", [])
            if scope_clar not in refs:
                refs.append(scope_clar)
            break
    else:
        raise RuntimeError("scope not found in registry")
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest_path = HANDOFF / "source-assertions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    evidence = list(manifest["evidence_sources"])
    additions = [
        ("support/client-addresses-approved-clarifications.md", "approved-clarification"),
        ("support/client-addresses-approved-clarifications-v2.md", "approved-clarification"),
        ("support/АФБ справочники 26.06.26.md", "supporting-material"),
    ]
    for local_path, role in additions:
        path = FT_ROOT / local_path
        upsert(
            evidence,
            {
                "path": rel(path),
                "sha256": sha256(path),
                "role": role,
            },
        )
    manifest["evidence_sources"] = evidence
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    source_selection = HANDOFF / "source-selection.scope-local.md"
    text = source_selection.read_text(encoding="utf-8")
    marker = "| `support/client-addresses-approved-clarifications-v3.md` | `approved-clarification` |"
    extra_rows = [
        (
            "| `support/client-addresses-approved-clarifications.md` | `approved-clarification` | "
            f"`{sha256(FT_ROOT / 'support/client-addresses-approved-clarifications.md')}` | "
            "`approved-clarification` | `4-3-client-addresses` |"
        ),
        (
            "| `support/client-addresses-approved-clarifications-v2.md` | `approved-clarification` | "
            f"`{sha256(FT_ROOT / 'support/client-addresses-approved-clarifications-v2.md')}` | "
            "`approved-clarification` | `4-3-client-addresses` |"
        ),
        (
            "| `support/АФБ справочники 26.06.26.md` | `supporting-material` | "
            f"`{sha256(FT_ROOT / 'support/АФБ справочники 26.06.26.md')}` | "
            "`supporting-material` | `4-3-client-addresses` |"
        ),
    ]
    if "support/client-addresses-approved-clarifications-v2.md" not in text:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith(marker):
                lines[index + 1:index + 1] = extra_rows
                break
        text = "\n".join(lines) + "\n"
        source_selection.write_text(text, encoding="utf-8", newline="\n")

    print(json.dumps({"status": "aligned"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
