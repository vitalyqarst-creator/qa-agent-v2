"""Audit AutoFin BSR traceability across source and artifacts.

This script treats the selected PDF BSR codes as the structural code inventory.
Only active source-row inventories with ``in_scope = yes`` count as mappings;
historical review cycles and arbitrary textual mentions are not mappings.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader


HISTORICAL_PARTS = {"_artifact_write", "review-cycles", "review-loops", "versions"}


def norm_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def bsr_code(value: int) -> str:
    return f"BSR {value}"


def extract_bsr_numbers(text: str) -> set[int]:
    return {int(match) for match in re.findall(r"BSR\s*([0-9]+)", text, flags=re.I)}


def scope_guess(number: int) -> str:
    """Route only Final ranges confirmed by bounded source analysis."""
    if 1 <= number <= 34:
        return "01-applications-menu-search"
    if 35 <= number <= 42:
        return "section-4.2-applications-menu-search"
    if 43 <= number <= 46:
        return "27-calculator-summary-final-source-rebase"
    return "unmapped-final-source"


def collect_pdf_bsr_pages(pdf_path: Path) -> dict[int, set[int]]:
    pages_by_bsr: dict[int, set[int]] = defaultdict(set)
    reader = PdfReader(str(pdf_path))
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for number in extract_bsr_numbers(text):
            pages_by_bsr[number].add(page_num)
    return pages_by_bsr


def collect_artifact_refs(root: Path) -> dict[int, list[str]]:
    refs: dict[int, list[str]] = defaultdict(list)
    for path in root.rglob("source-row-inventory.md"):
        if not path.is_file() or HISTORICAL_PARTS.intersection(path.parts):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        table_header: list[str] | None = None
        for line in lines:
            if not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
            normalized = [cell.lower() for cell in cells]
            if "requirement_codes" in normalized and "in_scope" in normalized:
                table_header = normalized
                continue
            if table_header is None or len(cells) != len(table_header):
                continue
            row = dict(zip(table_header, cells))
            if row.get("in_scope", "").lower() != "yes":
                continue
            for number in extract_bsr_numbers(row.get("requirement_codes", "")):
                refs[number].append(norm_path(path.relative_to(root.parent.parent)))
    return refs


def status_for(number: int, refs: dict[int, list[str]]) -> str:
    if len(set(refs.get(number, []))) > 1:
        return "multiple-active-row-mappings"
    if number in refs:
        return "active-row-mapping"
    return "needs-row-mapping"


def render_inventory(
    root: Path,
    pdf_path: Path,
    pages_by_bsr: dict[int, set[int]],
    refs: dict[int, list[str]],
) -> str:
    lines: list[str] = []
    lines.extend(
        [
            "## Контекст",
            "",
            "- FT-пакет: `fts/AutoFin`",
            f"- Source PDF: `{norm_path(pdf_path)}`",
            "- Назначение: единый контрольный реестр `BSR` для source-to-artifact traceability.",
            "- Правило: каждый in-scope `BSR` должен быть связан с `source-row-inventory.md`, `ATOM-*`/`TC-*`, `GAP-*`, `out-of-scope` или accepted residual risk.",
            "",
            "## Summary",
            "",
        ]
    )
    total = len(pages_by_bsr)
    mapped = sum(1 for number in pages_by_bsr if number in refs)
    multiple = sum(1 for number in pages_by_bsr if len(set(refs.get(number, []))) > 1)
    missing = total - mapped
    lines.extend(
        [
            f"- BSR in PDF: `{total}`",
            f"- BSR with active in-scope row mappings: `{mapped}`",
            f"- BSR with multiple active row mappings requiring conflict review: `{multiple}`",
            f"- BSR requiring mapping/status: `{missing}`",
            "",
            "## Inventory",
            "",
            "| bsr_id | pdf_pages | likely_scope | status | artifact_refs | action |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for number in sorted(pages_by_bsr):
        pages = ", ".join(str(page) for page in sorted(pages_by_bsr[number]))
        scope = scope_guess(number)
        refs_for_code = sorted(set(refs.get(number, [])))
        status = status_for(number, refs)
        if refs_for_code:
            shown_refs = "; ".join(f"`{ref}`" for ref in refs_for_code[:3])
            if len(refs_for_code) > 3:
                shown_refs += f"; ... +{len(refs_for_code) - 3}"
            action = (
                "resolve conflicting active scope/source-version mappings"
                if status == "multiple-active-row-mappings"
                else "verify Final source parity and downstream ATOM/TC closure"
            )
        else:
            shown_refs = "-"
            action = "backfill source parity/source-row inventory or mark out-of-scope/GAP"
        lines.append(
            f"| `{bsr_code(number)}` | `{pages}` | `{scope}` | `{status}` | {shown_refs} | {action} |"
        )
    lines.extend(
        [
            "",
            "## Использование",
            "",
            "- Перед writer/reviewer loop по scope отфильтровать строки по `likely_scope`.",
            "- Для `needs-row-mapping` сначала обновить `source-parity-check.md` и `source-row-inventory.md`.",
            "- `active-row-mapping` означает только наличие активной строки `source-row-inventory.md` с `in_scope = yes`; semantic closure проверяется отдельно.",
            "- `multiple-active-row-mappings` требует source-version review: несколько активных inventories не считаются доказанной трассировкой.",
            "- Historical review cycles, `_artifact_write`, versions and arbitrary text mentions do not count as mappings.",
            "- Если эвристический `likely_scope` неверен, исправить scope-specific handoff вручную и оставить решение в `agent-decision-log.md`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="fts/AutoFin", help="AutoFin package root")
    parser.add_argument(
        "--source-pdf",
        default="fts/AutoFin/source/FT4AutoFinFinal.pdf",
        help="Selected AutoFin PDF used for structural BSR inventory",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="UTF-8 Markdown chunk output; assemble the canonical artifact with write_artifact_sections.py",
    )
    args = parser.parse_args()

    root = Path(args.root)
    pdf_path = Path(args.source_pdf)
    output_path = Path(args.output)
    pages_by_bsr = collect_pdf_bsr_pages(pdf_path)
    refs = collect_artifact_refs(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_inventory(root, pdf_path, pages_by_bsr, refs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
