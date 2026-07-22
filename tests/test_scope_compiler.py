from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

from test_case_agent.scope_compiler import (
    ScopeCompilationError,
    compile_scope_source,
    validate_manifest_scope_binding,
)
from test_case_agent.scope_registry import resolve_scope_registry


@dataclass(frozen=True)
class _Registered:
    path: str
    sha256: str = ""
    role: str = ""


@dataclass(frozen=True)
class _Row:
    source_row_id: str
    source_path: str
    source_locator: str
    bounded_source_text: str
    source_context_class: str
    candidate_id: str | None
    requirement_codes: tuple[str, ...]


@dataclass(frozen=True)
class _Assertion:
    assertion_id: str
    requirement_codes: tuple[str, ...]


@dataclass(frozen=True)
class _Clarification:
    clarification_id: str
    evidence_source_path: str
    evidence_source_sha256: str
    requirement_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Manifest:
    scope_slug: str
    source_row_extraction_spec_digest: str
    source_row_baseline_digest: str
    source_row_candidate_count: int
    sources: tuple[_Registered, ...]
    source_rows: tuple[_Row, ...]
    assertions: tuple[_Assertion, ...]
    clarifications: tuple[object, ...] = ()
    evidence_sources: tuple[_Registered, ...] = ()
    mockups: tuple[_Registered, ...] = ()


class ScopeCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.repo_root = Path(self.temporary_directory.name)
        self.package_root = self.repo_root / "fts" / "sample"
        (self.package_root / "source").mkdir(parents=True)
        (self.package_root / "support").mkdir()
        (self.package_root / "mockups").mkdir()
        (self.package_root / "source" / "requirements.docx").write_bytes(b"docx")
        (self.package_root / "source" / "requirements.pdf").write_bytes(b"pdf")
        (self.package_root / "support" / "clarifications.md").write_text(
            "clarifications", encoding="utf-8"
        )
        (self.package_root / "mockups" / "screen.png").write_bytes(b"mockup")
        self.xhtml = self.package_root / "source" / "requirements.xhtml"
        self.xhtml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<table>
