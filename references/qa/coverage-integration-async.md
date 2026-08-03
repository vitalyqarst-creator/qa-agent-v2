# Coverage Integration And Async

Deep coverage reference for integration, API, async, persistence and server-side behavior. Use it only when the confirmed scope contains these dimensions or when reviewer/validator reports fake internal coverage.

## Runtime Rule

No internal or integration requirement is `covered` without a confirmed observable artifact.

Observable artifacts may include:

- visible UI state explicitly tied to the requirement;
- generated document or message;
- named API request/response artifact;
- log, queue, database or model artifact only if source/handoff permits checking it.

## Required Handling

- If FT describes user action and internal effect, split them: executable action/initiation TC for observable part, `GAP-*` for unobservable internal part.
- If retry, timeout, duplicate prevention or conflict resolution is not described, create `GAP-*`.
- Do not invent HTTP status codes, schemas, queue names, storage effects or fallback behavior.
- Persistence coverage requires source-backed observable state after save/reopen or allowed technical artifact.
- Async coverage requires source-backed completion signal or allowed trace/log artifact.

## Negative Integration Cases

Only write negative integration tests when expected behavior is source-backed:

- failed dependency;
- partial data;
- stale reference data;
- unavailable service;
- duplicate event/request;
- retry or timeout.

If expected behavior is absent, record a coverage gap instead of choosing a fallback by convention.
