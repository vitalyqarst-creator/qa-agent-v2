# Artifact Manifest Format

`fts/artifact-manifest.json` фиксирует переносимые свойства артефактов, которые нельзя надежно восстановить только из имени файла или `workflow-state.yaml`.

Manifest не заменяет `source-selection.md`, `workflow-state.yaml` и stage handoff. Его задача уже: явно описать canonical artifact, alias-копии, checksum/size и local-only ограничения.

## Когда нужен manifest

- один и тот же binary source/support файл хранится под несколькими именами;
- файл добавлен как alias для совместимости со старыми `workflow-state.yaml`;
- evidence ссылается на ignored/local `output/` paths;
- artifact внешне хранится вне repo или намеренно не collected.

Не нужно заносить в manifest каждый обычный source/support файл без aliases и portability риска.

## Расположение

Основной файл:

```text
fts/artifact-manifest.json
```

Пути в manifest указываются относительно repository root, например:

```text
fts/<ft-slug>/source/<file>.docx
```

## Schema v1

```json
{
  "manifest_version": 1,
  "generated_at": "2026-05-25",
  "artifacts": [
    {
      "id": "stable-artifact-id",
      "role": "main-ft-docx",
      "canonical_path": "fts/<ft-slug>/source/main.docx",
      "aliases": [
        "fts/<ft-slug>/source/alias.docx"
      ],
      "sha256": "<64 hex chars>",
      "size_bytes": 12345,
      "export_policy": "alias-copy",
      "notes": "Why this alias exists."
    }
  ]
}
```

## Required fields

- `manifest_version`: currently `1`.
- `artifacts`: list of artifact entries.
- `id`: stable unique id.
- `role`: short purpose, for example `main-ft-docx`, `main-ft-pdf`, `shared-support-docx`, `ui-evidence-output`.
- `export_policy`: one of the canonical values below.
- `canonical_path`: required unless `export_policy` is `not-collected`.

## Optional fields

- `aliases`: alternate repo paths that must contain the same bytes as `canonical_path` for repo-tracked policies.
- `sha256`: checksum of `canonical_path`.
- `size_bytes`: size of `canonical_path`.
- `referenced_by`: files that depend on this artifact or evidence entry.
- `availability`: short note such as `present-in-repo` or `not-present-in-clean-checkout`.
- `notes`: human explanation.

## Export Policies

- `repo-tracked`: canonical file is present in repo/workspace and should be validated.
- `alias-copy`: canonical file and aliases are present; aliases must match canonical bytes.
- `local-output-index-only`: path is local/ignored evidence, usually under `output/`; existence is not required.
- `external`: artifact is stored outside the repo; manifest documents the reference but validator does not require local existence.
- `not-collected`: artifact was intentionally not collected.

## Validator Rules

`scripts/validate_agent_artifacts.py` checks:

- manifest is valid UTF-8 JSON;
- `manifest_version` is supported;
- ids are unique;
- export policy is canonical;
- repo-tracked canonical paths exist;
- declared aliases exist and match canonical bytes;
- `sha256` and `size_bytes` match when present;
- duplicate source/support files are declared as canonical+aliases.

If duplicate source/support files exist without manifest coverage, validator reports `artifact-manifest-duplicate-untracked`.
