# Requirements Registry Format

Requirements Registry is a machine-checkable artifact for one FT source version. It is built from a Source Manifest, OOXML coverage audit, and primary DOCX source nodes.

It is not a requirements diff, impact analysis, writer/reviewer workflow, or test-case update mechanism.

## Required Files

For source version `<version>`, the builder writes:

- `requirements.<version>.jsonl`
- `requirements-summary.<version>.json`

Recommended package location:

```text
fts/<ft-slug>/requirements/requirements.<source-version>.jsonl
fts/<ft-slug>/requirements/requirements-summary.<source-version>.json
```

Each JSONL line is one registry entry: an atomic requirement, explicit `gap`, `unclear` statement, or `source_only` source statement.

## Entry Shape

```json
{
  "req_uid": "REQ-AUTOFIN-7A12D9C41B22",
  "atom_id": "ATOM-000001",
  "source_version": "autofin-final-v1",
  "ft_slug": "AutoFin",
  "source_req_id": "BSR 115",
  "source_row_id": null,
  "section_id": "14",
  "scope_slug": null,
  "package_id": null,
  "requirement_type": "requiredness",
  "object": null,
  "condition": null,
  "expected_behavior": "BSR 115 Адрес регистрации обязателен, если Ввести вручную = Нет.",
  "source_text": "BSR 115 Адрес регистрации обязателен, если Ввести вручную = Нет.",
  "normalized_text": "BSR 115 Адрес регистрации обязателен, если Ввести вручную = Нет.",
  "source_anchors": [
    {
      "source_doc": "fts/AutoFin/source/FT4AutoFinFinal/FT4AutoFinFinal.docx",
      "source_version": "autofin-final-v1",
      "part": "word/document.xml",
      "xpath": "/w:document/w:body/w:p[1]/w:r/w:t/text()",
      "node_id": "ooxml-node-000001",
      "value_type": "text",
      "flags": [],
      "aggregate_kind": null,
      "aggregate_confidence": null
    }
  ],
  "semantic_fingerprint": "requiredness|||bsr 115 адрес регистрации обязателен, если ввести вручную = нет.",
  "text_hash": "sha256:64 lowercase hex characters",
  "status": "active",
  "confidence": "medium",
  "warnings": []
}
```

## Fields

`req_uid` is deterministic for the same FT slug, normalized text, source requirement id, and requirement type. It must not depend only on JSONL row number.

`atom_id` is a local sequential id inside one generated registry file.

`source_req_id` is extracted conservatively from patterns such as `BSR <number>`, `GSR <number>`, `REQ-<number>`, `REQ <number>`, `ID <number>`, or local codes like `ABC-123`.

`source_row_id`, `scope_slug`, and `package_id` are nullable in Stage 3. They can be filled by later scoped workflows, but the registry builder must not invent them.

`object`, `condition`, and `expected_behavior` must not be invented. Stage 3 may leave `object` and `condition` null. For an active entry, `expected_behavior` may be the normalized source statement when the rule classifier detects a behavior signal but cannot safely split the statement further.

`source_anchors` must reference OOXML `SourceNode` data: `part`, `xpath`, `node_id`, `value_type`, flags, and aggregate metadata.

`semantic_fingerprint` is a deterministic normalized string used for stable matching inside one version. It is not a cross-version diff key yet.

`text_hash` is `sha256:<hash>` over `normalized_text`.

## Status Values

Allowed `status` values:

- `active`: a source-backed statement looks like a checkable requirement and has a behavior signal.
- `gap`: important source information is present but required behavior is missing. Stage 3 extractor may use `unclear` instead when it cannot distinguish safely.
- `unclear`: source text looks requirement-adjacent but cannot be safely atomized or interpreted.
- `source_only`: source text is metadata, comment, document property, technical source value, or non-checkable text.

The registry must be honest. If the extractor cannot confidently atomize a statement, it must not create a silently active requirement.

## Confidence

Allowed `confidence` values:

- `high`
- `medium`
- `low`

Stage 3 conservative extraction usually produces `medium` for direct active text and `low` for `source_only` or `unclear` entries. Aggregate-derived entries must not exceed `medium`.

## Requirement Type Detection

Stage 3 uses rule-based classification:

