from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class UiEvidencePolicyTests(unittest.TestCase):
    def test_ui_evidence_policy_defines_status_gate(self) -> None:
        content = (ROOT_DIR / "references" / "agent" / "ui-evidence-policy.md").read_text(encoding="utf-8")

        self.assertIn("Normal UI path", content)
        self.assertIn("DOM-seeded observation", content)
        self.assertIn("Local-only evidence не запрещает `confirmed`", content)
        self.assertIn("DOM-seeded observation не может быть самостоятельным основанием", content)
        self.assertIn("`dom_seeded_policy`: `non-canonical-observation`", content)
        self.assertIn("`downstream_rule`: `dom-seeded-not-confirmed`", content)

    def test_ui_prep_links_to_ui_evidence_policy(self) -> None:
        skill = (ROOT_DIR / "skills" / "ft-ui-automation-prep" / "SKILL.md").read_text(encoding="utf-8")
        format_ref = (ROOT_DIR / "references" / "qa" / "ui-automation-prep-format.md").read_text(encoding="utf-8")
        contracts = (ROOT_DIR / "references" / "agent" / "instruction-contract-index.md").read_text(encoding="utf-8")

        self.assertIn("ui-evidence-policy.md", skill)
        self.assertIn("ui-evidence-policy.md", format_ref)
        self.assertIn("UI evidence trust and portability", contracts)
        self.assertIn("ui-evidence-policy.md", contracts)

    def test_ui_prep_forbids_dom_seeded_confirmation(self) -> None:
        skill = (ROOT_DIR / "skills" / "ft-ui-automation-prep" / "SKILL.md").read_text(encoding="utf-8")
        format_ref = (ROOT_DIR / "references" / "qa" / "ui-automation-prep-format.md").read_text(encoding="utf-8")

        self.assertIn("Не ставь `confirmed` или `mismatch-ft-ui` на основании DOM-seeded observation", skill)
        self.assertIn("DOM-seeded observations не являются normal UI path", format_ref)


if __name__ == "__main__":
    unittest.main()
