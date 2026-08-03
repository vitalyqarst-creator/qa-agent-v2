# Source Quality Strict Warning Review - 2026-05-25

## Scope

This review explains the current `--source-quality-policy strict` warnings for active FT source documents.

Validation command:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --source-quality-policy strict
```

Current strict result:

- errors: `0`
- warnings: `4`
- info: `3`

## Findings

| Source | Strict warning | Evidence | Assessment |
| --- | --- | --- | --- |
| FT-5 main DOCX | `source-quality-many-untitled-sections` | 39 non-preface sections, 39 generated `section-*` ids, 0 numeric ids | Real traceability risk. The DOCX uses heading styles, but the visible heading text does not contain numeric section ids for business sections. |
| FT-5 main DOCX | `source-quality-no-numeric-sections` | first extracted ids are `section-1`, `section-2`, `section-3`, ... | Real traceability risk. Section filters by numeric prefix cannot work reliably for this source. |
| FT-5 main DOCX | `source-quality-oversized-blocks` | `section-11:13915`, `section-41:16532` | Manageable extraction risk. Defensive chunking splits downstream chunks, but reviewers should know these source sections are large table/text blocks. |
| FT-2 main DOCX | `source-quality-oversized-blocks` | `2.2.1.1:29192`, `2.2.2.1:15978`, `section-19:14759` | Manageable extraction risk. Numeric ids exist for core sections, but large status-model and UI-property blocks require chunk-aware review. |

## Root Cause

The current DOCX parser intentionally uses a conservative rule:

- Word paragraph style must match `Heading N`;
- section id is extracted only from a numeric prefix in the visible heading text;
- otherwise the loader assigns generated ids like `section-10`.

This is simple and testable, but it does not reconstruct Word auto-numbering or domain-specific implicit section numbers.

For FT-5, the relevant business headings look like:

- `Описание свойств полей формы в разделе «Документы клиента»`
- `Описание действий в разделе «Документы клиента»`
- `Список допустимых тегов в печатных формах`

Those headings have no numeric prefix in the extracted text. Most of them also do not expose a useful `numPr` value through `python-docx`, so silently inventing numeric ids would be unsafe.

## Decision

Do not implement automatic numeric-id reconstruction for FT-5 at this stage.

Rationale:

- It would likely create false traceability: generated numbers could look authoritative while not matching the real FT document.
- The current workflow can still operate through title/path matching and explicit source-selection artifacts.
- Strict mode already exposes the limitation when a new or changed source needs stronger review.

Treat the current warnings as legacy source limitations, not as validator bugs.

## Required Handling

When working with FT-5:

- do not rely on numeric `section_prefix` filters;
- select sections by title or full-title text;
- record source limitations in `source-selection.md` or `scope-coverage-gaps.md` before downstream writing;
- keep reviewer traceability anchored to visible titles and extracted chunk ids.

When working with FT-2:

- numeric filters are usable for sections such as `2.2.1.1` and `2.2.2.1`;
- oversized blocks require chunk-aware review;
- do not treat one generated UI-property section id as a full source failure.

When onboarding new FT packages or replacing source DOCX files:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning --source-quality-policy strict
```

If strict mode emits warnings for a new source, either:

1. document the limitation and justify proceeding, or
2. fix the parser/source structure before writer/reviewer work.

## Rejected Alternatives

### Reconstruct Word Numbering Automatically

Rejected for now. Word numbering is not consistently exposed for the affected business headings, and false ids would be worse than explicit generated ids.

### Keep All Source-Quality Risks As Info Forever

Rejected. This hides real onboarding risk for new sources. The current compatible/strict split is a better trade-off.

### Fail Current Root Validation By Default

Rejected. Existing FT-5 and FT-2 packages already depend on these historical source shapes. Breaking the default gate would create process noise without fixing extraction.

