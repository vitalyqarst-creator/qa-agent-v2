from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    CompletedPackageRegressionReport,
    build_completed_package_regression,
    load_completed_package_regression,
    write_completed_package_regression,
)
from test_case_agent.writer_dry_run_proposals import compute_file_sha256


PKG2_OLD = ["REQ-AUTOFIN-3D1FEBD741A1", "REQ-AUTOFIN-63CC9F1AC781"]
PKG2_NEW = ["REQ-AUTOFIN-339239217ED5", "REQ-AUTOFIN-75E43AC628D5"]
PKG3_OLD = ["REQ-AUTOFIN-03B83DF07255", "REQ-AUTOFIN-EDDF1133C9DF"]
PKG3_NEW = ["REQ-AUTOFIN-FC1ED982E572", "REQ-AUTOFIN-DDBC8DCB97AF"]


class CompletedPackageRegressionTests(unittest.TestCase):
    def test_passes_when_completed_package_validations_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = build_regression(ctx)

            self.assertEqual("pass-with-warnings", report.regression_status)
            self.assertEqual(2, len(report.completed_packages))
            self.assertEqual(3, len(report.validated_test_cases))
            self.assertEqual(2, report.final_state_valid_count)
            self.assertEqual(2, report.safe_for_next_stage_count)
            self.assertTrue(report.old_refs_absent)
            self.assertTrue(report.new_refs_present)
            self.assertFalse(report.duplicate_req_refs_found)
            self.assertEqual([], report.regressions_found)
            self.assertEqual([], report.blocking_reasons)

    def test_passes_with_warning_when_git_state_is_clean_and_final_state_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)

            report = build_regression(ctx)

            self.assertEqual("pass-with-warnings", report.regression_status)
            self.assertEqual([], report.git_state_summary["changed_test_case_files"])

    def test_fails_if_final_new_req_refs_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg2_file, PKG2_NEW[1], "")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("WPKG-000002.TC-ACCEI-012.new_refs_present", report.failed_checks)

    def test_fails_if_old_intermediate_refs_are_still_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg3_file, PKG3_NEW[0], f"{PKG3_NEW[0]}, {PKG3_OLD[0]}")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("WPKG-000003.TC-AMSR-012.old_refs_absent", report.failed_checks)

    def test_fails_if_duplicate_req_refs_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg2_file, PKG2_NEW[0], f"{PKG2_NEW[0]}, {PKG2_NEW[0]}")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertTrue(report.duplicate_req_refs_found)

    def test_fails_if_expected_tc_block_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg2_file, "## TC-ACCEI-013", "## TC-ACCEI-013-MISSING")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("WPKG-000002.TC-ACCEI-013.tc_block_once", report.failed_checks)

    def test_fails_if_expected_tc_has_no_traceability_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg3_file, "**Traceability:**", "**Trace:**")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("WPKG-000003.TC-AMSR-012.traceability_line_once", report.failed_checks)

    def test_fails_if_unrelated_tc_contains_completed_intermediate_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            replace_in_file(ctx.pkg2_file, "**Traceability:** BSR 999", f"**Traceability:** BSR 999; {PKG2_OLD[0]}")

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("collateral.TC-OTHER.no_intermediate_refs", report.failed_checks)

    def test_fails_if_update_plan_mapping_does_not_match_completed_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            data = json.loads(ctx.update_plan_path.read_text(encoding="utf-8"))
            data["plan_items"][0]["new_refs"] = ["REQ-AUTOFIN-BADBADBADBAD"]
            write_json(ctx.update_plan_path, data)

            report = build_regression(ctx)

            self.assertEqual("failed", report.regression_status)
            self.assertIn("WPKG-000002.update_plan_completed_mappings_match", report.failed_checks)

    def test_json_and_markdown_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            report = build_regression(ctx)

            json_path, markdown_path = write_completed_package_regression(report, ctx.work_dir)
            loaded = load_completed_package_regression(json_path)
            markdown = markdown_path.read_text(encoding="utf-8")

            self.assertIsInstance(loaded, CompletedPackageRegressionReport)
            self.assertIn("Completed Package Regression", markdown)
            self.assertTrue(json_path.name.endswith("WPKG-000002-WPKG-000003.json"))

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx = setup_context(temp_dir)
            before = {
                ctx.pkg2_file: compute_file_sha256(ctx.pkg2_file),
                ctx.pkg3_file: compute_file_sha256(ctx.pkg3_file),
            }

            report = build_regression(ctx)
            write_completed_package_regression(report, ctx.work_dir)

            self.assertEqual(before[ctx.pkg2_file], compute_file_sha256(ctx.pkg2_file))
            self.assertEqual(before[ctx.pkg3_file], compute_file_sha256(ctx.pkg3_file))