<tr><td>Контекст раздела</td></tr>
<tr><td>Поле Имя</td><td>BSR 10</td></tr>
<tr><td>Поле Телефон</td><td>BSR 11</td></tr>
</table>
<p>Связанное правило BSR 20</p>
</body></html>
""",
            encoding="utf-8",
        )
        self.registry = resolve_scope_registry(
            {
                "version": 1,
                "scopes": [
                    {
                        "scope_id": "sample-scope",
                        "tc_prefix": "SMP",
                        "source_set": {
                            "docx": "source/requirements.docx",
                            "xhtml": "source/requirements.xhtml",
                            "pdf": "source/requirements.pdf",
                        },
                        "boundary": {
                            "container_xpath": "/*/*[1]/*[1]",
                            "row_ranges": [
                                {"role": "context", "start": 1, "end": 1},
                                {"role": "testable", "start": 2, "end": 3},
                            ],
                            "cross_references": [
                                {
                                    "reference_id": "BSR-20",
                                    "xpath": "/*/*[1]/*[2]",
                                }
                            ],
                        },
                        "requirement_guard": {
                            "allowed_ranges": [
                                {"prefix": "BSR", "start": 10, "end": 11},
                                {"prefix": "BSR", "start": 20, "end": 20},
                            ],
                            "excluded_codes": [],
                        },
                        "reference_paths": [
                            "support/clarifications.md",
                            "mockups/screen.png",
                        ],
                        "fixture_ids": [],
                        "gap_ids": [],
                        "execution_profile": "lean-production",
                    }
                ],
            },
            self.package_root,
        )

    def _compiled(self):
        return compile_scope_source(
            self.registry,
            scope_id="sample-scope",
            repo_root=self.repo_root,
        )

    def _manifest(self):
        compiled = self._compiled()
        rows = tuple(
            _Row(
                source_row_id=f"SRC-{index:03d}",
                source_path=compiled.baseline.selected_xhtml.relative_path,
                source_locator=candidate.canonical_xpath,
                bounded_source_text=candidate.bounded_source_text,
                source_context_class=candidate.source_context_class,
                candidate_id=candidate.candidate_id,
                requirement_codes=(
                    ("BSR 10",)
                    if "Имя" in candidate.bounded_source_text
                    else ("BSR 11",)
                    if "Телефон" in candidate.bounded_source_text
                    else ("BSR 20",)
                    if "Связанное" in candidate.bounded_source_text
                    else ()
                ),
            )
            for index, candidate in enumerate(compiled.baseline.candidates, 1)
        )
        def registered(relative_path: str, *, role: str = "") -> _Registered:
            path = self.package_root / relative_path
            return _Registered(
                path=path.relative_to(self.repo_root).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                role=role,
            )

        return compiled, _Manifest(
            scope_slug="sample-scope",
            source_row_extraction_spec_digest=compiled.extraction_spec.digest,
            source_row_baseline_digest=compiled.baseline.digest,
            source_row_candidate_count=compiled.baseline.candidate_count,
            sources=(
                registered("source/requirements.xhtml"),
            ),
            source_rows=rows,
            assertions=(_Assertion("ASSERT-001", ("BSR 10",)),),
            evidence_sources=(
                registered(
                    "source/requirements.docx",
                    role="semantic-source-of-truth",
                ),
                registered(
                    "source/requirements.pdf",
                    role="structural-visual-parity",
                ),
                registered(
                    "support/clarifications.md",
                    role="supporting-material",
                ),
            ),
            mockups=(registered("mockups/screen.png"),),
        )

    def test_registry_compiles_exact_rows_and_cross_reference(self) -> None:
        compiled = self._compiled()

        self.assertEqual(compiled.baseline.candidate_count, 4)
        self.assertEqual(
            [item.source_context_class for item in compiled.baseline.candidates],
            [
                "ancestor-and-section-preamble",
                "scope-local",
                "scope-local",
                "cross-referenced-constraints",
            ],
        )
        self.assertEqual(compiled.extraction_spec.digest, compiled.baseline.extraction_spec_sha256)

    def test_compilation_is_deterministic(self) -> None:
        first = self._compiled()
        second = self._compiled()
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_manifest_binds_to_exact_compiled_universe(self) -> None:
        compiled, manifest = self._manifest()

        validate_manifest_scope_binding(
            manifest,  # type: ignore[arg-type]
            compiled=compiled,
            repo_root=self.repo_root,
            package_root=self.package_root,
        )

    def test_manifest_with_foreign_requirement_code_is_rejected(self) -> None:
        compiled, manifest = self._manifest()
        manifest = replace(
            manifest,
            assertions=(_Assertion("ASSERT-001", ("BSR 999",)),),
        )

        with self.assertRaisesRegex(ScopeCompilationError, "outside the scope guard"):
            validate_manifest_scope_binding(
                manifest,  # type: ignore[arg-type]
                compiled=compiled,
                repo_root=self.repo_root,
                package_root=self.package_root,
            )

    def test_manifest_with_stale_candidate_text_is_rejected(self) -> None:
        compiled, manifest = self._manifest()
        rows = list(manifest.source_rows)
        rows[1] = replace(rows[1], bounded_source_text="Подменённый текст")
        manifest = replace(manifest, source_rows=tuple(rows))

        with self.assertRaisesRegex(ScopeCompilationError, "do not cover"):
            validate_manifest_scope_binding(
                manifest,  # type: ignore[arg-type]
                compiled=compiled,
                repo_root=self.repo_root,
                package_root=self.package_root,
            )

    def test_manifest_cannot_read_unregistered_support(self) -> None:
        compiled, manifest = self._manifest()
        unregistered = self.package_root / "support" / "unregistered.md"
        unregistered.write_text("unregistered", encoding="utf-8")
        manifest = replace(
            manifest,
            evidence_sources=manifest.evidence_sources
            + (
                _Registered(
                    unregistered.relative_to(self.repo_root).as_posix(),
                    hashlib.sha256(unregistered.read_bytes()).hexdigest(),
                    "supporting-material",
                ),
            ),
        )

        with self.assertRaisesRegex(ScopeCompilationError, "exact scope source set"):
            validate_manifest_scope_binding(
                manifest,  # type: ignore[arg-type]
                compiled=compiled,
                repo_root=self.repo_root,
                package_root=self.package_root,
            )

    def test_manifest_requires_every_declared_source_and_reference(self) -> None:
        compiled, manifest = self._manifest()
        cases = (
            replace(manifest, sources=()),
            replace(
                manifest,
                evidence_sources=manifest.evidence_sources[1:],
            ),
            replace(
                manifest,
                evidence_sources=(
                    manifest.evidence_sources[0],
                    manifest.evidence_sources[2],
                ),
            ),
            replace(
                manifest,
                evidence_sources=manifest.evidence_sources[:2],
            ),
            replace(manifest, mockups=()),
        )
        for mutated in cases:
            with self.subTest(missing=mutated), self.assertRaisesRegex(
                ScopeCompilationError,
                "exact scope source set",
            ):
                validate_manifest_scope_binding(
                    mutated,  # type: ignore[arg-type]
                    compiled=compiled,
                    repo_root=self.repo_root,
                    package_root=self.package_root,
                )

    def test_manifest_rejects_wrong_bucket_role_and_current_hash(self) -> None:
        compiled, manifest = self._manifest()
        docx = manifest.evidence_sources[0]
        wrong_bucket = replace(
            manifest,
            sources=manifest.sources + (replace(docx, role=""),),
            evidence_sources=manifest.evidence_sources[1:],
        )
        wrong_role = replace(
            manifest,
            evidence_sources=(
                replace(docx, role="supporting-material"),
                *manifest.evidence_sources[1:],
            ),
        )
        stale_hash = replace(
            manifest,
            evidence_sources=(
                replace(docx, sha256="0" * 64),
                *manifest.evidence_sources[1:],
            ),
        )
        mockup_in_evidence = replace(
            manifest,
            evidence_sources=manifest.evidence_sources
            + (replace(manifest.mockups[0], role="supporting-material"),),
            mockups=(),
        )

        for mutated in (wrong_bucket, wrong_role, stale_hash, mockup_in_evidence):
            with self.subTest(mutated=mutated), self.assertRaisesRegex(
                ScopeCompilationError,
                "bucket, role, or current SHA-256 mismatch",
            ):
                validate_manifest_scope_binding(
                    mutated,  # type: ignore[arg-type]
                    compiled=compiled,
                    repo_root=self.repo_root,
                    package_root=self.package_root,
                )

    def test_manifest_rejects_duplicate_or_cross_bucket_registration(self) -> None:
        compiled, manifest = self._manifest()
        duplicate = replace(
            manifest,
            sources=manifest.sources + manifest.sources,
        )
        cross_bucket = replace(
            manifest,
            evidence_sources=manifest.evidence_sources
            + (replace(manifest.sources[0], role="supporting-material"),),
        )

        for mutated in (duplicate, cross_bucket):
            with self.subTest(mutated=mutated), self.assertRaisesRegex(
                ScopeCompilationError,
                "more than once or in multiple buckets",
            ):
                validate_manifest_scope_binding(
                    mutated,  # type: ignore[arg-type]
                    compiled=compiled,
                    repo_root=self.repo_root,
                    package_root=self.package_root,
                )

    def test_manifest_binding_rehashes_declared_files_at_validation_time(self) -> None:
        compiled, manifest = self._manifest()
        (self.package_root / "support" / "clarifications.md").write_text(
            "changed after accepted manifest",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ScopeCompilationError,
            "current SHA-256 mismatch",
        ):
            validate_manifest_scope_binding(
                manifest,  # type: ignore[arg-type]
                compiled=compiled,
                repo_root=self.repo_root,
                package_root=self.package_root,
            )

    def test_clarification_reference_requires_approved_role_and_exact_hash(self) -> None:
        compiled, manifest = self._manifest()
        support = manifest.evidence_sources[2]
        clarification = _Clarification(
            clarification_id="CLR-001",
            evidence_source_path=support.path,
            evidence_source_sha256=support.sha256,
        )
        correctly_bound = replace(
            manifest,
            clarifications=(clarification,),
            evidence_sources=(
                *manifest.evidence_sources[:2],
                replace(support, role="approved-clarification"),
            ),
        )
        validate_manifest_scope_binding(
            correctly_bound,  # type: ignore[arg-type]
            compiled=compiled,
            repo_root=self.repo_root,
            package_root=self.package_root,
        )

        wrong_role = replace(manifest, clarifications=(clarification,))
        stale_clarification = replace(
            correctly_bound,
            clarifications=(
                replace(clarification, evidence_source_sha256="f" * 64),
            ),
        )
        for mutated in (wrong_role, stale_clarification):
            with self.subTest(mutated=mutated), self.assertRaises(
                ScopeCompilationError
            ):
                validate_manifest_scope_binding(
                    mutated,  # type: ignore[arg-type]
                    compiled=compiled,
                    repo_root=self.repo_root,
                    package_root=self.package_root,
                )


if __name__ == "__main__":
    unittest.main()
