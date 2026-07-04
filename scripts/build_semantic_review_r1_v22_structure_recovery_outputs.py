from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path("fts/ft-2-OF_16")
SCOPE = "ui-employment-canary-v22-structure-recovery-regression"
CYCLE_DIR = ROOT / "work" / "review-cycles" / SCOPE
OUTPUTS = CYCLE_DIR / "outputs"
PROMPTS = CYCLE_DIR / "prompts"
TD = ROOT / "work" / "test-design" / SCOPE
CANONICAL = ROOT / "test-cases" / "2-1-1-1-1-2-ui-employment-canary-v22-structure-recovery-regression.md"
STATE = CYCLE_DIR / "cycle-state.yaml"

INSTRUCTION_FILES = [
    "AGENTS.md",
    "skills/README.md",
    "references/agent/session-based-review-cycle-format.md",
    "references/agent/codex-sdk-orchestration-format.md",
    "skills/ft-test-case-reviewer/SKILL.md",
    "references/agent/reviewer-output-format.md",
    "references/agent/package-test-design-plan-format.md",
    "references/agent/dictionary-inventory-format.md",
    "references/agent/test-design-defect-taxonomy.md",
    "references/qa/review-findings-format.md",
    "references/qa/traceability-matrix-format.md",
    "references/qa/test-design-review-rubric.md",
    "references/qa/coverage-runtime-checklist.md",
    "references/qa/traceability-rules.md",
    "references/agent/workflow-state-format.md",
    "references/agent/session-log-format.md",
    "references/agent/agent-decision-log-format.md",
    "references/agent/next-step-prompt-format.md",
]

REQUIRED_INPUTS = [
    "fts/ft-2-OF_16/AGENT-NOTES.md",
    "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-contract.md",
    "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md",
    "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-parity-check.md",
    "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-row-inventory.md",
    "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md",
    f"fts/ft-2-OF_16/work/test-design/{SCOPE}/",
    f"fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml",
    f"fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/structure-preflight-r1-findings.md",
    f"fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md",
    f"fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md",
    f"fts/ft-2-OF_16/test-cases/{CANONICAL.name}",
]

SPLIT_INPUTS = [
    "artifact-write-strategy.md",
    "atomic-requirements-ledger.md",
    "coverage-gaps.md",
    "coverage-metrics.md",
    "coverage-obligation-table.md",
    "dependency-matrix.md",
    "dictionary-inventory.md",
    "fixture-catalog.md",
    "package-test-design-plan.md",
    "risk-priority-map.md",
    "source-row-completeness-matrix.md",
    "source-row-inventory.md",
    "source-table-normalization.md",
    "test-design-applicability-matrix.md",
    "test-design-decision-table.md",
    "test-design-review.md",
    "writer-quality-gate.md",
    "writer-self-check.md",
]

MATRIX_HEADERS = [
    "atom_id",
    "req_id",
    "source_path",
    "atomic_statement",
    "field_or_block",
    "condition",
    "expected_behavior",
    "covered_by_tc",
    "coverage_status",
    "gap_note",
]


