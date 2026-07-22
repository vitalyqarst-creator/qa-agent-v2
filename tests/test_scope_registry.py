from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.scope_registry import (
    ScopeRegistry,
    ScopeRegistryError,
    load_and_resolve_scope_registry,
    load_scope_registry,
    resolve_scope_registry,
)


class ScopeRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.package_root = Path(self.temporary_directory.name) / "ft-package"
        (self.package_root / "source").mkdir(parents=True)
        (self.package_root / "support").mkdir()
        (self.package_root / "source" / "requirements.docx").write_bytes(b"docx")
        (self.package_root / "source" / "requirements.xhtml").write_text(
            "<html/>", encoding="utf-8"
        )
        (self.package_root / "source" / "requirements.pdf").write_bytes(b"pdf")
        (self.package_root / "AGENT-NOTES.md").write_text("notes", encoding="utf-8")
        (self.package_root / "support" / "clarifications.md").write_text(
            "support", encoding="utf-8"
        )

    @staticmethod
    def scope_payload(scope_id: str = "client-addresses") -> dict[str, object]:
        return {
            "scope_id": scope_id,
            "tc_prefix": "ADDR",
            "source_set": {
                "docx": "source/requirements.docx",
                "xhtml": "source/requirements.xhtml",
                "pdf": "source/requirements.pdf",
            },
            "boundary": {
                "container_xpath": "/*/*[2]/*[116]",
                "row_ranges": [
                    {"role": "context", "start": 32, "end": 32},
                    {"role": "testable", "start": 33, "end": 58},
                ],
                "cross_references": [
                    {
                        "reference_id": "BSR-324-address-decomposition",
                        "xpath": "/*/*[2]/*[119]/*[1]",
                    }
                ],
            },
            "requirement_guard": {
                "allowed_ranges": [
                    {"prefix": "BSR", "start": 115, "end": 161},
                    {"prefix": "GSR", "start": 2, "end": 2},
                ],
                "excluded_codes": ["BSR 160"],
            },
            "reference_paths": [
                "AGENT-NOTES.md",
                "support/clarifications.md",
            ],
            "fixture_ids": ["FX-DADATA-ADDR-POS-001", "FX-DADATA-ADDR-NEG-001"],
            "gap_ids": ["ADDR-001", "ADDR-002"],
            "execution_profile": "standard-production",
        }

    @classmethod
    def registry_payload(cls) -> dict[str, object]:
        return {"version": 1, "scopes": [cls.scope_payload()]}

    def assert_error(
        self,
        code: str,
        payload: dict[str, object],
        *,
        resolve: bool = False,
    ) -> None:
        with self.assertRaises(ScopeRegistryError) as caught:
            if resolve:
                resolve_scope_registry(payload, self.package_root)
            else:
                ScopeRegistry.from_dict(payload)
        self.assertEqual(code, caught.exception.code)

    def test_valid_registry_resolves_only_package_local_files(self) -> None:
        resolved = resolve_scope_registry(self.registry_payload(), self.package_root)

        scope = resolved.get("client-addresses")
        self.assertEqual(self.package_root.resolve(), resolved.package_root)
        self.assertEqual(
            (self.package_root / "source" / "requirements.docx").resolve(),
            scope.source_set.docx,
        )
        self.assertEqual(
            (self.package_root / "source" / "requirements.xhtml").resolve(),
            scope.source_set.xhtml,
        )
        self.assertEqual(
            (self.package_root / "source" / "requirements.pdf").resolve(),
            scope.source_set.pdf,
        )
        self.assertEqual(2, len(scope.reference_paths))
        self.assertTrue(
            all(
                path.is_relative_to(resolved.package_root)
                for path in scope.reference_paths
            )
        )
        self.assertTrue(scope.definition.requirement_guard.allows("BSR 115"))
        self.assertEqual("ADDR", scope.definition.tc_prefix)
        self.assertFalse(scope.definition.requirement_guard.allows("BSR 160"))
        self.assertFalse(scope.definition.requirement_guard.allows("BSR 162"))
        self.assertRegex(resolved.digest, r"^[0-9a-f]{64}$")

    def test_pdf_is_optional_but_docx_and_xhtml_are_mandatory(self) -> None:
        payload = self.registry_payload()
        del payload["scopes"][0]["source_set"]["pdf"]  # type: ignore[index]

        resolved = resolve_scope_registry(payload, self.package_root)

        self.assertIsNone(resolved.scopes[0].source_set.pdf)
        for field in ("docx", "xhtml"):
            invalid = self.registry_payload()
            del invalid["scopes"][0]["source_set"][field]  # type: ignore[index]
            with self.subTest(field=field):
                self.assert_error("invalid-fields", invalid)

    def test_declared_source_and_reference_files_must_exist(self) -> None:
        for field, relative_path in (
            ("docx", "source/missing.docx"),
            ("xhtml", "source/missing.xhtml"),
            ("pdf", "source/missing.pdf"),
        ):
            payload = self.registry_payload()
            payload["scopes"][0]["source_set"][field] = relative_path  # type: ignore[index]
            with self.subTest(field=field):
                self.assert_error("missing-package-file", payload, resolve=True)

        payload = self.registry_payload()
        payload["scopes"][0]["reference_paths"] = ["support/missing.md"]  # type: ignore[index]
        self.assert_error("missing-package-file", payload, resolve=True)

    def test_selected_scope_resolves_without_unrelated_missing_files(self) -> None:
        payload = self.registry_payload()
        unrelated = self.scope_payload("unrelated-scope")
        unrelated["tc_prefix"] = "OTHER"
        unrelated["source_set"] = {
            "docx": "source/unrelated-missing.docx",
            "xhtml": "source/unrelated-missing.xhtml",
        }
        payload["scopes"].append(unrelated)  # type: ignore[union-attr]

        selected = resolve_scope_registry(
            payload,
            self.package_root,
            scope_id="client-addresses",
        )

        self.assertEqual(1, len(selected.scopes))
        self.assertEqual("client-addresses", selected.scopes[0].definition.scope_id)
        with self.assertRaises(ScopeRegistryError) as caught:
            resolve_scope_registry(payload, self.package_root)
        self.assertEqual("missing-package-file", caught.exception.code)

    def test_selected_scope_still_requires_full_registry_syntax(self) -> None:
        payload = self.registry_payload()
        unrelated = self.scope_payload("unrelated-scope")
        unrelated["requirement_text"] = "semantic content is forbidden"
        payload["scopes"].append(unrelated)  # type: ignore[union-attr]

        with self.assertRaises(ScopeRegistryError) as caught:
            resolve_scope_registry(
                payload,
                self.package_root,
                scope_id="client-addresses",
            )

        self.assertEqual("invalid-fields", caught.exception.code)

    def test_registry_digest_is_invariant_to_unordered_declaration_order(self) -> None:
        first = self.registry_payload()
        second = copy.deepcopy(first)
        scope = second["scopes"][0]  # type: ignore[index]
        scope["boundary"]["row_ranges"].reverse()  # type: ignore[index]
        scope["boundary"]["cross_references"].reverse()  # type: ignore[index]
        scope["requirement_guard"]["allowed_ranges"].reverse()  # type: ignore[index]
        scope["reference_paths"].reverse()  # type: ignore[index]
        scope["fixture_ids"].reverse()  # type: ignore[index]
        scope["gap_ids"].reverse()  # type: ignore[index]
        added_scope = self.scope_payload("employment-main-work")
        first["scopes"].append(added_scope)  # type: ignore[union-attr]
        second["scopes"].insert(  # type: ignore[union-attr]
            0, copy.deepcopy(added_scope)
        )

        first_registry = ScopeRegistry.from_dict(first)
        second_registry = ScopeRegistry.from_dict(second)

        self.assertEqual(first_registry.to_dict(), second_registry.to_dict())
        self.assertEqual(first_registry.digest, second_registry.digest)

    def test_tc_prefix_is_required_strict_and_digest_bound(self) -> None:
        missing = self.registry_payload()
        del missing["scopes"][0]["tc_prefix"]  # type: ignore[index]
        self.assert_error("missing-tc-prefix", missing)

        for invalid_prefix in (
            "A",
            "addr",
            "ADDR_01",
            "-ADDR",
            "ADDR 01",
            "TC-ADDR",
        ):
            payload = self.registry_payload()
            payload["scopes"][0]["tc_prefix"] = invalid_prefix  # type: ignore[index]
            with self.subTest(prefix=invalid_prefix):
                self.assert_error("invalid-tc-prefix", payload)

        first = ScopeRegistry.from_dict(self.registry_payload())
        changed_payload = self.registry_payload()
        changed_payload["scopes"][0]["tc_prefix"] = "ADR2"  # type: ignore[index]
        changed = ScopeRegistry.from_dict(changed_payload)
        self.assertNotEqual(first.digest, changed.digest)

    def test_json_loader_rejects_duplicate_object_keys(self) -> None:
        registry_path = self.package_root / "registry.json"
        registry_path.write_text(
            '{"version":1,"version":1,"scopes":[]}', encoding="utf-8"
        )

        with self.assertRaises(ScopeRegistryError) as caught:
            load_scope_registry(registry_path)

        self.assertEqual("duplicate-json-key", caught.exception.code)

    def test_load_and_resolve_uses_strict_utf8_json(self) -> None:
        registry_path = self.package_root / "scope-registry.json"
        registry_path.write_text(
            json.dumps(self.registry_payload(), ensure_ascii=False), encoding="utf-8"
        )

        resolved = load_and_resolve_scope_registry(registry_path, self.package_root)

        self.assertEqual("client-addresses", resolved.scopes[0].definition.scope_id)

    def test_unknown_or_semantic_content_fields_are_rejected(self) -> None:
        mutations = (
            ((), "requirement_text"),
            (("scopes", 0), "atomic_statements"),
            (("scopes", 0), "obligations"),
            (("scopes", 0), "expected_results"),
            (("scopes", 0, "boundary"), "source_text"),
            (("scopes", 0, "requirement_guard"), "test_cases"),
        )
        for path, forbidden_key in mutations:
            payload = self.registry_payload()
            target: object = payload
            for part in path:
                target = target[part]  # type: ignore[index]
            target[forbidden_key] = "must not be stored here"  # type: ignore[index]
            with self.subTest(key=forbidden_key):
                self.assert_error("invalid-fields", payload)

    def test_relative_paths_reject_traversal_absolute_and_windows_forms(self) -> None:
        invalid_paths = (
            "../outside.docx",
            "/absolute.docx",
            "C:/outside.docx",
            "source\\requirements.docx",
            "source//requirements.docx",
            "source/./requirements.docx",
        )
        for path in invalid_paths:
            payload = self.registry_payload()
            payload["scopes"][0]["source_set"]["docx"] = path  # type: ignore[index]
            with self.subTest(path=path):
                self.assert_error("invalid-package-path", payload)

    def test_resolver_rejects_a_package_local_symlink_that_escapes_root(self) -> None:
        outside = self.package_root.parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        link = self.package_root / "support" / "outside-link.md"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink creation is unavailable: {error}")
        payload = self.registry_payload()
        payload["scopes"][0]["reference_paths"] = [  # type: ignore[index]
            "support/outside-link.md"
        ]

        self.assert_error("package-path-escape", payload, resolve=True)

    def test_source_extensions_are_type_checked(self) -> None:
        for field, path in (
            ("docx", "source/requirements.pdf"),
            ("xhtml", "source/requirements.html"),
            ("pdf", "source/requirements.docx"),
        ):
            payload = self.registry_payload()
            payload["scopes"][0]["source_set"][field] = path  # type: ignore[index]
            with self.subTest(field=field):
                self.assert_error("invalid-source-extension", payload)

    def test_duplicate_scope_paths_and_ids_are_rejected(self) -> None:
        payload = self.registry_payload()
        payload["scopes"].append(  # type: ignore[union-attr]
            copy.deepcopy(payload["scopes"][0])  # type: ignore[index]
        )
        self.assert_error("duplicate-scope-id", payload)

        list_mutations = (
            ("reference_paths", ["AGENT-NOTES.md", "agent-notes.md"]),
            ("fixture_ids", ["FX-001", "fx-001"]),
            ("gap_ids", ["GAP-001", "gap-001"]),
        )
        for field, duplicate_values in list_mutations:
            payload = self.registry_payload()
            payload["scopes"][0][field] = duplicate_values  # type: ignore[index]
            with self.subTest(field=field):
                self.assert_error("duplicate-value", payload)

        payload = self.registry_payload()
        payload["scopes"][0]["fixture_ids"] = ["SHARED-001"]  # type: ignore[index]
        payload["scopes"][0]["gap_ids"] = ["SHARED-001"]  # type: ignore[index]
        self.assert_error("identifier-namespace-collision", payload)

    def test_row_ranges_must_be_positive_ordered_disjoint_and_testable(self) -> None:
        invalid_cases = (
            (
                "invalid-positive-integer",
                [{"role": "testable", "start": 0, "end": 1}],
            ),
            (
                "invalid-row-range",
                [{"role": "testable", "start": 8, "end": 7}],
            ),
            (
                "overlapping-row-ranges",
                [
                    {"role": "context", "start": 5, "end": 8},
                    {"role": "testable", "start": 8, "end": 10},
                ],
            ),
            (
                "missing-testable-range",
                [{"role": "context", "start": 5, "end": 8}],
            ),
            (
                "invalid-row-role",
                [{"role": "ignored", "start": 5, "end": 8}],
            ),
        )
        for expected_code, ranges in invalid_cases:
            payload = self.registry_payload()
            payload["scopes"][0]["boundary"]["row_ranges"] = ranges  # type: ignore[index]
            with self.subTest(code=expected_code):
                self.assert_error(expected_code, payload)

    def test_xpath_uses_the_existing_fail_closed_child_axis_contract(self) -> None:
        for xpath in ("//table", "/*/*[text()='scope']", "relative/path", "/*/"):
            payload = self.registry_payload()
            boundary = payload["scopes"][0]["boundary"]  # type: ignore[index]
            boundary["container_xpath"] = xpath  # type: ignore[index]
            with self.subTest(xpath=xpath):
                self.assert_error("invalid-container-xpath", payload)

    def test_cross_reference_xpaths_are_structural_and_unique(self) -> None:
        invalid = self.registry_payload()
        invalid["scopes"][0]["boundary"]["cross_references"][0]["xpath"] = "//table"  # type: ignore[index]
        self.assert_error("invalid-cross-reference-xpath", invalid)

        duplicate_id = self.registry_payload()
        references = duplicate_id["scopes"][0]["boundary"]["cross_references"]  # type: ignore[index]
        references.append(copy.deepcopy(references[0]))
        references[1]["xpath"] = "/*/*[2]/*[119]/*[2]"
        self.assert_error("duplicate-cross-reference-id", duplicate_id)

        duplicate_xpath = self.registry_payload()
        references = duplicate_xpath["scopes"][0]["boundary"]["cross_references"]  # type: ignore[index]
        references.append(copy.deepcopy(references[0]))
        references[1]["reference_id"] = "SECOND"
        self.assert_error("duplicate-cross-reference-xpath", duplicate_xpath)

    def test_requirement_ranges_are_positive_disjoint_and_exclusions_are_bounded(self) -> None:
        invalid_cases = (
            (
                "invalid-requirement-range",
                [
                    {"prefix": "BSR", "start": 200, "end": 199},
                ],
                [],
            ),
            (
                "overlapping-requirement-ranges",
                [
                    {"prefix": "BSR", "start": 100, "end": 120},
                    {"prefix": "BSR", "start": 120, "end": 140},
                ],
                [],
            ),
            (
                "invalid-requirement-prefix",
                [{"prefix": "Bsr", "start": 100, "end": 120}],
                [],
            ),
            (
                "excluded-code-outside-guard",
                [{"prefix": "BSR", "start": 100, "end": 120}],
                ["BSR 121"],
            ),
            (
                "invalid-requirement-code",
                [{"prefix": "BSR", "start": 100, "end": 120}],
                ["BSR-101"],
            ),
        )
        for expected_code, ranges, excluded in invalid_cases:
            payload = self.registry_payload()
            guard = payload["scopes"][0]["requirement_guard"]  # type: ignore[index]
            guard["allowed_ranges"] = ranges  # type: ignore[index]
            guard["excluded_codes"] = excluded  # type: ignore[index]
            with self.subTest(code=expected_code):
                self.assert_error(expected_code, payload)

    def test_execution_profile_is_a_small_explicit_enum(self) -> None:
        payload = self.registry_payload()
        payload["scopes"][0]["execution_profile"] = "fast-ish"  # type: ignore[index]

        self.assert_error("invalid-execution-profile", payload)


if __name__ == "__main__":
    unittest.main()
