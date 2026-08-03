# Instruction Authoring Policy

This document governs agent instructions. Placement, duplication, and loading are defined by `content-placement.md`, `duplication-policy.md`, and `deep-reference-loading-policy.md`.

## Scope and Sufficiency

- The H1 must explain the document purpose without relying on the file name.
- Keep each document limited to one area and to knowledge that changes the agent's decision. Replace the rest with a link to the canonical contract.
- Do not add explanations only to prevent implausible mistakes by a competent agent.

## Generalization and Placement

- Describe the same semantics once at the highest reusable level where the rule remains exact.
- Split rules only when applicability, authority, behavior, output, or error handling differs.
- In dependent documents, keep only local conditions, additional consequences, and a link to the canonical source.
- Do not generalize rules from different authority sources when that hides source priority or changes conflict behavior.
- Mark explicit dependencies as `governed-by` (normative contract), `validated-against` (check), or `derived-from` (source). A decision-affecting `governed-by` target must be present in the actual context.

## Language Selection

- Prefer English for stable technical contracts, runtime protocols, schemas, gates, routing, budgets, and model-facing reviewer/writer rules when the wording is not tied to Russian source text.
- Keep Russian for user-facing output requirements, Russian FT terminology, field/button labels, source quotes, examples of `TC-*` wording, and any rule whose precision depends on the Russian requirement language.
- Do not keep parallel Russian and English copies of the same rule. If translation is needed, replace the rule and preserve only exact Russian labels or examples as quoted literals.

## Structure and Modality

- Group requirements by aspect and logical dependency. A heading or lead-in sentence must define the group scope.
- Keep list items at the same semantic level. Put clarification inside the item it clarifies.
- Use numbered lists only for sequences where order affects the result. Use bullets for unordered sets.
- Use one modality system within a document. Do not mix imperatives with `MUST`, `SHOULD`, and `MAY` unless the document defines those terms.

## Contracts of Other Components

- Describe the tool purpose, trigger conditions, inputs, outputs, and success criterion.
- Treat `<script-path> --help` as the canonical source for CLI syntax, flags, and defaults. Do not reproduce a full CLI reference in agent instructions.
- A minimal run/check command is allowed; an alternative parameter reference is not.
- Keep lifecycle and handoff in the governing workflow. Locally describe only the component's own conditions and outputs.

## Target Model

- Describe the current target behavior directly.
- Mention history only when it changes inputs, storage, compatibility, error handling, or the agent's current decision.
- Do not use historical comparison instead of stating the active rule.

## Review in the Target-Agent Context

After changing agent instructions:

1. Identify affected scenarios and get their actual context through `resolve_instruction_context.py`; see the CLI contract in `scripts/resolve_instruction_context.py --help`.
2. Review the material as a competent target agent that has only the selected scenario context.
3. Fix insufficient, contradictory, redundant, or duplicated instructions. Treat a finding as material when it changes source, scope, route, authority, output, state, gate, or error handling. Do not remove a guardrail that is backed by repeated runtime defects.
4. Repeat the review until material findings are closed. Ignore style preferences; record an unresolvable contradiction as a blocker. Then run architecture and budget gates.

Successful lint, audit, and budget checks are required, but they do not replace semantic sufficiency review of the limited runtime context.