def parse_md_table(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [line for line in lines if line.startswith("|")]
    if len(table_lines) < 2:
        return []
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell.replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def field_from_statement(statement: str) -> str:
    return statement.split(": ", 1)[0].strip() if ": " in statement else "-"


def condition_for(row: dict[str, str]) -> str:
    statement = row.get("atomic_statement", "")
    if " при " in statement:
        return statement.split(" при ", 1)[1].strip().strip(".")
    if "если" in statement.lower():
        return statement
    return "always"


def expected_from_statement(statement: str) -> str:
    text = statement.split(": ", 1)[1] if ": " in statement else statement
    if " при " in text:
        text = text.split(" при ", 1)[0]
    return text.strip().strip(".")


def build_matrix() -> list[dict[str, str]]:
    rows = parse_md_table(TD / "atomic-requirements-ledger.md")
    matrix: list[dict[str, str]] = []
    for row in rows:
        atom = row.get("atom_id", "")
        if not atom.startswith("ATOM-"):
            continue
        raw_status = row.get("coverage_status", "covered")
        gap_id = row.get("gap_id", "-")
        status = raw_status
        gap_note = "-"
        covered_by = row.get("covered_by_tc", "-") or "-"
        if raw_status == "gap":
            status = "unclear"
            covered_by = "-"
            gap_note = f"{gap_id} retained as accepted residual gap/unclear item for the targeted V22 subset; do not convert to executable TC without source-backed oracle."
        elif raw_status == "unclear":
            covered_by = "-"
            gap_note = "Residual non-executable structural/source-context item; not counted as covered behavior."
        matrix.append(
            {
                "atom_id": atom,
                "req_id": row.get("req_id", "-") or "-",
                "source_path": row.get("source_row_id", "-"),
                "atomic_statement": row.get("atomic_statement", ""),
                "field_or_block": field_from_statement(row.get("atomic_statement", "")),
                "condition": condition_for(row),
                "expected_behavior": expected_from_statement(row.get("atomic_statement", "")),
                "covered_by_tc": covered_by,
                "coverage_status": status,
                "gap_note": gap_note,
            }
        )
    return matrix


def write_matrix(matrix: list[dict[str, str]]) -> None:
    table_rows = [[row[h] for h in MATRIX_HEADERS] for row in matrix]
    md = "# Semantic Review R1 Traceability Matrix\n\n"
    md += "## Traceability Matrix\n\n"
    md += md_table(MATRIX_HEADERS, table_rows)
    md += "\n"
    (OUTPUTS / "semantic-review-r1-traceability-matrix.md").write_text(md, encoding="utf-8")

    write_xlsx(
        OUTPUTS / "semantic-review-r1-traceability-matrix.xlsx",
        {
            "traceability": [MATRIX_HEADERS] + table_rows,
            "meta": [
                ["field", "value"],
                ["ft_slug", "ft-2-OF_16"],
                ["scope_slug", SCOPE],
                ["stage", "semantic-review-r1"],
                ["markdown_artifact", "semantic-review-r1-traceability-matrix.md"],
            ],
        },
    )


def column_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(rows: list[list[str]]) -> str:
    xml_rows = []
    for row_idx, row in enumerate(rows, 1):
        cells = []
        for col_idx, value in enumerate(row, 1):
            ref = f"{column_name(col_idx)}{row_idx}"
            text = escape(str(value))
            style = ' s="1"' if row_idx == 1 else ""
            cells.append(f'<c r="{ref}" t="inlineStr"{style}><is><t>{text}</t></is></c>')
        xml_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '<autoFilter ref="A1:J1"/>'
        '</worksheet>'
    )


def write_xlsx(path: Path, sheets: dict[str, list[list[str]]]) -> None:
    sheet_names = list(sheets)
    workbook_sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, name in enumerate(sheet_names, 1)
    )
    workbook_rels = "".join(
        f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        for idx, _ in enumerate(sheet_names, 1)
    )
    content_types = "".join(
        f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for idx, _ in enumerate(sheet_names, 1)
    )
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{content_types}</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{workbook_sheets}</sheets></workbook>",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{workbook_rels}<Relationship Id="rId{len(sheet_names) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
            "</styleSheet>",
        )
        for idx, name in enumerate(sheet_names, 1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(sheets[name]))


