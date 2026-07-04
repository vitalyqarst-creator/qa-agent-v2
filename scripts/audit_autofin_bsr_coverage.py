"""Audit AutoFin BSR traceability across source and artifacts.

This script intentionally treats PDF BSR codes as authoritative because the
AutoFin DOCX extraction exposes only a small subset of requirement codes.
It writes a Markdown source inventory that can be used as a package-level
gate before test-case writer/reviewer work.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader


TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".txt", ".csv"}
IGNORED_FILE_PATTERNS = (
    "autofin-bsr-source-inventory.md",
    "requirements-artifact-coverage-audit",
    "open-scope-coverage-gaps",
    "validator-report",
)


def norm_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def bsr_code(value: int) -> str:
    return f"BSR {value}"


def extract_bsr_numbers(text: str) -> set[int]:
    return {int(match) for match in re.findall(r"BSR\s*([0-9]+)", text, flags=re.I)}


def scope_guess(number: int) -> str:
    """Best-effort routing based on known AutoFin PDF BSR ranges."""
    if 1 <= number <= 34:
        return "01-applications-menu-search"
    if 35 <= number <= 38:
        return "04-universal-application-common-actions"
    if 39 <= number <= 69:
        return "06-application-card-client-personal-data"
    if 70 <= number <= 75:
        return "07-application-card-document-recognition-popup"
    if 76 <= number <= 106:
        return "08-application-card-passport-current-and-previous"
    if 107 <= number <= 153:
        return "09-application-card-client-addresses"
    if 154 <= number <= 197:
        return "10-application-card-client-contacts-and-extra-info"
    if 198 <= number <= 232:
        return "11-application-card-documents-and-questionnaire-files"
    if 233 <= number <= 255:
        return "12-application-card-participants-coborrower-pledger"
    if 256 <= number <= 302:
        return "13-application-card-employment-income-gosuslugi"
    if 303 <= number <= 309:
        return "17-visual-assessment-criteria"
    if 310 <= number <= 316:
        return "16-consents-and-checks"
    if 317 <= number <= 320:
        return "15-application-card-next-action-validation"
    if number == 321:
        return "04-universal-application-common-actions"
    return "unmapped"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1251", errors="ignore")


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
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        normalized_name = path.name.lower()
        if any(pattern in normalized_name for pattern in IGNORED_FILE_PATTERNS):
            continue
        text = read_text(path)
        for number in extract_bsr_numbers(text):
            refs[number].append(norm_path(path.relative_to(root.parent.parent)))
    return refs


def status_for(number: int, refs: dict[int, list[str]]) -> str:
    if number in refs:
        return "mapped-in-artifacts"
    return "needs-row-mapping"


def render_inventory(root: Path, pages_by_bsr: dict[int, set[int]], refs: dict[int, list[str]]) -> str:
    lines: list[str] = []
    lines.extend(
        [
            "# AutoFin BSR Source Inventory",
            "",
            "## Контекст",
            "",
            "- FT-пакет: `fts/AutoFin`",
            "- Source PDF: `fts/AutoFin/source/AutoFinPreFinal.pdf`",
            "- Назначение: единый контрольный реестр `BSR` для source-to-artifact traceability.",
            "- Правило: каждый in-scope `BSR` должен быть связан с `source-row-inventory.md`, `ATOM-*`/`TC-*`, `GAP-*`, `out-of-scope` или accepted residual risk.",
            "",
            "## Summary",
            "",
        ]
    )
    total = len(pages_by_bsr)
    mapped = sum(1 for number in pages_by_bsr if number in refs)
    missing = total - mapped
    lines.extend(
        [
            f"- BSR in PDF: `{total}`",
            f"- BSR currently mentioned in artifacts: `{mapped}`",
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
            action = "verify in-scope coverage or explicit residual status"
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
            "- Для `mapped-in-artifacts` проверить, что ссылка не случайная: код должен относиться к текущему scope и быть связан с конкретным source row/atom/gap.",
            "- Если эвристический `likely_scope` неверен, исправить scope-specific handoff вручную и оставить решение в `agent-decision-log.md`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="fts/AutoFin", help="AutoFin package root")
    parser.add_argument(
        "--output",
        default="fts/AutoFin/work/stage-handoffs/autofin-bsr-source-inventory.md",
        help="Markdown output path",
    )
    args = parser.parse_args()

    root = Path(args.root)
    pdf_path = root / "source" / "AutoFinPreFinal.pdf"
    output_path = Path(args.output)
    pages_by_bsr = collect_pdf_bsr_pages(pdf_path)
    refs = collect_artifact_refs(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_inventory(root, pages_by_bsr, refs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