class Context:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.work_dir = root / "fts" / "AutoFin" / "work" / "e2e-dry-run" / "run"
        self.test_cases_dir = root / "fts" / "AutoFin" / "test-cases"
        self.pkg2_file = self.test_cases_dir / "14-application-card-client-contacts-and-extra-info.md"
        self.pkg3_file = self.test_cases_dir / "section-4.2-applications-menu-search.md"
        self.update_plan_path = self.work_dir / "test-case-update-plan.autofin-prefinal-to-autofin-final.json"
        self.old_registry_path = self.work_dir / "requirements.autofin-prefinal.jsonl"
        self.new_registry_path = self.work_dir / "requirements.autofin-final.jsonl"


def setup_context(temp_dir: str) -> Context:
    root = Path(temp_dir)
    run_git(root, ["init"])
    run_git(root, ["config", "user.email", "tests@example.com"])
    run_git(root, ["config", "user.name", "Tests"])
    ctx = Context(root)
    ctx.work_dir.mkdir(parents=True)
    ctx.test_cases_dir.mkdir(parents=True)
    ctx.pkg2_file.write_text(pkg2_text(PKG2_NEW), encoding="utf-8", newline="\n")
    ctx.pkg3_file.write_text(pkg3_text(PKG3_NEW), encoding="utf-8", newline="\n")
    write_artifacts(ctx)
    run_git(root, ["add", "fts/AutoFin/test-cases"])
    run_git(root, ["commit", "-m", "baseline-final"])
    return ctx


def build_regression(ctx: Context) -> CompletedPackageRegressionReport:
    return build_completed_package_regression(
        work_dir=ctx.work_dir,
        test_cases_dir=ctx.test_cases_dir,
        update_plan_path=ctx.update_plan_path,
        old_registry_path=ctx.old_registry_path,
        new_registry_path=ctx.new_registry_path,
        workspace_root=ctx.root,
    )


def pkg2_text(refs: list[str]) -> str:
    reqs = ", ".join(refs)
    return (
        "## TC-ACCEI-012\n\n"
        f"**Traceability:** ATOM-013; BSR 173; WP-01; REQ: {reqs}\n\n"
        "### Steps\n\n1. Step.\n\n"
        "## TC-ACCEI-013\n\n"
        f"**Traceability:** ATOM-015; BSR 182; WP-01; REQ: {reqs}\n\n"
        "### Steps\n\n1. Step.\n\n"
        "## TC-OTHER\n\n"
        "**Traceability:** BSR 999\n"
    )


def pkg3_text(refs: list[str]) -> str:
    reqs = ", ".join(refs)
    return (
        "## TC-AMSR-012\n\n"
        f"**Traceability:** ATOM-020; BSR 28; BSR 29; SRC-020; DICT-EMP-01; GAP-003; GAP-005; REQ: {reqs}\n\n"
        "### Steps\n\n1. Step.\n"
    )


def write_artifacts(ctx: Context) -> None:
    write_json(ctx.update_plan_path, update_plan_payload())
    refs = [{"req_uid": ref} for ref in [*PKG2_OLD, *PKG2_NEW, *PKG3_OLD, *PKG3_NEW]]
    write_jsonl(ctx.old_registry_path, refs[:4])
    write_jsonl(ctx.new_registry_path, refs[4:])
    for package_id, file_path, tc_ids, old_refs, new_refs in [
        ("WPKG-000002", ctx.pkg2_file, ["TC-ACCEI-012", "TC-ACCEI-013"], PKG2_OLD, PKG2_NEW),
        ("WPKG-000003", ctx.pkg3_file, ["TC-AMSR-012"], PKG3_OLD, PKG3_NEW),
    ]:
        suffix = f"{package_id}-after-backfill"
        write_json(ctx.work_dir / f"writer-traceability-post-apply-validation-{suffix}.json", validation_payload(package_id, file_path, tc_ids))
        write_json(ctx.work_dir / f"writer-dry-run-proposal-{suffix}.json", proposal_payload(package_id, file_path, tc_ids, old_refs, new_refs))
        write_json(ctx.work_dir / f"writer-proposal-review-{suffix}.json", review_payload(package_id))
        write_json(ctx.work_dir / f"writer-traceability-update-apply-{suffix}.json", apply_payload(package_id, file_path, tc_ids, old_refs, new_refs))