- `requiredness`: contains `обязател`, `required`, or standalone `О`.
- `visibility`: contains `отображ`, `видим`, `скрыт`, or `показыв`.
- `editability`: contains `редакт`, `доступно для редактирования`, or standalone `Р`.
- `validation`: contains `не принимает`, `недопуст`, `только`, `формат`, `маска`, or `длина`.
- `dictionary`: contains `справочник`, `значения`, `перечень`, or `DICT`.
- `navigation/action`: contains `кнопка`, `переход`, `нажать`, or `действие`.
- `calculation`: contains `расчет`, `вычисляется`, or `формула`.
- `generated_document`: contains `печатная форма`, `PDF`, `шаблон`, or `тег`.
- `metadata/source_only`: source text does not look like a checkable requirement.

These rules are intentionally conservative and are not a replacement for writer/reviewer semantic decomposition.

## Risky OOXML Zones

The builder must not silently promote risky source zones to active requirements.

Aggregate nodes:

- use only as fallback when direct text does not carry the same normalized value;
- confidence must be at most `medium`;
- add warning: `Derived aggregate source node used; verify direct source nodes if behavior is critical.`

Tracked deletion:

- must not become `active` without warning;
- Stage 3 uses `source_only`;
- add warning: `Tracked deletion text; may represent removed requirement.`

Hidden text:

- may be included;
- must add warning: `Hidden text source node; verify whether it is intended requirement text.`

Comments:

- must not become `active` by default;
- use `source_only` or `unclear`;
- add warning that comment source nodes are not active requirements by default.

Footnotes, endnotes, custom XML, headers, footers, and document properties may be included as source-backed statements, but must keep their OOXML flags and appropriate warnings where the extractor can identify them.

## Summary Shape

`requirements-summary.<version>.json`:

```json
{
  "ft_slug": "AutoFin",
  "source_version": "autofin-final-v1",
  "registry_version": "1.0",
  "created_at_utc": "2026-07-04T00:00:00Z",
  "created_by_tool": "scripts/build_requirements_registry.py",
  "source_manifest_path": "fts/AutoFin/requirements/source-manifest.autofin-final-v1.json",
  "source_manifest_sha256": "64 lowercase hex characters",
  "coverage_audit_path": "fts/AutoFin/requirements/source-coverage-audit.autofin-final-v1.json",
  "registry_path": "fts/AutoFin/requirements/requirements.autofin-final-v1.jsonl",
  "registry_status": "pass-with-warnings",
  "entries_total": 10,
  "active": 1,
  "gap": 0,
  "unclear": 0,
  "source_only": 9,
  "by_requirement_type": {
    "metadata/source_only": 9,
    "requiredness": 1
  },
  "by_part": {
    "word/document.xml": 10
  },
  "source_nodes_seen": 42,
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `registry_status` values:

- `pass`: registry was built without warnings.
- `pass-with-warnings`: registry was built, but source manifest or entry-level warnings need review.
- `blocked`: registry did not create active entries because upstream input is missing, blocked, or contaminated.

## Blocking Rules

The builder must write a blocked summary and no active entries when:

- source manifest file is missing;
- source manifest `ingestion_status` is `blocked`;
- source manifest `coverage_audit_created` is `false`;
- source manifest has no `primary_docx`;
- coverage audit path is missing or unreadable;
- primary DOCX is missing or unreadable;
- source manifest `clean_run_audit.clean_run_status` is not `clean`.

For Stage 3, contamination is handled strictly: `contaminated-risk` and `contaminated` both block registry extraction. This prevents the registry builder from reading expected/private/golden/answer/solution/bundle inputs or proceeding from a contaminated source manifest.

## CLI

```bash
python scripts/build_requirements_registry.py \
  --source-manifest fts/AutoFin/requirements/source-manifest.autofin-final-v1.json \
  --out-dir fts/AutoFin/requirements
```

The CLI writes JSONL and summary files. A blocked registry is reported through `registry_status=blocked` in the summary and stdout payload.

## Stage 3 Limits

- No comparison of two FT versions.
- No requirements diff.
- No impact analysis.
- No writer/reviewer workflow changes.
- No automatic test-case update.
- No claim that rule-based entries are final human-reviewed atomic requirements.
