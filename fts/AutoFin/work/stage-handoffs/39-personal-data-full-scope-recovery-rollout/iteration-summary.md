# Iteration Summary

V2 confirmed the seed-order fix in a real writer session: 47 ordered cases, 65/65 obligations and all deterministic writer gates passed. The recovery avoided the 2.306M-token input-preparation agent by recompiling verified inputs directly.

The full cycle is not accepted. Reviewer did not start because its prompt was 183 402 bytes against a 131 072-byte limit. The reviewer transport has been compacted to 117 439 bytes on the same V2 evidence, and the runner now persists future reviewer-preflight budget blockers correctly. The fix is regression-tested but requires a new immutable V3 live cycle.

The pre-fix V2 `cycle-state.yaml` is intentionally unchanged and therefore stale (`writer pending` despite a completed writer result). `v2-cycle-integrity-warning.yaml` quarantines that state in machine-readable form; V2 must not be resumed.

FT-first baseline and production shadow target remain unchanged.