def write_findings(matrix: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {}
    for row in matrix:
        counts[row["coverage_status"]] = counts.get(row["coverage_status"], 0) + 1
    findings = f"""# Semantic Review R1 Findings

## Human Summary

| item | value |
| --- | --- |
| review_mode | `semantic_traceability_test_design` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| canonical_test_cases | `test-cases/{CANONICAL.name}` |
| verdict | `not signed-off` |
| recommended_next_step | `writer-r2` |

Semantic review found no unsupported executable oracle for `GAP-005` through `GAP-015`: the invalid numeric/input classes are preserved as residual exact-mechanism gaps and are not silently treated as covered behavior. Dictionary cases use the full active values from `dictionary-inventory.md`, and executable expected results in the canonical TC file stay observable.

Semantic review cannot pass because split test-design artifacts still contain stale coverage evidence: `dependency-matrix.md` links dependency rows to wrong or non-existent `TC-*`, and `coverage-metrics.md` has inconsistent numeric counts for main-income obligations. These are writer-fixable artifact synchronization defects; the writer must not close residual mechanism gaps by inventing UI feedback.

## Coverage Summary

| coverage_status | count |
| --- | --- |
| covered | {counts.get("covered", 0)} |
| unclear | {counts.get("unclear", 0)} |
| gap | {counts.get("gap", 0)} |

## Residual Unclear Items

- `GAP-001`; `GAP-003`; `GAP-004` remain integration/setup residuals with no UI-only backend assertions.
- `GAP-005` through `GAP-015` remain exact numeric/input rejection mechanism residuals.
- `GAP-016`; `GAP-017`; `GAP-018`; `GAP-019` remain explicit targeted-subset residuals and must not be marked covered without new source evidence.

## Review Findings

### FINDING-001
**Review Mode:** test-design
**Severity:** warning
**Category:** test-design
**Coverage Dimension:** dependency
**Test Case ID:** current-scope split artifact `dependency-matrix.md`
**Traceability Ref:** ATOM-012; ATOM-013; ATOM-016; ATOM-021; ATOM-022; ATOM-023; ATOM-036
**Title:** Dependency Matrix links dependency rows to wrong or non-existent test cases

**Problem:** `dependency-matrix.md` is not semantically aligned with the canonical TC file and the Package Test Design Plan. It claims dependency coverage through unrelated or missing `TC-*`, so the split artifact cannot be used as reliable evidence for dependency coverage.

**Evidence:**
- `DEP-V22-002` links add-income block visibility to `TC-EMP-V22-012`, but `TC-EMP-V22-012` verifies `Визуальная информация = Да`, while add-income block creation is `TC-EMP-V22-006`.
- `DEP-V22-003` links created additional-income fields to `TC-EMP-V22-013`, but `TC-EMP-V22-013` verifies `DICT-005` visual-assessment checkboxes; the created income fields are covered by `TC-EMP-V22-007`.
- `DEP-V22-005` links `Визуальная информация = Да` to non-existent `TC-EMP-V22-019` and `TC-EMP-V22-021`; canonical cases stop at `TC-EMP-V22-015`.
- `DEP-V22-006` links the inverse visual-info branch to `TC-EMP-V22-015`, but that case verifies `Следующий шаг` navigation; the inverse branch is `TC-EMP-V22-009`.

**Required Change:** Update `dependency-matrix.md` so every dependency row points to the actual covering `TC-*` or to the applicable `GAP-*`: expected mappings include add-income block creation -> `TC-EMP-V22-006`, created income fields -> `TC-EMP-V22-007`, visual-info positive/requiredness branch -> `TC-EMP-V22-012` and `TC-EMP-V22-014`, visual-info inverse branch -> `TC-EMP-V22-009`.

**Source Reference:** `work/test-design/{SCOPE}/dependency-matrix.md`; canonical TC file; `package-test-design-plan.md`

**Status:** open

### FINDING-002
**Review Mode:** test-design
**Severity:** warning
**Category:** coverage
**Coverage Dimension:** numeric
**Test Case ID:** current-scope split artifact `coverage-metrics.md`
**Traceability Ref:** ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011
**Title:** Main-income numeric coverage metrics do not match listed obligations and gaps

**Problem:** `coverage-metrics.md` reports inconsistent counts for `main-income-numeric`, which weakens the reviewer evidence for the V22 negative-oracle recovery. The row lists six residual invalid-class gaps but reports only five gaps.

**Evidence:**
- `coverage-metrics.md` row `main-income-numeric` states `obligations_total = 8`, `covered = 3`, `gap = 5`.
- The same row's evidence lists `GAP-005`, `GAP-006`, `GAP-007`, `GAP-008`, `GAP-009` and `GAP-010`, which is six gap obligations.
- `coverage-obligation-table.md` also has six main-income invalid obligations: below minimum, letters, spaces, special chars, decimal separator and sign.

**Required Change:** Recalculate the `main-income-numeric` row in `coverage-metrics.md` so `obligations_total`, `covered`, `gap` and evidence agree with `coverage-obligation-table.md`, `package-test-design-plan.md` and the reviewer matrix. Do not remove `GAP-005` through `GAP-010` or convert them to executable TCs without a source-backed oracle.

**Source Reference:** `work/test-design/{SCOPE}/coverage-metrics.md`; `coverage-obligation-table.md`; `package-test-design-plan.md`

**Status:** open

## Gate Decision Result

Semantic review round 1 routes to `writer-r2`: open warning findings remain. Residual mechanism/setup gaps are accepted as non-executable V22 residuals and are not the requested writer fix.
"""
    (OUTPUTS / "semantic-review-r1-findings.md").write_text(findings, encoding="utf-8")


def write_prompt() -> None:
    prompt = f"""## Handoff Prompt

## Stage Goal

Run `ft-test-case-writer` in session semantic revision mode for V22. Fix the semantic review R1 split-artifact synchronization findings without expanding scope and without inventing UI/backend behavior for residual gaps.

## Cycle Context

- `cycle_id`: `ft-2-OF_16-ui-employment-canary-v22-structure-recovery-regression`
- `scope_slug`: `{SCOPE}`
- `current_stage`: `writer-r2`
- `semantic_round`: `1`
- canonical test cases: `test-cases/{CANONICAL.name}`
- test-design dir: `work/test-design/{SCOPE}/`
- cycle state: `work/review-cycles/{SCOPE}/cycle-state.yaml`
- semantic findings: `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-findings.md`
- semantic matrix: `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.md`

## Instruction Loading

Before writer decisions, run:

```powershell
python scripts/resolve_instruction_context.py --scenario writer.session_semantic_revision --budget-report --fail-on-budget
```

Read every selected required file from resolver output. Record resolver command, budget status and selected files in `outputs/writer-session-log.writer-r2.md`.

## Required Inputs

- `AGENT-NOTES.md`
- `work/stage-handoffs/01-ui-employment/scope-contract.md`
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/01-ui-employment/source-parity-check.md`
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`
- `work/test-design/{SCOPE}/`
- `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-findings.md`
- `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.md`
- canonical test-case file listed above

## Required Changes

1. Fix `FINDING-001`: update `dependency-matrix.md` so dependency rows point to actual covering cases or explicit gaps. Expected mappings include:
   - add-income block creation -> `TC-EMP-V22-006`;
   - created income fields -> `TC-EMP-V22-007`;
   - visual-info positive/display branch -> `TC-EMP-V22-012`;
   - visual-info requiredness branch -> `TC-EMP-V22-014`;
   - visual-info inverse branch -> `TC-EMP-V22-009`.
2. Fix `FINDING-002`: recalculate `coverage-metrics.md` for `main-income-numeric` so totals and gap count match the six listed residual gaps `GAP-005` through `GAP-010` and the coverage obligation table.
3. Create writer response artifact `outputs/writer-r2-response.md` with canonical response blocks for each finding.
4. Update writer session log and decision log for `writer-r2`.
5. Update `cycle-state.yaml` to route back to `semantic-review-r2` with `stage_status: semantic-review-ready`, `semantic_round: 2`, and active prompt `prompts/prompt.semantic-review-r2.md`.

## Do Not Do

- Do not edit residual gaps into covered behavior.
- Do not create executable invalid numeric/input TCs for `GAP-005` through `GAP-015` unless a source-backed deterministic oracle is added.
- Do not invent filtering, clearing, disabled state, exact validation message, blocked transition or backend effects.
- Do not expand the canary into full employment-section coverage.
- Do not edit `codex-session-map.yaml`.

## Expected Outputs

- Updated split artifacts under `work/test-design/{SCOPE}/`.
- Optional canonical TC edits only if needed by the findings; current findings are split-artifact synchronization issues.
- `work/review-cycles/{SCOPE}/outputs/writer-r2-response.md`
- `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r2.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r2.md`
- `work/review-cycles/{SCOPE}/prompts/prompt.semantic-review-r2.md`
- Updated `cycle-state.yaml`

## Gate Completion

Writer-r2 is complete only when both R1 findings have canonical `fixed` or justified `not-fixed-scope`/`needs-clarification` responses, split artifacts are synchronized, and `cycle-state.yaml` routes to `semantic-review-r2`.
"""
    (PROMPTS / "prompt.writer-r2.md").write_text(prompt, encoding="utf-8")


def write_logs() -> None:
    inputs_read = [
        "- `python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget` - resolver command; budget status `pass (262.2 / 290.0 KiB)`.",
    ]
    inputs_read += [f"- `{path}` - selected required instruction file read before reviewer decisions." for path in INSTRUCTION_FILES]
    inputs_read += [f"- `{path}` - required semantic-review-r1 input." for path in REQUIRED_INPUTS]
    inputs_read += [f"- `fts/ft-2-OF_16/work/test-design/{SCOPE}/{name}` - split test-design artifact read for semantic review." for name in SPLIT_INPUTS]

    log = f"""# Semantic Review R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-reviewer` |
| mode | `semantic_traceability_test_design` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| started_from | `cycle-state.yaml` |
| status_after | `semantic-revision-needed` |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-findings.md` | `review artifact` | `file-based helper write` | `yes` | `scripts/build_semantic_review_r1_v22_structure_recovery_outputs.py` | `yes` |
| `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.md` | `generated matrix` | `file-based helper write` | `yes` | `scripts/build_semantic_review_r1_v22_structure_recovery_outputs.py` | `yes` |
| `work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.xlsx` | `generated xlsx` | `stdlib zip/xml xlsx write` | `yes` | `scripts/build_semantic_review_r1_v22_structure_recovery_outputs.py` | `yes` |

## Inputs Read

{chr(10).join(inputs_read)}

## Inputs Not Used

- Historical canary v1-v21 artifacts outside the explicitly referenced writer inputs - not used as requirement sources or templates.
- UI automation artifacts - out of scope for semantic review.

## Key Decisions

- Accepted the V22 targeted subset boundary from `cycle-state.yaml`: review checked negative-oracle recovery, not full employment-section sign-off.
- Treated `GAP-005` through `GAP-015` as valid residual exact-mechanism gaps because no source-backed deterministic rejection oracle is available.
- Rejected semantic pass because split design artifacts contain stale dependency links and inconsistent main-income numeric metrics.
- Routed to `writer-r2`; requested artifact synchronization only, not invented behavior.

## Risks And Fallbacks

- Residual gaps remain open by design for the targeted V22 subset; future full-section sign-off must not treat them as covered.
- Initial PowerShell output for some Cyrillic instruction files showed mojibake; source evidence was read again through explicit UTF-8 paths and distorted stdout was not used.

## Validation

- `python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget` - pass, `262.2 / 290.0 KiB`.
- Manual semantic checks: canonical TC expected results, gap preservation, dictionary values, dependency matrix links, coverage metrics consistency.

## Contamination Check

- Review used only the active V22 canonical file, V22 split artifacts, stage handoff source artifacts, package notes and active cycle outputs.
- Historical canary artifacts were not used to create requirements or expected results.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved reviewer instruction context | pass | resolver output: 18 files, budget pass |
| 2 | Read selected instruction files | pass | files listed under Inputs Read |
| 3 | Read package/source/scope inputs | pass | `AGENT-NOTES.md`; scope/parity/row/mockup inventories |
| 4 | Read V22 canonical and split artifacts | pass | canonical TC; test-design directory |
| 5 | Ran semantic traceability/test-design review | warnings found | `semantic-review-r1-findings.md` |
| 6 | Wrote reviewer matrix and XLSX duplicate | pass | `semantic-review-r1-traceability-matrix.*` |
| 7 | Prepared writer-r2 prompt and state transition | pass | `prompts/prompt.writer-r2.md`; `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| GAP-005..GAP-015 admissibility | pass | no executable invalid numeric/input TC remains | keep as residual unless source evidence appears |
| Dictionary active values | pass | TC-001, TC-008, TC-013 match `DICT-001`, `DICT-004`, `DICT-005` active values | none |
| Dependency matrix semantic links | fail | `DEP-V22-002`/`003`/`005`/`006` wrong or stale TC ids | writer-r2 |
| Coverage metrics consistency | fail | `main-income-numeric` gap count contradicts listed gaps | writer-r2 |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic mojibake in initial PowerShell stdout | plain console output as evidence | explicit UTF-8 file reads via `Get-Content -Encoding UTF8` | `n/a` | `n/a` | none; distorted stdout discarded | none |
| `TF-002` | reviewer matrix requires XLSX duplicate and `openpyxl` is unavailable | manual spreadsheet editing / `openpyxl` workbook write | file-based helper script with standard-library zip/xml XLSX writer | `scripts/build_semantic_review_r1_v22_structure_recovery_outputs.py` | `yes` | low | keep Markdown/XLSX rows synchronized |

## Handoff Notes For Next Session

- Writer-r2 should change only split-artifact synchronization unless it finds a direct dependency of the findings.
- Do not close residual mechanism gaps by adding unsupported invalid numeric/input expected results.
"""
    (OUTPUTS / "reviewer-session-log.semantic-review-r1.md").write_text(log, encoding="utf-8")

    decision_log = f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| stage | `semantic-review-r1` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | instruction resolver | Proceed with semantic review | Resolver passed and all selected required files were read | `reviewer-session-log.semantic-review-r1.md` | high | applied |
| `DEC-002` | 2 | `scope-boundary` | `cycle-state.yaml`; accepted risks | Review targeted V22 subset, not full employment section | V22 is a canary for negative-oracle recovery and structure recovery | findings; matrix | high | applied |
| `DEC-003` | 3 | `gap` | `GAP-005`..`GAP-015` | Keep invalid numeric/input classes as residual unclear/gap items | Source lacks deterministic observable enforcement mechanism | traceability matrix | high | applied |
| `DEC-004` | 4 | `test-design` | `dependency-matrix.md` | Open warning for stale dependency TC links | Wrong/non-existent TC ids affect dependency coverage evidence | `FINDING-001` | high | applied |
| `DEC-005` | 5 | `coverage` | `coverage-metrics.md` | Open warning for inconsistent main-income numeric counts | Metrics contradict listed gaps and obligation table | `FINDING-002` | high | applied |
| `DEC-006` | 6 | `routing` | open warning findings | Route to `writer-r2` | Semantic review cannot pass with warning findings | `cycle-state.yaml`; `prompt.writer-r2.md` | high | applied |
"""
    (OUTPUTS / "agent-decision-log.semantic-review-r1.md").write_text(decision_log, encoding="utf-8")


def update_state() -> None:
    text = STATE.read_text(encoding="utf-8")
    text = text.replace("current_stage: semantic-review-r1", "current_stage: writer-r2")
    text = text.replace("stage_status: semantic-review-ready", "stage_status: semantic-revision-needed")
    text = text.replace(
        f"active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.semantic-review-r1.md",
        f"active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.writer-r2.md",
    )
    marker = "accepted_risks:\n"
    additions = [
        f"  - work/review-cycles/{SCOPE}/outputs/semantic-review-r1-findings.md",
        f"  - work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.md",
        f"  - work/review-cycles/{SCOPE}/outputs/semantic-review-r1-traceability-matrix.xlsx",
        f"  - work/review-cycles/{SCOPE}/outputs/reviewer-session-log.semantic-review-r1.md",
        f"  - work/review-cycles/{SCOPE}/outputs/agent-decision-log.semantic-review-r1.md",
        f"  - work/review-cycles/{SCOPE}/prompts/prompt.writer-r2.md",
    ]
    for item in additions:
        if item not in text:
            text = text.replace(marker, "\n".join(additions) + "\n" + marker)
            break
    text = text.replace(
        "blocking_reasons: []",
        "blocking_reasons:\n  - FINDING-001: dependency-matrix.md has stale or wrong TC links.\n  - FINDING-002: coverage-metrics.md main-income numeric counts are inconsistent.",
    )
    text = text.replace(
        "blocking_findings: []",
        "blocking_findings:\n  - FINDING-001\n  - FINDING-002",
    )
    STATE.write_text(text, encoding="utf-8")


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    matrix = build_matrix()
    write_matrix(matrix)
    write_findings(matrix)
    write_prompt()
    write_logs()
    update_state()


if __name__ == "__main__":
    main()
