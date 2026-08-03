# Controlled Promotion Format

This contract defines the post-hoc, model-free promotion of an already accepted
prepared exec review cycle. The implementation entry point is
`scripts/promote_review_cycle.py`.

## Admission

Promotion is allowed only when all of the following immutable inputs exist:

- source-first reviewer contract v4 normalized as review-result schema v2 in
  `review-result.json`;
- runner-owned `promotion-basis.seed.json` plus a deterministically built
  `promotion-basis.json` binding the candidate, writer draft, source basis,
  obligation set, prepared package v9, reviewer result, explicit `scope_slug`,
  passed gate reports, canonical destination, state replacements and final
  aliases by SHA-256;
- `cycle-state.yaml` in an accepted-not-promoted terminal state;
- one prepared quality-gate bundle with `passed: true` and `draft_sha256` equal
  to the accepted candidate;
- immutable compiler evidence declaring `output_mode: release`,
  `release_eligible: true` and an empty `blocking_gap_ids` list;
- accepted `cycle-state.yaml`, the unique active scope workflow-state/handoff,
  and runner-materialized accepted final findings, Markdown/XLSX traceability
  matrix and pending reviewer-to-UI-prep handoff.

An exact reviewer-rebind terminal is also admissible when it records
`accepted-not-promoted`, `writer_stage_status: skipped-reviewer-rebind`, an
accepted reviewer stage and a non-empty runner-owned `reviewer_rebind_report`.
This exception only admits the candidate to the same post-hoc hash/source/gate
validation; it does not promote automatically or weaken any transaction gate.

Do not reconstruct the normalized reviewer decision or source semantics from
stdout, event logs, Markdown prose or file names during promotion. The builder
may resolve already-existing reviewer-owned aliases through the active
workflow-state or exact canonical cycle output names, but it treats their
contents as opaque hash-bound artifacts except for the traceability pair.
The matrix XLSX must open as a complete OOXML workbook, contain exactly one
visible traceability data sheet plus an optional `meta` sheet, and contain no
formulas. Promotion compares its normalized header, rows, order and values with
exactly one Markdown table; Markdown inline-code markup is presentation-only.
Missing normalized review evidence,
missing or ambiguous handoff aliases, an unknown state schema, stale hashes,
legacy compiler contracts, or incomplete final artifacts are `blocked-input`.

The normalized reviewer result must bind the same draft, source basis and
obligation set hashes reviewed under contract v4, contain `decision: accepted`,
carry an exact duplicate-free compact receipt for every bound obligation, have
no error finding, and mark every routed review dimension `verified`. Every
testable obligation must be `covered`; every gap, unclear or not-applicable
obligation must be `gap-preserved`. Promotion independently parses the
complete embedded source assertion manifest and independent accepted receipt
from the hash-bound source basis. It validates registered source/mockup hashes,
the exact `scope_slug` (also matched to the signed-off workflow-state
replacement), the exact set of testable obligation ids, the complete
ATOM set, each obligation's semantic disposition, canonical statement, testable
oracle and canonical source-ref subset. Exact equality is intentionally not used
for the full obligation `source_refs` array because compiler-derived aliases and
dictionary ids may be additional valid refs. Only after authenticating this
source contract does promotion parse the
`reviewer-dimension-source-bindings-v1` map from the same source basis,
requires the dimension receipt to have the same exact dimension set, and rejects
any ref array that is not exactly equal to that dimension's complete canonical
sorted binding (including omissions or reordering). It does not trust the
runner's earlier parser result as sufficient evidence at this trust boundary.
Legacy/plain Markdown evidence cannot promote a source-first v4 review.

Promotion independently loads the bound prepared package v9 and reconciles its
canonical structured `release_status` with the exact bound source basis and
obligation set. The package artifact path/SHA bindings must equal the promotion
basis bindings. A draft, a non-eligible package, stale external gap/manifest
input, or an omitted/mutated execution-dependency registry blocks before writes.

