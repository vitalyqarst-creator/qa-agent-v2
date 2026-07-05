# Writer Package Task Format

Stage 7B converts Manual Update Work Packages into scoped writer task artifacts for a future writer agent.

It does not edit, create, deprecate, rewrite, or delete test-case files. It does not run controlled apply.
It does not change the writer/reviewer workflow.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `writer-package-tasks.<old-version>-to-<new-version>.json`
- `writer-package-tasks-summary.<old-version>-to-<new-version>.json`
- `writer-package-task-WPKG-000001.md`
- one `writer-package-task-<package_id>.md` file per package.

## Task Shape

```json
{
  "package_id": "WPKG-000001",
  "task_file_name": "writer-package-task-WPKG-000001.md",
  "package_type": "update_existing",
  "file_path": "fts/AutoFin/test-cases/14-client-addresses.md",
  "affected_test_case_ids": ["TC-001", "TC-002"],
  "plan_item_ids": ["PLAN-000001", "PLAN-000002"],
  "impact_ids": ["IMP-000001"],
  "change_ids": ["CHG-000001"],
  "actions": ["update_existing"],
  "plan_items_count": 2,
  "large_package": false,
  "safe_to_try_first": true,
  "allowed_operations": [
    "update listed TC only",
    "review steps",
    "review expected result",
    "update traceability"
  ],
  "forbidden_operations": [
    "Do not touch unlisted TC",
    "Do not rewrite entire file"
  ],
  "scope_instruction": "Update only listed TC, do not rewrite entire file.",
  "execution_notes": [
    "Limit review and proposed edits to the listed TC IDs."
  ],
  "warnings": []
}
```

## Task Rules

- one writer task is created per manual update package;
- file-bound packages with listed TC IDs must include exact `file_path` and only listed `affected_test_case_ids`;
- file-bound packages with listed TC IDs must include `Do not touch unlisted TC`;
- file-bound packages with listed TC IDs must include the exact instruction `Update only listed TC, do not rewrite entire file.`;
- `create_new_candidate` tasks must say to propose drafts only and not write canonical files;
- unlinked manual-review tasks must say to analyze and classify and not edit files;
- `large_package=true` when `plan_items_count > 50`;
- large packages must recommend splitting before writer execution.

`safe_to_try_first=true` is a convenience hint for small file-bound tasks with concrete TC IDs.
It is not permission to edit files in Stage 7B.

## Summary Shape

```json
{
  "task_status": "pass-with-warnings",
  "tasks_total": 5,
  "file_bound_tasks": 2,
  "unlinked_tasks": 3,
  "create_new_candidate_tasks": 1,
  "large_package_tasks": 2,
  "large_package_task_ids": ["WPKG-000004", "WPKG-000005"],
  "largest_task_plan_items_count": 371,
  "safe_to_try_first_task_ids": ["WPKG-000002", "WPKG-000003"],
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `task_status` values:

- `pass`
- `pass-with-warnings`
- `blocked`

## Blocking Rules

Block task generation when:

- manual update packages file is missing;
- manual update packages file cannot be parsed;
- manual update packages summary has `package_status=blocked`;
- no packages are available for writer task generation;
- duplicate task `package_id` is detected.

When blocked, artifacts may still be written for diagnostics, but `tasks` must be empty.

## Markdown Task File

Each task Markdown file must contain:

- `Scope`
- `Instruction`
- `Allowed Operations`
- `Forbidden Operations`
- `Execution Notes`

The Markdown task is a prompt/task artifact only. It must not apply edits by itself.

## CLI

```bash
python scripts/build_writer_package_tasks.py \
  --packages fts/AutoFin/work/e2e-dry-run/<run>/manual-update-packages.<old>-to-<new>.json \
  --out-dir fts/AutoFin/work/e2e-dry-run/<run>
```

## Stage 7B Limits

- Do not edit test-case files.
- Do not create new test-case files.
- Do not mark test cases deprecated in files.
- Do not run `--apply`.
- Do not change writer/reviewer workflow.
