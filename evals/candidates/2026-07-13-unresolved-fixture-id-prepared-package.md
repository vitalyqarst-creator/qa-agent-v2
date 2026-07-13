# unresolved-fixture-id: fixture-ID без исполнимого содержимого

## Metadata

- `candidate_id`: `EVAL-CAND-2026-07-13-ACPD-UNRESOLVED-FIXTURE`
- `created_at`: `2026-07-13`
- `source_signal`: V4r1 live writer `blocked-input`
- `affected_skill`: `ft-test-case-iteration`, prepared package compiler/preflight
- `failure_class`: `unresolved-fixture-id`
- `status`: `proposed`

## Failure Signal

- `bad_artifact`: H41 compiler inputs and V4r1 prepared package.
- `bad_output`: writer stopped because `FIX-ACPD-SAVE-001` and `FIX-ACPD-DADATA-001` had names/contracts but no registered concrete data.
- `why_it_is_wrong`: compiler treated a non-empty fixture reference as sufficient, so missing input reached a 38 071-token live model call.
- `source_or_rule_ref`: `references/agent/fixture-catalog-format.md`; V4r1 `writer-result.json`.

## Eval Target

- reject a plan/package whose fixture reference is absent from the catalog;
- reject generic, conditional or incomplete `concrete_data`;
- require dependencies/cleanup for save and integration fixtures;
- accept a complete synthetic catalog without requiring PII or environment secrets;
- stop before package write or live attempt.

## Guardrails

- fixture catalog is not a source of new product behavior;
- an opaque alias does not replace portable execution data;
- unavailable or restricted fixture remains `blocked-input`;
- do not broaden this into a general keyword ban.

## Next action

Create a bounded bad/corrected compiler eval, add catalog resolution to the prepared compiler, register safe stand-backed data, and validate only in a fresh V5 package.
