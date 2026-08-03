# Duplication Policy

The project follows the single-source-of-truth rule.

## Canonical Zones

- `AGENTS.md` - global policy and routing.
- `skills/*/SKILL.md` - phase-specific workflow.
- `references/agent/` - agent-layer architecture rules.
- `references/qa/` - stable QA rules, format, and traceability.
- `fts/<ft-slug>/work/test-design/<scope>/` - the only source for table-heavy writer artifacts for the concrete scope.
- `fts/<ft-slug>/test-cases/` - canonical `TC-*` suite, links to split artifacts, and a short summary without full table copies.
- `test_case_agent/` - technical implementation.

## Allowed Repetition

Only these are allowed:

- short links to a canonical document;
- a short reminder without copying the full rule;
- UI metadata in `agents/openai.yaml`.

## Disallowed Repetition

- same procedural steps in `AGENTS.md` and `SKILL.md`;
- same QA rules in multiple `SKILL.md` files;
- copies of shared references inside a concrete skill without a strong reason;
- domain policy text inside code or helper scripts;
- full copies of `Source Table Normalization`, `Test Design Decision Table`, ledger, design plan, coverage gaps, or gate in both `work/test-design/<scope>/` and the canonical test-case file.