An accepted source assertion receipt authenticates the source model, and an
accepted reviewer receipt authenticates the unsigned candidate; neither is a
release waiver. Promotion independently loads `atomic-obligations.json`. Any
gap whose content still has `blocking: true` fails as
`PROMO-BLOCKING-SOURCE-GAPS` before writes in `--validate-only`, `--dry-run` and
full transaction modes, regardless of copied status metadata or aliases.
Any typed execution-dependency registry fails separately as
`PROMO-BLOCKED-EXECUTION-DEPENDENCIES`.

## Runner Seed

After every accepted release-eligible source-first exec review, the runner writes
immutable `review-result.json`, a deterministic accepted-source-first final
Markdown/XLSX traceability pair, a `pending-controlled-promotion`
reviewer-to-UI-prep prompt, and `promotion-basis.seed.json`. The matrix contains
one row per manifest ATOM, including honest `not-applicable` rows without
fabricated test-case coverage; Markdown/XLSX semantic parity is self-checked
before the seed is written. The seed binds the candidate,
writer draft, source basis, obligation set, prepared package, reviewer result,
explicit scope slug, quality-gate bundle, final findings, both matrix files,
handoff prompt and cycle-start production baseline by SHA-256. The
seed uses schema v2; the full promotion basis uses schema v3 and requires the
prepared-package binding. Older full-basis schemas are intentionally rejected
because they do not authenticate package release status at the promotion trust
boundary. The seed is intentionally not itself a promotable basis. The default
promotion command consumes it and atomically generates only deterministic
signed-off cycle/workflow-state projections and their final alias references.
It rediscovers the one exact matrix pair and active handoff for the bound scope
and rejects any mismatch with the seed bindings; ambiguity, absence or mutation
blocks. The promotion builder itself never generates semantic findings, matrix
content, reviewer decisions or a handoff prompt. Explicit replacement paths remain an advanced
compatibility input and must already exist as a complete pair. A normal accepted
cycle needs no manually pre-created `promotion-inputs/` directory.

The pending handoff prompt is scope-stable and cycle-independent: cycle state,
findings, matrices and snapshot are resolved only through the signed-off
`workflow-state.yaml.latest_artifacts` aliases. This permits byte-identical,
no-clobber reuse after an interrupted pre-promotion cycle. Controlled promotion
must set both `prompt_reviewer_to_ui_prep` and `active_transition_prompt` to that
exact seed-bound prompt; retaining the previous writer/reviewer transition prompt
is invalid.

A reviewer-accepted `draft-with-blocking-gaps` cycle ends
`blocked-input`/`blocked-source-gaps` or
`blocked-input`/`blocked-execution-dependencies`. It may retain its unsigned draft and
normalized review evidence, but the runner must not emit
`promotion-basis.seed.json`, a canonical file or a signed-off snapshot. Once the
gaps are clarified, promotion requires a fresh source-first release cycle.

## Transaction

One invocation owns `<cycle-dir>/promotion.lock` and one repository-local lock
for each resolved canonical or workflow-state target. Target locks are derived
independently from normalized absolute paths and acquired in deterministic
sorted order, so promotions sharing either target cannot overlap even when their
other target differs. Lock schema v2 binds PID, owner token, cycle, basis hash,
transaction id, roles and resolved target. A live owner always blocks. A dead
owner can be removed only after startup reconciliation proves the exact bound
transaction: pre-commit targets must each equal their journaled before/after
image and are rolled back to before; a committed transaction must have every
target in its after image and is rolled forward by publishing its prepared
snapshot. Legacy, malformed, PID-reused or otherwise ambiguous locks remain
fail-closed. An invocation releases only locks whose exact ownership it proved.
The basis is reloaded
and its target bindings are compared after lock acquisition before the
transaction performs this sequence:

1. Validate paths, schemas, accepted-not-promoted state and the complete hash
   chain without changing production.