def update_plan_payload() -> dict:
    items = []
    counter = 1
    for package_tcs, old_refs, new_refs in [
        (["TC-ACCEI-012", "TC-ACCEI-013"], PKG2_OLD, PKG2_NEW),
        (["TC-AMSR-012"], PKG3_OLD, PKG3_NEW),
    ]:
        for tc_id in package_tcs:
            for old_ref, new_ref in zip(old_refs, new_refs):
                items.append({
                    "plan_item_id": f"PLAN-{counter:06d}",
                    "impact_id": f"IMP-{counter:06d}",
                    "change_id": f"CHG-{counter:06d}",
                    "test_case_id": tc_id,
                    "file_path": "dummy.md",
                    "action": "traceability_update_only",
                    "apply_mode": "safe_auto_candidate",
                    "old_refs": [old_ref],
                    "new_refs": [new_ref],
                    "required_changes": [],
                    "forbidden_changes": [],
                    "rationale": [],
                    "requires_manual_review": True,
                    "warnings": [],
                })
                counter += 1
    return {
        "ft_slug": "AutoFin",
        "old_source_version": "old",
        "new_source_version": "new",
        "impact_report_path": "impact.json",
        "test_cases_dir": "fts/AutoFin/test-cases",
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "plan_items": items,
        "summary": {},
        "warnings": [],
        "blocking_reasons": [],
    }


def validation_payload(package_id: str, file_path: Path, tc_ids: list[str]) -> dict:
    return {
        "package_id": package_id,
        "validation_status": "pass-with-warnings",
        "final_state_valid": True,
        "git_change_state": "final_state_already_baselined",
        "safe_to_commit": False,
        "safe_for_next_stage": True,
        "commit_action": "nothing_to_commit",
        "file_path": str(file_path),
        "affected_test_case_ids": tc_ids,
        "checks": [],
        "failed_checks": [],
        "warnings": [],
        "blocking_reasons": [],
        "git_state": {},
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
    }


def proposal_payload(package_id: str, file_path: Path, tc_ids: list[str], old_refs: list[str], new_refs: list[str]) -> dict:
    changes = []
    counter = 1
    for tc_id in tc_ids:
        for old_ref, new_ref in zip(old_refs, new_refs):
            changes.append({
                "plan_item_id": f"PLAN-{counter:06d}",
                "impact_id": f"IMP-{counter:06d}",
                "change_id": f"CHG-{counter:06d}",
                "test_case_id": tc_id,
                "change_type": "traceability_ref_replace",
                "old_ref": old_ref,
                "new_ref": new_ref,
                "status": "proposed",
            })
            counter += 1
    return {
        "package_id": package_id,
        "file_path": str(file_path),
        "affected_test_case_ids": tc_ids,
        "source_plan_item_ids": [change["plan_item_id"] for change in changes],
        "source_impact_ids": [change["impact_id"] for change in changes],
        "source_change_ids": [change["change_id"] for change in changes],
        "proposal_status": "pass-with-warnings",
        "risk_level": "low",
        "manual_review_required": True,
        "proposed_changes": changes,
        "rationale": [],
        "missing_information": [],
        "original_tc_blocks": {},
        "proposed_tc_blocks": {},
        "unified_diff_preview": "",
        "sha256_before": "sha",
        "sha256_after": "sha",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def review_payload(package_id: str) -> dict:
    return {
        "package_id": package_id,
        "review_status": "approved-with-warnings",
        "safe_for_controlled_apply": True,
        "risk_level": "medium",
        "checks": [],
        "failed_checks": [],
        "warnings": [],
        "blocking_reasons": [],
        "reviewer_recommendation": "safe",
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "git_state": {},
    }


def apply_payload(package_id: str, file_path: Path, tc_ids: list[str], old_refs: list[str], new_refs: list[str]) -> dict:
    changes = []
    counter = 1
    for tc_id in tc_ids:
        for old_ref, new_ref in zip(old_refs, new_refs):
            changes.append({
                "plan_item_id": f"PLAN-{counter:06d}",
                "impact_id": f"IMP-{counter:06d}",
                "change_id": f"CHG-{counter:06d}",
                "test_case_id": tc_id,
                "old_ref": old_ref,
                "new_ref": new_ref,
                "old_traceability_line": old_ref,
                "new_traceability_line": new_ref,
                "status": "applied",
            })
            counter += 1
    return {
        "package_id": package_id,
        "apply_status": "applied",
        "dry_run": False,
        "file_path": str(file_path),
        "affected_test_case_ids": tc_ids,
        "applied_changes": changes,
        "previewed_changes": [],
        "skipped_changes": [],
        "backup_path": "backup.bak",
        "sha256_before": "before",
        "sha256_after": "after",
        "files_changed_count": 1,
        "input_paths": {},
        "created_at_utc": "2026-07-05T00:00:00Z",
        "created_by_tool": "tests",
        "warnings": [],
        "blocking_reasons": [],
    }


def replace_in_file(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8", newline="\n")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8", newline="\n")


def run_git(root: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


if __name__ == "__main__":
    unittest.main()
