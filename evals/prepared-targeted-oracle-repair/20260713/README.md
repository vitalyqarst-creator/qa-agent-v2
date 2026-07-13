# Prepared Targeted Oracle Repair Eval

This fixture set protects two pre-live boundaries:

- prepared obligations with empty or non-observable oracles must block before an attempt;
- a new targeted-repair cycle may return only the named replacement TC sections, while the runner preserves all other sections byte-for-byte and still runs full-set gates/review.

`bad-prepared-oracles.json` contains rejected oracle shapes. `corrected-repair-sections.md` is a valid two-section repair response for TC 001 and 003. `expected.json` records the required route invariants.
