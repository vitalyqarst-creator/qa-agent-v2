# Artifact Write Strategy Format

## Purpose

Large generated Markdown artifacts must be written through files, not through shell arguments, PowerShell here-strings, inline Python/Node commands, or ad-hoc temporary generators.

This rule applies before the first write attempt. Hitting a Windows command-line limit and then switching to chunked writing is a failed preflight, not a clean fallback.

## Canonical Helper

Use the committed helper:

```powershell
python scripts\write_artifact_sections.py --manifest <manifest.json>
```

The manifest is UTF-8 JSON. Relative paths are resolved from the manifest file directory.

Minimal manifest:

```json
{
  "target_path": "../../test-cases/2.3-ui-main-info.md",
  "preamble_file": "chunks/00-preamble.md",
  "sections": [
    {
      "level": 2,
      "heading": "Artifact Write Strategy",
      "content_file": "chunks/01-artifact-write-strategy.md"
    },
    {
      "level": 2,
      "heading": "Source Table Normalization",
      "content_file": "chunks/02-source-table-normalization.md"
    }
  ]
}
```

Use `--dry-run` before the real write when creating a new manifest.

## When It Is Mandatory

Use `scripts/write_artifact_sections.py` as the default writer when any condition is true:

- generated artifact is package-based or table-heavy;
- expected Markdown is larger than `20 000` characters;
- expected output has more than `20` `TC-*` or more than `30` `ATOM-*`;
- artifact is `source-row-inventory.md`;
- artifact is `source-normalization-diagnostic.md`;
- artifact is a canonical test-case file;
- artifact is a large traceability matrix or review-cycle table.

`scripts/update_markdown_section.py` remains acceptable for small targeted edits to one existing section. It is not the primary writer for large/generated artifacts.

## Session Log Gate

For audit runs, add a `## Artifact Write Strategy` section to the session log before writing generated artifacts:

```md
## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/stage-handoffs/05-ui-main-info/source-normalization-diagnostic.md` | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest sections.json` | `yes` |
```

Rules:

- `declared_before_first_write` must be `yes`;
- `helper` must name `scripts/write_artifact_sections.py` for large/generated artifacts;
- `forbidden_methods_checked` must be `yes`;
- do not mark command-line limit fallback as recovered cleanly.

## Validator Expectations

Validator warnings:

- `session-log-artifact-write-strategy-missing`;
- `session-log-artifact-write-strategy-invalid-table`;
- `session-log-artifact-write-strategy-not-preflight`;
- `session-log-artifact-writer-helper-missing`;
- `session-log-artifact-write-strategy-unsafe`;
- `session-log-forbidden-initial-one-shot-write`;
- `artifact-write-strategy-helper-missing`.

In clean eval runs with `--fail-on warning`, any of these warnings should block the stage from being treated as clean.
