from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.audit_autofin_bsr_coverage import collect_artifact_refs, scope_guess


class AutoFinBsrCoverageAuditTests(unittest.TestCase):
    def test_final_confirmed_scope_ranges_are_not_shifted_to_prefinal_scopes(self) -> None:
        self.assertEqual("section-4.2-applications-menu-search", scope_guess(35))
        self.assertEqual("section-4.2-applications-menu-search", scope_guess(38))
        self.assertEqual("27-calculator-summary-final-source-rebase", scope_guess(43))
        self.assertEqual("27-calculator-summary-final-source-rebase", scope_guess(46))
        self.assertEqual("unmapped-final-source", scope_guess(47))

    def test_only_active_in_scope_source_rows_count_as_mappings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fts" / "AutoFin"
            active = root / "work" / "stage-handoffs" / "27-scope"
            active.mkdir(parents=True)
            active.joinpath("source-row-inventory.md").write_text(
                "| requirement_codes | in_scope |\n"
                "| --- | --- |\n"
                "| `BSR 43`; `BSR 44` | `yes` |\n"
                "| `BSR 35` | `no` |\n",
                encoding="utf-8",
            )
            historical = root / "work" / "review-cycles" / "old"
            historical.mkdir(parents=True)
            historical.joinpath("source-row-inventory.md").write_text(
                "| requirement_codes | in_scope |\n"
                "| --- | --- |\n"
                "| `BSR 35` | `yes` |\n",
                encoding="utf-8",
            )

            refs = collect_artifact_refs(root)

        self.assertEqual({43, 44}, set(refs))


if __name__ == "__main__":
    unittest.main()
