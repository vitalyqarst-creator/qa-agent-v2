from __future__ import annotations

import json
import unittest

from test_case_agent.review_cycle.evidence_access import validate_evidence_access
from test_case_agent.review_cycle.prepared_package import SourceRegistryEntry


def event(item_id: str, item_type: str, **fields) -> str:
    return json.dumps(
        {"type": "item.completed", "item": {"id": item_id, "type": item_type, **fields}}
    ) + "\n"


class PreparedEvidenceAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceRegistryEntry(
            path="fts/demo/source/main.xhtml",
            sha256="0" * 64,
            role="machine-readable",
            locator="SRC-001 exact row",
        )

    def validate(self, events: str, *, allowed_stage_roots=()):
        return validate_evidence_access(
            events_text=events,
            forbidden_roots=("fts/demo/test-cases", "fts/demo/work/canary-runs"),
            source_registry=(self.source,),
            allowed_stage_roots=allowed_stage_roots,
        )

    def test_allows_narrow_prepared_input_commands(self) -> None:
        result = self.validate(
            event("cmd-1", "command_execution", command="Get-Content fts/demo/work/prepared-input/payload.md")
        )
        self.assertTrue(result.passed)
        self.assertEqual(1, result.commands_checked)

    def test_blocks_forbidden_root_and_broad_scan(self) -> None:
        result = self.validate(
            event("cmd-1", "command_execution", command="Get-Content fts/demo/test-cases/old.md")
            + event("cmd-2", "command_execution", command="rg --files")
        )
        ids = {finding["id"] for finding in result.findings}
        self.assertFalse(result.passed)
        self.assertIn("forbidden-evidence-root-access", ids)
        self.assertIn("unbounded-prepared-stage-scan", ids)

    def test_allows_current_stage_output_nested_under_forbidden_cycle_root(self) -> None:
        stage_root = "fts/demo/work/canary-runs/current/attempts/writer-r1/attempt-001/stage-output"
        result = self.validate(
            event(
                "cmd-1",
                "command_execution",
                command=f"Get-Content {stage_root}/draft.md",
            ),
            allowed_stage_roots=(stage_root,),
        )
        self.assertTrue(result.passed)

    def test_allowed_stage_root_does_not_hide_sibling_cycle_access(self) -> None:
        stage_root = "fts/demo/work/canary-runs/current/attempts/writer-r1/attempt-001/stage-output"
        result = self.validate(
            event(
                "cmd-1",
                "command_execution",
                command=(
                    f"Get-Content {stage_root}/draft.md; "
                    "Get-Content fts/demo/work/canary-runs/sibling/cycle-state.yaml"
                ),
            ),
            allowed_stage_roots=(stage_root,),
        )
        self.assertFalse(result.passed)
        self.assertIn(
            "forbidden-evidence-root-access",
            {finding["id"] for finding in result.findings},
        )

    def test_allowed_stage_root_rejects_path_traversal(self) -> None:
        stage_root = "fts/demo/work/canary-runs/current/attempts/writer-r1/attempt-001/stage-output"
        result = self.validate(
            event(
                "cmd-1",
                "command_execution",
                command=f"Get-Content {stage_root}/../runner-output/events.ndjson",
            ),
            allowed_stage_roots=(stage_root,),
        )
        self.assertFalse(result.passed)
        self.assertIn(
            "forbidden-evidence-root-access",
            {finding["id"] for finding in result.findings},
        )

    def test_blocks_full_source_without_exact_fallback(self) -> None:
        result = self.validate(
            event("cmd-1", "command_execution", command="Get-Content fts/demo/source/main.xhtml")
        )
        self.assertFalse(result.passed)
        self.assertEqual("unapproved-full-source-access", result.findings[0]["id"])

    def test_allows_full_source_after_exact_fallback_event(self) -> None:
        result = self.validate(
            event(
                "msg-1",
                "agent_message",
                text=(
                    "targeted_source_fallback path=fts/demo/source/main.xhtml "
                    "locator=SRC-001 exact row"
                ),
            )
            + event("cmd-1", "command_execution", command="Get-Content fts/demo/source/main.xhtml")
        )
        self.assertTrue(result.passed)
        self.assertTrue(result.accesses[0]["authorized"])

    def test_late_fallback_message_cannot_authorize_prior_access(self) -> None:
        result = self.validate(
            event("cmd-1", "command_execution", command="Get-Content fts/demo/source/main.xhtml")
            + event(
                "msg-1",
                "agent_message",
                text=(
                    "targeted_source_fallback path=fts/demo/source/main.xhtml "
                    "locator=SRC-001 exact row"
                ),
            )
        )
        self.assertFalse(result.passed)

    def test_reviewer_policy_allows_only_explicit_environment_probe(self) -> None:
        result = validate_evidence_access(
            events_text=event(
                "cmd-1",
                "command_execution",
                command="powershell -Command python scripts/probe_environment.py",
            ),
            forbidden_roots=("skills", "references", "prepared-input"),
            source_registry=(self.source,),
            allowed_command_fragments=("python scripts/probe_environment.py",),
            reject_unlisted_commands=True,
        )
        self.assertTrue(result.passed)

    def test_reviewer_policy_blocks_skill_read_even_when_narrow(self) -> None:
        result = validate_evidence_access(
            events_text=event(
                "cmd-1",
                "command_execution",
                command="Get-Content skills/ft-test-case-reviewer/SKILL.md",
            ),
            forbidden_roots=("skills", "references", "prepared-input"),
            source_registry=(self.source,),
            allowed_command_fragments=("python scripts/probe_environment.py",),
            reject_unlisted_commands=True,
        )
        ids = {finding["id"] for finding in result.findings}
        self.assertIn("unapproved-prepared-stage-command", ids)
        self.assertIn("forbidden-evidence-root-access", ids)


if __name__ == "__main__":
    unittest.main()
