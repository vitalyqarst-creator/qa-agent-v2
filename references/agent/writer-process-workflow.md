# Writer Process Workflow

This reference contains process and artifact-writing rules for `ft-test-case-writer`. It is loaded only when process artifacts are required.

## Session And Decision Logs

Before finishing a writer pass, create or update `writer-session-log.md` according to `session-log-format.md`.

Record:

- inputs read and inputs intentionally not used;
- key source, coverage and artifact decisions;
- validation commands and results;
- technical fallbacks;
- contamination check;
- handoff notes for reviewer or next stage.

For clean eval or diagnostic runs, include:

- `Event Timeline`;
- `Quality Checkpoints`;
- `Artifact Write Strategy`;
- `Technical Fallbacks`;
- `Handoff Notes For Next Session`.

Create or update `agent-decision-log.md` according to `agent-decision-log-format.md`. It must record observable inputs, decision, rationale, output and risk. It is not a transcript and must not include hidden reasoning.

Link both logs from `workflow-state.yaml` through `latest_artifacts`.

## Artifact Write Strategy

Before creating a large canonical file or split test-design artifacts, choose the write strategy before content generation.

Use `scripts/write_artifact_sections.py --manifest <manifest.json>` when any of these is true:

- more than 20 planned `TC-*`;
- more than 30 planned `ATOM-*`;
- generated Markdown is likely above 20,000 characters;
- the scope contains internal `WP-*` packages;
- table-heavy output requires several split artifacts.

Do not start with one-shot PowerShell, here-string, giant inline command or ad-hoc `tmp/generate_*.py`. A command-line limit fallback is a clean-run failure, not an acceptable production path.

## Encoding And Source Fidelity

For Russian-language sources in PowerShell, use the UTF-8 preamble from `session-log-format.md`.

If terminal output distorts Cyrillic:

- reread the source through an explicit UTF-8 file/script path;
- do not use distorted stdout as evidence;
- record the fallback in `Technical Fallbacks`.

## Workflow State

Use `workflow-state.yaml` as the process-status source of truth.

Use:

- `ready-for-review` only after the writer output, gates, logs and prompt are complete;
- `blocked-input` when required source/scope/gap decisions are missing;
- `ready-for-writer-revision` only when reviewer findings require a new writer round.

Store `prompt.writer-to-reviewer.round-N.md` in the current stage-handoff folder. For new scopes, use `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/`.
