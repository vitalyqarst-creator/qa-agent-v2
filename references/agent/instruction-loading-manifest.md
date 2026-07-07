# Instruction Loading Manifest

Этот manifest задает, какие instruction files читать для типовых сценариев agent pipeline. Он не заменяет правила writer/reviewer/scope skill-ов и не описывает, как писать тест-кейсы. Его единственная задача - управлять загрузкой инструкций и budget checks.

Resolver должен читать JSON-блок ниже как канонический источник. Текст вокруг блока предназначен только для людей.

<!-- instruction-loading-manifest:v1 -->
```json
{
  "version": 1,
  "budget_unit": "KiB",
  "baseline": {
    "captured_at": "2026-06-02",
    "writer_ready_scope_kib": 419.0,
    "fresh_write_chain_kib": 516.4,
    "iteration_chain_kib": 664.8,
    "method": "direct AGENTS.md + skills/README.md + selected SKILL.md files + all Markdown links from those SKILL.md files"
  },
  "groups": {
    "global_core": {
      "rationale": "Global policy and active skill dispatch map.",
      "paths": [
        "AGENTS.md",
        "skills/README.md"
      ]
    },
    "review_cycle_core": {
      "rationale": "Session-based writer/reviewer cycle contract and Codex SDK orchestration rules.",
      "paths": [
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md"
      ]
    },
    "writer_core": {
      "rationale": "Minimum runtime contract for writing test cases when the FT package and scope are already confirmed.",
      "paths": [
        "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md",
        "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md",
        "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md"
      ]
    },
    "writer_process_artifacts": {
      "rationale": "Detailed process artifact formats for workflow/session/decision logs and next-step prompts.",
      "paths": [
        "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/writer-handoff-format.md"
      ]
    },
    "writer_table_artifacts": {
      "rationale": "Table-heavy and row-level parity writer artifacts required before ledger and TC writing.",
      "paths": [
        "references/agent/writer-table-workflow.md",
        "references/agent/writer-table-artifacts-format.md",
        "references/agent/artifact-write-strategy-format.md",
        "references/agent/source-parity-check-format.md",
        "references/agent/source-row-inventory-format.md",
        "references/agent/source-table-normalization-format.md",
        "references/agent/source-normalization-diagnostic-format.md",
        "references/agent/dictionary-inventory-format.md",
        "references/agent/test-design-decision-table-format.md",
        "references/agent/coverage-obligation-table-format.md",
        "references/agent/test-design-coverage-metrics-format.md",
        "references/agent/fixture-catalog-format.md",
        "references/agent/risk-priority-map-format.md",
        "references/agent/state-model-coverage-format.md",
        "references/agent/experience-based-coverage-format.md",
        "references/agent/package-test-design-plan-format.md",
        "references/agent/test-design-review-format.md",
        "references/agent/test-design-defect-taxonomy.md",
        "references/agent/writer-quality-gate-format.md"
      ]
    },
    "writer_ui_artifacts": {
      "rationale": "UI writer references used only when the confirmed scope has mockups or screen images.",
      "paths": [
        "references/agent/mockup-visual-inventory-format.md"
      ]
    },
    "writer_revision_artifacts": {
      "rationale": "Revision-only formats for fixing an existing set by structured reviewer findings.",
      "paths": [
        "references/agent/writer-revision-workflow.md",
        "references/agent/writer-revision-output-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/traceability-matrix-format.md"
      ]
    },
    "writer_numeric_coverage": {
      "rationale": "Deep input-boundary coverage for numeric, date, length, mask and allowed-symbol constraints.",
      "paths": [
        "references/qa/coverage-input-boundaries.md"
      ]
    },
    "writer_integration_coverage": {
      "rationale": "Deep coverage for integration, async, API, persistence and internal effects.",
      "paths": [
        "references/qa/coverage-integration-async.md"
      ]
    },
    "writer_validator_failure_deep": {
      "rationale": "Deep references for remediation after validator or Writer Quality Gate failures.",
      "paths": [
        "references/agent/writer-remediation-workflow.md",
        "references/agent/writer-output-format.md",
        "references/agent/writer-quality-gate-format.md",
        "references/agent/dictionary-inventory-format.md",
        "references/agent/test-design-defect-taxonomy.md",
        "references/qa/test-case-format.md"
      ]
    },
    "source_locator_core": {
      "rationale": "Instruction context for locating an FT package and source files.",
      "paths": [
        "skills/ft-source-locator/SKILL.md",
        "references/agent/source-selection-format.md",
        "references/agent/artifact-manifest-format.md",
        "references/agent/ft-package-agent-notes-template.md",
        "references/agent/stage-handoff-model.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md"
      ]
    },
    "scope_manual_core": {
      "rationale": "Scope analyzer context for a user-provided manual scope.",
      "paths": [
        "skills/ft-scope-analyzer/SKILL.md",
        "references/agent/source-selection-format.md",
        "references/agent/scope-contract-format.md",
        "references/agent/scope-coverage-gaps-format.md",
        "references/agent/scope-clarification-requests-format.md",
        "references/agent/scope-decomposition-policy.md",
        "references/agent/source-parity-check-format.md",
        "references/agent/stage-handoff-model.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/next-step-prompt-format.md"
      ]
    },
    "scope_table_artifacts": {
      "rationale": "Scope analyzer references for row-level/table parity scopes.",
      "paths": [
        "references/agent/source-row-inventory-format.md"
      ]
    },
    "scope_ui_artifacts": {
      "rationale": "Scope analyzer references for UI scopes with mockups or screen images.",
      "paths": [
        "references/agent/mockup-visual-inventory-format.md"
      ]
    },
    "scope_agent_proposed_core": {
      "rationale": "Scope analyzer context for proposing candidate external scopes before writer work.",
      "paths": [
        "skills/ft-scope-analyzer/SKILL.md",
        "references/agent/source-selection-format.md",
        "references/agent/scope-options-format.md",
        "references/agent/scope-selection-prompts-format.md",
        "references/agent/scope-decomposition-policy.md",
        "references/agent/stage-handoff-model.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md"
      ]
    },
    "iteration_core": {
      "rationale": "Orchestrator context for the session-based writer/reviewer cycle and final routing.",
      "paths": [
        "skills/ft-test-case-iteration/SKILL.md",
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md",
        "references/qa/test-case-versioning-policy.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/stage-handoff-model.md"
      ]
    },
    "reviewer_core": {
      "rationale": "Reviewer context needed by iteration to understand review modes and findings contracts.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/agent/package-test-design-plan-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/traceability-matrix-format.md",
        "references/qa/test-design-review-rubric.md",
        "references/agent/test-design-defect-taxonomy.md",
        "references/agent/dictionary-inventory-format.md",
        "references/qa/test-case-runtime-format.md",
        "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md"
      ]
    },
    "reviewer_process_artifacts": {
      "rationale": "Process artifact formats for a direct reviewer pass outside the full iteration orchestrator.",
      "paths": [
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/next-step-prompt-format.md"
      ]
    },
    "reviewer_scope_gap_core": {
      "rationale": "Pre-writer reviewer context for checking scope coverage gaps and clarification requests before test-case writing starts.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/scope-contract-format.md",
        "references/agent/scope-coverage-gaps-format.md",
        "references/agent/scope-clarification-requests-format.md",
        "references/agent/source-parity-check-format.md",
        "references/agent/source-row-inventory-format.md",
        "references/agent/mockup-visual-inventory-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/traceability-rules.md"
      ]
    },
    "reviewer_structure_preflight_core": {
      "rationale": "Lightweight reviewer pass for parseability, handoff completeness and blocking format prerequisites before semantic review.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/test-case-runtime-format.md"
      ]
    },
    "reviewer_semantic_core": {
      "rationale": "Semantic reviewer pass for traceability, coverage, test-design and expected-result observability.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/agent/package-test-design-plan-format.md",
        "references/agent/dictionary-inventory-format.md",
        "references/agent/test-design-defect-taxonomy.md",
        "references/qa/review-findings-format.md",
        "references/qa/traceability-matrix-format.md",
        "references/qa/test-design-review-rubric.md",
        "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md"
      ]
    },
    "reviewer_structure_format_core": {
      "rationale": "Final reviewer pass for template, numbering, grouping, wording and format-only findings after semantic closure.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/test-case-format.md",
        "references/qa/test-case-style-examples.md"
      ]
    },
    "reviewer_semantic_regression_core": {
      "rationale": "Final semantic regression pass after format-only changes to prove traceability and coverage did not change.",
      "paths": [
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/traceability-matrix-format.md",
        "references/qa/test-design-review-rubric.md",
        "references/qa/traceability-rules.md"
      ]
    },
    "sdk_orchestration_core": {
      "rationale": "Runner-facing context for Codex SDK session orchestration and cycle state validation.",
      "paths": [
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md",
        "references/agent/task-start-skill-routing-format.md"
      ]
    },
    "ui_automation_prep_core": {
      "rationale": "Post-sign-off UI verification and automation-ready preparation context.",
      "paths": [
        "skills/ft-ui-automation-prep/SKILL.md",
        "references/agent/ui-evidence-policy.md",
        "references/agent/workflow-state-format.md",
        "references/agent/stage-handoff-model.md",
        "references/agent/ft-ui-agent-notes-template.md",
        "references/qa/test-case-runtime-format.md",
        "references/qa/traceability-rules.md",
        "references/qa/automation-ready-lifecycle.md",
        "references/qa/ui-automation-prep-format.md"
      ]
    },
    "architecture_audit_core": {
      "rationale": "Script-first architecture audit context for agent-layer governance tasks.",
      "paths": [
        "skills/agent-architecture-auditor/SKILL.md",
        "references/agent/task-start-skill-routing-format.md",
        "references/agent/instruction-contract-index.md",
        "references/agent/content-placement.md",
        "references/agent/skill-boundaries.md",
        "references/agent/duplication-policy.md",
        "references/agent/maintenance-checklist.md",
        "references/agent/audit-output-format.md"
      ]
    },
    "style_remediation": {
      "rationale": "Examples for style-specific remediation after a style finding, not default writer runtime.",
      "paths": [
        "references/qa/test-case-format.md",
        "references/qa/test-case-style-examples.md"
      ]
    },
    "audit_only_history": {
      "rationale": "Historical debt and migration reports used for maintenance, not default runtime instruction loading.",
      "paths": [
        "references/agent/iteration-lifecycle-format.md",
        "references/agent/canonical-handoff-examples.md",
        "references/agent/strict-debt-report-2026-05-25.md",
        "references/agent/reviewer-signoff-migration-report-2026-05-25.md",
        "references/agent/traceability-legacy-matrix-report-2026-05-25.md",
        "references/agent/source-quality-strict-warning-review-2026-05-25.md"
      ]
    },
    "governance_audit_only": {
      "rationale": "Architecture governance docs for audit and maintenance, not writer runtime.",
      "paths": [
        "references/agent/instruction-contract-index.md",
        "references/agent/content-placement.md",
        "references/agent/skill-boundaries.md",
        "references/agent/duplication-policy.md",
        "references/agent/maintenance-checklist.md",
        "references/agent/audit-output-format.md"
      ]
    }
  },
  "scenarios": [
    {
      "id": "source_locator.discovery",
      "phase": "source_locator",
      "mode": "discovery",
      "scope_profile": "any",
      "required_groups": ["global_core", "source_locator_core"],
      "conditional_groups": ["scope_manual_core", "scope_agent_proposed_core", "scope_table_artifacts", "scope_ui_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 130,
      "rationale": "FT package and source discovery before scope or test-case work."
    },
    {
      "id": "writer.initial_draft.simple",
      "phase": "writer",
      "mode": "initial_draft",
      "scope_profile": "simple",
      "required_groups": ["global_core", "writer_core"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 140,
      "rationale": "Confirmed simple scope without row-level parity, mockups or reviewer findings."
    },
    {
      "id": "writer.initial_draft.table",
      "phase": "writer",
      "mode": "initial_draft",
      "scope_profile": "table",
      "required_groups": ["global_core", "writer_core", "writer_process_artifacts", "writer_table_artifacts"],
      "conditional_groups": ["writer_ui_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 300,
      "rationale": "Confirmed table-heavy or row-level parity scope requiring normalization and table design artifacts."
    },
    {
      "id": "writer.initial_draft.ui",
      "phase": "writer",
      "mode": "initial_draft",
      "scope_profile": "ui",
      "required_groups": ["global_core", "writer_core", "writer_ui_artifacts"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 210,
      "rationale": "Confirmed UI scope with mockup or screen image, but without row-level table parity."
    },
    {
      "id": "writer.initial_draft.numeric",
      "phase": "writer",
      "mode": "initial_draft",
      "scope_profile": "numeric",
      "required_groups": ["global_core", "writer_core", "writer_numeric_coverage"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_revision_artifacts", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 180,
      "rationale": "Confirmed scope dominated by numeric/date/length/mask input constraints without table parity."
    },
    {
      "id": "writer.initial_draft.integration",
      "phase": "writer",
      "mode": "initial_draft",
      "scope_profile": "integration",
      "required_groups": ["global_core", "writer_core", "writer_integration_coverage"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 180,
      "rationale": "Confirmed scope with integration/API/async/internal effects where fake internal coverage is the primary risk."
    },
    {
      "id": "writer.revision_from_findings",
      "phase": "writer",
      "mode": "revision_from_findings",
      "scope_profile": "any",
      "required_groups": ["global_core", "writer_core", "writer_process_artifacts", "writer_revision_artifacts"],
      "conditional_groups": ["writer_table_artifacts", "writer_ui_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 180,
      "rationale": "Revision of an existing TC set by structured reviewer findings without changing source/scope."
    },
    {
      "id": "writer.remediation.style",
      "phase": "writer",
      "mode": "remediation",
      "scope_profile": "style",
      "required_groups": ["global_core", "writer_core", "style_remediation"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 180,
      "rationale": "Style/wording remediation after reviewer or validator finding."
    },
    {
      "id": "writer.remediation.validator_failure",
      "phase": "writer",
      "mode": "remediation",
      "scope_profile": "validator_failure",
      "required_groups": ["global_core", "writer_core", "writer_validator_failure_deep"],
      "conditional_groups": ["writer_process_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_revision_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 292,
      "rationale": "Deep repair context after validator or Writer Quality Gate failure."
    },
    {
      "id": "writer.session_initial_draft",
      "phase": "writer",
      "mode": "session_initial_draft",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "writer_core", "writer_process_artifacts"],
      "conditional_groups": ["writer_table_artifacts", "writer_ui_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_revision_artifacts", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 200,
      "rationale": "Initial writer session inside the session-based review cycle."
    },
    {
      "id": "writer.session_semantic_revision",
      "phase": "writer",
      "mode": "session_semantic_revision",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "writer_core", "writer_process_artifacts", "writer_revision_artifacts"],
      "conditional_groups": ["writer_table_artifacts", "writer_ui_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 240,
      "rationale": "Writer semantic revision session after semantic reviewer findings."
    },
    {
      "id": "writer.session_format_revision",
      "phase": "writer",
      "mode": "session_format_revision",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "writer_core", "writer_process_artifacts", "style_remediation"],
      "conditional_groups": ["writer_revision_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 240,
      "rationale": "Format-only writer revision after final structure/format review."
    },
    {
      "id": "reviewer.full_existing_cases",
      "phase": "reviewer",
      "mode": "full",
      "scope_profile": "any",
      "required_groups": ["global_core", "reviewer_core", "reviewer_process_artifacts"],
      "conditional_groups": ["source_locator_core", "scope_manual_core", "scope_table_artifacts", "scope_ui_artifacts", "writer_table_artifacts", "writer_revision_artifacts", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 257,
      "rationale": "Direct review of an existing test-case set for an already confirmed FT package and scope; includes mandatory semantic rubric, defect taxonomy and dictionary checks."
    },
    {
      "id": "reviewer.scope_gap_review",
      "phase": "reviewer",
      "mode": "scope_gap_review",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "reviewer_scope_gap_core", "reviewer_process_artifacts"],
      "conditional_groups": ["source_locator_core", "scope_manual_core", "scope_table_artifacts", "scope_ui_artifacts", "writer_core"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 230,
      "rationale": "Session-based pre-writer review of scope coverage gaps, source anchors and clarification requests."
    },
    {
      "id": "reviewer.structure_preflight",
      "phase": "reviewer",
      "mode": "structure_preflight",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "reviewer_structure_preflight_core", "reviewer_process_artifacts"],
      "conditional_groups": ["source_locator_core", "scope_manual_core", "writer_table_artifacts", "writer_ui_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 210,
      "rationale": "Session-based lightweight structure preflight before semantic review."
    },
    {
      "id": "reviewer.semantic_traceability_test_design",
      "phase": "reviewer",
      "mode": "semantic_traceability_test_design",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "reviewer_semantic_core", "reviewer_process_artifacts"],
      "conditional_groups": ["source_locator_core", "scope_manual_core", "scope_table_artifacts", "scope_ui_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 290,
      "rationale": "Session-based semantic review for traceability and test-design, before format polishing."
    },
    {
      "id": "reviewer.structure_format_final",
      "phase": "reviewer",
      "mode": "structure_format_final",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "reviewer_structure_format_core", "reviewer_process_artifacts"],
      "conditional_groups": ["reviewer_semantic_core", "writer_revision_artifacts", "writer_table_artifacts", "writer_ui_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 260,
      "rationale": "Final structure and formatting review after semantic closure."
    },
    {
      "id": "reviewer.semantic_regression",
      "phase": "reviewer",
      "mode": "semantic_regression",
      "scope_profile": "any",
      "required_groups": ["global_core", "review_cycle_core", "reviewer_semantic_regression_core", "reviewer_process_artifacts"],
      "conditional_groups": ["reviewer_structure_format_core", "writer_revision_artifacts", "writer_table_artifacts", "writer_ui_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 260,
      "rationale": "Final semantic regression pass after format-only changes."
    },
    {
      "id": "scope.manual",
      "phase": "scope",
      "mode": "manual",
      "scope_profile": "any",
      "required_groups": ["global_core", "source_locator_core", "scope_manual_core"],
      "conditional_groups": ["scope_table_artifacts", "scope_ui_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 260,
      "rationale": "Manual scope selection when the user already provides the intended section or boundary."
    },
    {
      "id": "scope.agent_proposed",
      "phase": "scope",
      "mode": "agent_proposed",
      "scope_profile": "any",
      "required_groups": ["global_core", "source_locator_core", "scope_agent_proposed_core"],
      "conditional_groups": ["scope_manual_core"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 220,
      "rationale": "Candidate-scope proposal before the user confirms one external scope."
    },
    {
      "id": "iteration.full_loop",
      "phase": "iteration",
      "mode": "full_loop",
      "scope_profile": "any",
      "required_groups": ["global_core", "source_locator_core", "scope_manual_core", "iteration_core", "writer_core", "writer_process_artifacts", "writer_revision_artifacts", "reviewer_core"],
      "conditional_groups": ["scope_table_artifacts", "scope_ui_artifacts", "writer_table_artifacts", "writer_ui_artifacts", "writer_numeric_coverage", "writer_integration_coverage", "writer_validator_failure_deep", "style_remediation"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 438,
      "rationale": "End-to-end session-based writer/reviewer orchestration context; includes the lifecycle transition matrix and runner gates. Table/UI details remain conditional to the concrete scope profile and semantic reviewer safeguards remain required."
    },
    {
      "id": "ui_automation_prep.signed_off",
      "phase": "ui_automation_prep",
      "mode": "signed_off",
      "scope_profile": "any",
      "required_groups": ["global_core", "ui_automation_prep_core"],
      "conditional_groups": ["source_locator_core", "scope_manual_core", "iteration_core", "reviewer_core"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 210,
      "rationale": "Post-sign-off UI verification and automation-ready preparation without rewriting the FT-first baseline."
    },
    {
      "id": "architecture.audit",
      "phase": "architecture",
      "mode": "audit",
      "scope_profile": "any",
      "required_groups": ["global_core", "architecture_audit_core"],
      "conditional_groups": ["audit_only_history"],
      "audit_only_groups": [],
      "budget_limit_kib": 130,
      "rationale": "Agent-layer governance audit with script-first workflow and manual interpretation."
    },
    {
      "id": "sdk_orchestration.review_cycle",
      "phase": "sdk_orchestration",
      "mode": "review_cycle",
      "scope_profile": "any",
      "required_groups": ["global_core", "sdk_orchestration_core"],
      "conditional_groups": ["writer_core", "reviewer_core", "writer_process_artifacts", "reviewer_process_artifacts"],
      "audit_only_groups": ["audit_only_history", "governance_audit_only"],
      "budget_limit_kib": 130,
      "rationale": "Codex SDK runner context for session-based review-cycle orchestration."
    }
  ]
}
```

## Правила сопровождения

- Добавляй новый scenario только если он меняет набор runtime instructions.
- Не копируй сюда procedural workflow из `SKILL.md` или QA-правила из `references/qa`.
- Если reference нужен только для audit, migration или historical debt review, держи его в `audit_only_groups`.
- После изменения manifest запускай:

```powershell
python scripts/resolve_instruction_context.py --scenario writer.initial_draft.simple --budget-report
python scripts/run_tests.py --suite architecture
```
