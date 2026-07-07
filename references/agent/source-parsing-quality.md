# Source Parsing Quality

Source parsing is an upstream quality gate for FT-based test case generation. DOCX remains the authoritative main FT source of truth, but XHTML is mandatory as the primary machine-readable extraction source for tables, lists, nested lists, value sets and source rows.

## Contract

- `preview_chunks(..., max_chars=N)` must not return chunks longer than `N`.
- Oversized source blocks must be split defensively instead of leaking over the chunk limit.
- Source quality inspection should flag suspicious extraction shape before downstream test writing:
  - no non-preface requirement sections;
  - too many generated `section-*` ids;
  - no numeric section ids;
  - source blocks larger than the chunk limit.

## Helper

Run source quality inspection with:

```powershell
python skills/ft-test-case-writer/scripts/extract_requirement_sections.py <source.docx> --mode quality --max-chars 12000
```

This helper reports source parsing risks. It does not replace reviewer traceability checks.

It also does not replace `source-selection.md` or `source-parity-check.md`. `source-selection.md` proves that mandatory XHTML is available; source parsing quality checks whether one extracted source is structurally usable; source parity checks whether DOCX and PDF versions of the same FT preserve the same scope boundaries, requirement IDs and table rows.

## Validator Integration

`scripts/validate_agent_artifacts.py` checks active source DOCX parseability and validates mandatory XHTML availability/path through active `source-selection.md` artifacts.

The validator fails on:

- active DOCX files that cannot be parsed;
- generated chunks that still exceed `max_chars` after defensive splitting.

The validator reports as `info`:

- generated `section-*` heavy extraction;
- missing numeric section ids;
- source blocks that required defensive splitting.

This keeps the root validation signal focused on active handoff inputs instead of historical source aliases and backups.

## Escalation Policy

The validator supports two severity policies:

```powershell
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning --source-quality-policy compatible
python scripts/validate_agent_artifacts.py --root . --json --fail-on warning --source-quality-policy strict
```

`compatible` is the default policy for existing repositories and historical FT packages:

- unreadable active DOCX -> `error`;
- chunks still larger than `max_chars` after defensive splitting -> `error`;
- no non-preface requirement sections -> `warning`;
- generated `section-*` heavy extraction -> `info`;
- missing numeric section ids -> `info`;
- source blocks that required defensive splitting -> `info`.

`strict` is the policy for new or materially changed source documents before downstream writer/reviewer work:

- unreadable active DOCX -> `error`;
- chunks still larger than `max_chars` after defensive splitting -> `error`;
- no non-preface requirement sections -> `warning`;
- generated `section-*` heavy extraction -> `warning`;
- missing numeric section ids -> `warning`;
- source blocks that required defensive splitting -> `warning`.

Use `strict` when:

- onboarding a new FT package;
- replacing the main source DOCX;
- changing source parsing logic;
- preparing a new large scope where stable section ids matter for traceability.

Do not silently downgrade `strict` warnings. Either inspect the extracted structure and document the limitation in `source-selection.md` / `scope-coverage-gaps.md`, or fix the source parsing before writing downstream test cases.

Current legacy warning assessment is documented in:

- `references/agent/source-quality-strict-warning-review-2026-05-25.md`
