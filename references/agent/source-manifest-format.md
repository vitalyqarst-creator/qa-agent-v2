# Source Manifest Format

Source Manifest is a machine-checkable passport for one FT source version. It records which FT package and source version were ingested, which source files belong to that version, file hashes and metadata, the OOXML coverage audit location, and whether ingestion can proceed to downstream stages.

It is not a requirements registry and it does not contain atomic requirements, `req_uid`, test cases, or version diff results.

## Required JSON Files

For source version `<version>`, the builder writes:

- `source-manifest.<version>.json`
- `source-coverage-audit.<version>.json`

The coverage audit file must use `references/agent/ooxml-source-coverage-audit-format.md`.

## Manifest Shape

```json
{
  "manifest_version": "1.0",
  "ft_slug": "AutoFin",
  "source_version": "autofin-final-v1",
  "created_at_utc": "2026-07-04T00:00:00Z",
  "created_by_tool": "scripts/build_source_manifest.py",
  "source_files": [
    {
      "path": "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.docx",
      "role": "main_docx",
      "exists": true,
      "size_bytes": 12345,
      "sha256": "64 lowercase hex characters",
      "modified_time_utc": "2026-07-04T00:00:00Z",
      "file_suffix": ".docx",
      "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "notes": []
    }
  ],
  "primary_docx": "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.docx",
  "primary_pdf": "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.pdf",
  "primary_xhtml": "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.xhtml",
  "ooxml_coverage_audit_path": "fts/AutoFin/requirements/source-coverage-audit.autofin-final-v1.json",
  "coverage_audit_created": true,
  "ooxml_summary": {
    "zip_entries_seen": 24,
    "xml_parts_extracted": 19,
    "rels_parts_extracted": 3,
    "binary_parts_seen": 2,
    "extraction_warnings": 2,
    "comments_count": 0,
    "footnotes_count": 0,
    "endnotes_count": 0,
    "headers_count": 0,
    "footers_count": 0,
    "hidden_text_count": 0,
    "tracked_insert_count": 0,
    "tracked_delete_count": 0,
    "custom_xml_parts_count": 0
  },
  "ingestion_status": "pass-with-warnings",
  "blocking_reasons": [],
  "warnings": [
    "Binary part seen but not content-extracted: word/media/image1.png"
  ],
  "clean_run_audit": {
    "files_read": [
      "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.docx",
      "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.pdf",
      "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.xhtml"
    ],
    "forbidden_name_patterns": ["expected", "private", "golden", "answer", "solution", "bundle"],
    "forbidden_files_detected_nearby": [],
    "forbidden_files_in_inputs": [],
    "forbidden_files_read": [],
    "clean_run_claim": true,
    "clean_run_status": "clean"
  },
  "extraction_method": "native_ooxml_zip_lxml",
  "parser_mode": "strict"
}
```

## Source File Roles

Allowed `role` values:

- `main_docx`
- `main_pdf`
- `main_xhtml`
- `support`
- `mockup`
- `other`

Every passed source file must have a `SourceFileEntry`, even when it is missing. Missing entries use `exists=false`, null size/hash/mtime, and a note explaining the missing file.

## Ingestion Status

`blocked`:

- `primary_docx` is missing or was not provided;
- DOCX cannot be opened as ZIP;
- critical parts are not parsed: `[Content_Types].xml`, `word/document.xml`, `_rels/.rels`;
- `parser_mode` is not `strict` without an explicit tolerant flag;
- coverage audit is not created.

`pass-with-warnings`:

- DOCX was read and critical parts were parsed;
- binary parts exist without OCR/content extraction;
- non-critical XML warnings exist;
- comments, footnotes, endnotes, tracked changes, hidden text, or custom XML are present and require downstream attention.

`pass`:

- DOCX was read;
- critical parts were parsed;
- no warnings are present.

Binary warnings must not make ingestion `blocked`. They document that OCR/content extraction was not performed.

If ingestion is blocked before OOXML coverage can be created, `coverage_audit_created` must be `false`. `ooxml_coverage_audit_path` may still show the intended output path, but downstream tooling must use `coverage_audit_created=false` as the authoritative signal that no coverage audit file was produced.

## Clean Run Audit

`clean_run_audit.files_read` lists every existing source input that was actually read for hash/metadata calculation:

- primary DOCX;
- primary PDF;
- primary XHTML;
- support files;
- mockups;
- other explicitly passed source files.

Missing source inputs are not included in `files_read` because no hash was computed for them.

`forbidden_files_detected_nearby` lists forbidden-name files near the primary DOCX. These files may not have been read.

`forbidden_files_in_inputs` lists forbidden-name files explicitly passed as DOCX/PDF/XHTML/support/mockup/other inputs.

`forbidden_files_read` lists forbidden-name inputs that existed and were read for SHA-256.

Clean-run status values:

- `clean`: no forbidden-name files are nearby or read as inputs;
- `contaminated-risk`: forbidden-name files are present near the DOCX but were not read as inputs;
- `contaminated`: a forbidden-name input existed and was read.

`clean_run_claim` is `true` only when `clean_run_status` is `clean`.

## Downstream Rules

- A Source Manifest can unlock requirements extraction, but it is not itself a requirements registry.
- Do not infer atomic requirements, `req_uid`, or source diffs from this manifest.
- Downstream tooling must read `ooxml_coverage_audit_path` before relying on DOCX ingestion completeness.
- If `ingestion_status=blocked`, downstream extraction must stop or explicitly record an override outside this manifest.