2. Reuse the bound passed deterministic gate reports. Do not rerun them.
3. Capture the hash-bound candidate and final-alias bytes once, run
   `production_tc_gate` exactly once against the captured candidate, and recheck
   every captured input before commit.
4. Snapshot prior canonical/state bytes and atomically publish an immutable
   write-ahead recovery journal before the first production mutation.
5. Publish the captured candidate bytes atomically, verify byte identity, and
   bind the same bytes to the signed-off snapshot canonical entry.
6. Materialize deterministic receipt and before/after snapshot evidence inside
   the journal.
7. Atomically apply the prevalidated cycle-state and workflow-state replacements,
   with each target remaining exactly classifiable as its before or after image.
8. Write phase metrics, atomically rename the journal to the deterministic
   transaction root as the commit marker, publish the prepared signed-off
   snapshot, verify all after images, and release the locks.

If an ordinary exception occurs after publication, compare-and-swap rollback
restores only targets still equal to their bound after image and never clobbers
unknown external bytes. After abrupt process termination, the next invocation
reconciles before basis rebuilding: an uncommitted journal rolls back and an
atomic transaction marker rolls forward. A target that is neither its exact
before nor after image, a changed journal/basis, conflicting snapshot markers or
unprovable lock ownership blocks as `PROMO-RECOVERY-AMBIGUOUS`/
`PROMO-RECOVERY-CONFLICT` without rewriting evidence. A pre-existing canonical target is denied by
default. Overwrite requires both `--allow-overwrite` and the exact prior hash in
`promotion-basis.json`.

Journal files and snapshots use same-directory temporary files, flush+`fsync`
and `os.replace`; journal publication and the transaction commit marker use
atomic directory renames. This is the hard-process-termination contract. It does
not claim storage-controller/power-loss durability beyond guarantees provided by
the host filesystem, because ordinary Windows directory handles do not expose a
portable directory-`fsync` equivalent.

A replay of the same command is successful only when the receipt, complete hash
chain, canonical/state targets, metrics and every signed-off snapshot byte still
match the committed transaction. It returns `already-promoted` without rerunning
the production gate. Partial or mutated completion markers fail closed.

The deterministic transaction id is derived from the candidate and reviewer
result hashes. The deterministic receipt excludes timestamps and phase
durations; timings are stored separately in `promotion-metrics.json`.

## Outputs

Successful promotion creates:

```text
<cycle-dir>/promotion/<transaction-id>/
  before/repo/<bound paths>
  recovery-journal.json
  promotion-receipt.json
  promotion-metrics.json
<cycle-dir>/versions/signed-off/
  <FT-relative final files>
  snapshot-manifest.yaml
  snapshot-manifest.json
```

The workflow-state replacement must expose the canonical final aliases
`final_findings`, `final_traceability_matrix`,
`final_traceability_matrix_xlsx`, optional `final_writer_response`, the
signed-off snapshot and the reviewer-to-UI-prep prompt. The orchestrator checks
these aliases against bound artifacts; it does not invent them.

## Commands

Validation without production or state-target mutation (builder evidence may be
materialized in the cycle directory):

```powershell
python scripts\promote_review_cycle.py --repo-root . --cycle-dir <cycle-dir> --validate-only
```

Full transaction preflight without production or state-target mutation:

```powershell
python scripts\promote_review_cycle.py --repo-root . --cycle-dir <cycle-dir> --dry-run
```

Controlled publication:

```powershell
python scripts\promote_review_cycle.py --repo-root . --cycle-dir <cycle-dir>
```

This single command performs build, validation and publication, including state
projection, receipt, metrics, final aliases, snapshot and handoff-state
references. The target SLO is `300000 ms`; `420000 ms` is the hard limit. The
measured total includes basis/state projection time. Exceeding the hard limit
rolls back publication and state.

The default command never silently falls back to an unseeded basis. The
`--use-existing-basis` compatibility mode is reserved for an explicitly audited
schema-v3 basis and still executes the complete post-hoc validation/transaction;
it is not the normal accepted-cycle path.
