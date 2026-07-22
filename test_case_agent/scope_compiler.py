from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from test_case_agent.review_cycle.source_assertions import SourceAssertionManifest
from test_case_agent.review_cycle.source_row_baseline import (
    EXTRACTION_SPEC_VERSION,
    XHTML_NAMESPACE,
    ContiguousSiblingRangeSelector,
    ExtractionRegion,
    SelectedXhtml,
    SourceRowBaseline,
    SourceRowCandidateMapping,
    SourceRowExtractionSpec,
    build_source_row_baseline,
    validate_candidate_coverage,
)
from test_case_agent.scope_registry import ResolvedScopeRegistry, ScopeDefinition


class ScopeCompilationError(ValueError):
    """A registry boundary cannot be compiled into exact source evidence."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ScopeCompilationError(
            f"registered source is outside repo_root: {path}"
        ) from exc
    return relative.as_posix()


@dataclass(frozen=True)
class CompiledScopeSource:
    schema_version: int
    registry_digest: str
    scope_id: str
    definition: ScopeDefinition
    extraction_spec: SourceRowExtractionSpec
    baseline: SourceRowBaseline

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "registry_digest": self.registry_digest,
            "scope_id": self.scope_id,
            "definition": self.definition.to_dict(),
            "extraction_spec": self.extraction_spec.to_dict(),
            "baseline": self.baseline.to_dict(),
        }


def compile_scope_source(
    registry: ResolvedScopeRegistry,
    *,
    scope_id: str,
    repo_root: Path,
) -> CompiledScopeSource:
    """Compile structural registry data through the existing XHTML extractor."""

    try:
        resolved = registry.get(scope_id)
    except KeyError as exc:
        raise ScopeCompilationError(f"unknown scope_id: {scope_id}") from exc
    definition = resolved.definition
    xhtml_path = resolved.source_set.xhtml
    selected = SelectedXhtml(
        relative_path=_repo_relative(xhtml_path, repo_root),
        sha256=_sha256_file(xhtml_path),
    )
    regions: list[ExtractionRegion] = []
    for row_range in definition.boundary.row_ranges:
        context_class = (
            "scope-local"
            if row_range.role == "testable"
            else "ancestor-and-section-preamble"
        )
        regions.append(
            ExtractionRegion(
                region_id=(
                    f"{definition.scope_id}-{row_range.role}-"
                    f"{row_range.start}-{row_range.end}"
                ),
                source_context_class=context_class,
                selector=ContiguousSiblingRangeSelector(
                    start_xpath=(
                        f"{definition.boundary.container_xpath}/*[{row_range.start}]"
                    ),
                    end_xpath=(
                        f"{definition.boundary.container_xpath}/*[{row_range.end}]"
                    ),
                    include_start=True,
                    include_end=True,
                ),
            )
        )
    for reference in definition.boundary.cross_references:
        regions.append(
            ExtractionRegion(
                region_id=f"{definition.scope_id}-xref-{reference.reference_id}",
                source_context_class="cross-referenced-constraints",
                selector=ContiguousSiblingRangeSelector(
                    start_xpath=reference.xpath,
                    end_xpath=reference.xpath,
                    include_start=True,
                    include_end=True,
                ),
            )
        )
    spec = SourceRowExtractionSpec.from_dict(
        SourceRowExtractionSpec(
            version=EXTRACTION_SPEC_VERSION,
            scope_slug=definition.scope_id,
            selected_xhtml=selected,
            namespaces=(("xhtml", XHTML_NAMESPACE),),
            regions=tuple(regions),
        ).to_dict()
    )
    baseline = build_source_row_baseline(repo_root=repo_root, spec=spec)
    return CompiledScopeSource(
        schema_version=1,
        registry_digest=registry.digest,
        scope_id=definition.scope_id,
        definition=definition,
        extraction_spec=spec,
        baseline=baseline,
    )


@dataclass(frozen=True)
class _ManifestRegistration:
    bucket: str
    role: str | None
    sha256: str


def _registered_manifest_files(
    manifest: SourceAssertionManifest,
) -> dict[str, _ManifestRegistration]:
    result: dict[str, _ManifestRegistration] = {}

    def add(path: str, registration: _ManifestRegistration) -> None:
        previous = result.get(path)
        if previous is not None:
            raise ScopeCompilationError(
                "manifest registers one path more than once or in multiple buckets: "
                f"{path} ({previous.bucket}, {registration.bucket})"
            )
        result[path] = registration

    for item in manifest.sources:
        add(item.path, _ManifestRegistration("sources", None, item.sha256))
    for item in manifest.evidence_sources:
        add(
            item.path,
            _ManifestRegistration("evidence_sources", item.role, item.sha256),
        )
    for item in manifest.mockups:
        add(item.path, _ManifestRegistration("mockups", None, item.sha256))
    return result


def _resolved_registered_file(
    *,
    package_root: Path,
    relative_path: str,
) -> Path:
    try:
        candidate = package_root.joinpath(*PurePosixPath(relative_path).parts).resolve(
            strict=True
        )
    except OSError as exc:
        raise ScopeCompilationError(
            f"registered package file is unavailable: {relative_path}: {exc}"
        ) from exc
    if not candidate.is_relative_to(package_root):
        raise ScopeCompilationError(
            f"registered package file escapes package_root: {relative_path}"
        )
    if not candidate.is_file():
        raise ScopeCompilationError(
            f"registered package path is not a file: {relative_path}"
        )
    return candidate


def _expected_manifest_files(
    manifest: SourceAssertionManifest,
    *,
    compiled: CompiledScopeSource,
    repo_root: Path,
    package_root: Path,
) -> dict[str, _ManifestRegistration]:
    clarification_paths = {
        item.evidence_source_path for item in manifest.clarifications
    }
    expected: dict[str, _ManifestRegistration] = {}

    def add(
        relative_path: str,
        *,
        bucket: str,
        role: str | None,
    ) -> None:
        path = _resolved_registered_file(
            package_root=package_root,
            relative_path=relative_path,
        )
        repo_relative = _repo_relative(path, repo_root)
        if repo_relative in expected:
            raise ScopeCompilationError(
                "scope registry binds one package file more than once: "
                f"{repo_relative}"
            )
        expected[repo_relative] = _ManifestRegistration(
            bucket=bucket,
            role=role,
            sha256=_sha256_file(path),
        )

    source_set = compiled.definition.source_set
    add(source_set.xhtml, bucket="sources", role=None)
    add(
        source_set.docx,
        bucket="evidence_sources",
        role="semantic-source-of-truth",
    )
    if source_set.pdf is not None:
        add(
            source_set.pdf,
            bucket="evidence_sources",
            role="structural-visual-parity",
        )
    for relative_path in compiled.definition.reference_paths:
        repo_relative = _repo_relative(
            _resolved_registered_file(
                package_root=package_root,
                relative_path=relative_path,
            ),
            repo_root,
        )
        is_mockup = (
            PurePosixPath(relative_path).parts[0].casefold() == "mockups"
        )
        if is_mockup:
            bucket = "mockups"
            role = None
        elif repo_relative in clarification_paths:
            bucket = "evidence_sources"
            role = "approved-clarification"
        else:
            bucket = "evidence_sources"
            role = "supporting-material"
        add(relative_path, bucket=bucket, role=role)
    return expected


def _validate_exact_manifest_file_set(
    manifest: SourceAssertionManifest,
    *,
    compiled: CompiledScopeSource,
    repo_root: Path,
    package_root: Path,
) -> None:
    actual = _registered_manifest_files(manifest)
    expected = _expected_manifest_files(
        manifest,
        compiled=compiled,
        repo_root=repo_root,
        package_root=package_root,
    )
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        raise ScopeCompilationError(
            "manifest file registry is not the exact scope source set: "
            f"missing={missing or 'none'}, extra={extra or 'none'}"
        )
    mismatches = [
        f"{path}: expected={expected[path]}, actual={actual[path]}"
        for path in sorted(expected)
        if actual[path] != expected[path]
    ]
    if mismatches:
        raise ScopeCompilationError(
            "manifest file bucket, role, or current SHA-256 mismatch: "
            + "; ".join(mismatches)
        )
    for clarification in manifest.clarifications:
        registration = actual.get(clarification.evidence_source_path)
        if registration is None or registration.bucket != "evidence_sources":
            raise ScopeCompilationError(
                "clarification evidence is not registered in evidence_sources: "
                f"{clarification.evidence_source_path}"
            )
        if registration.role != "approved-clarification":
            raise ScopeCompilationError(
                "clarification evidence has the wrong role: "
                f"{clarification.evidence_source_path}"
            )
        if clarification.evidence_source_sha256 != registration.sha256:
            raise ScopeCompilationError(
                "clarification evidence SHA-256 differs from its registered file: "
                f"{clarification.evidence_source_path}"
            )


def validate_manifest_scope_binding(
    manifest: SourceAssertionManifest,
    *,
    compiled: CompiledScopeSource,
    repo_root: Path,
    package_root: Path,
) -> None:
    """Bind a semantic manifest to the registry-generated exact source universe."""

    if manifest.scope_slug != compiled.scope_id:
        raise ScopeCompilationError(
            f"manifest scope mismatch: {manifest.scope_slug} != {compiled.scope_id}"
        )
    if manifest.source_row_extraction_spec_digest != compiled.extraction_spec.digest:
        raise ScopeCompilationError("manifest uses a different source extraction spec")
    if manifest.source_row_baseline_digest != compiled.baseline.digest:
        raise ScopeCompilationError("manifest uses a different source row baseline")
    if manifest.source_row_candidate_count != compiled.baseline.candidate_count:
        raise ScopeCompilationError("manifest source candidate count is stale")

    current_xhtml_sha256 = _sha256_file(
        _resolved_registered_file(
            package_root=package_root.resolve(),
            relative_path=compiled.definition.source_set.xhtml,
        )
    )
    if current_xhtml_sha256 != compiled.extraction_spec.selected_xhtml.sha256:
        raise ScopeCompilationError(
            "registry-selected XHTML changed after scope compilation"
        )
    _validate_exact_manifest_file_set(
        manifest,
        compiled=compiled,
        repo_root=repo_root,
        package_root=package_root.resolve(),
    )
    mappings = tuple(
        SourceRowCandidateMapping(
            source_row_id=row.source_row_id,
            source_path=row.source_path,
            source_locator=row.source_locator,
            bounded_source_text=row.bounded_source_text,
            source_context_class=row.source_context_class,
            candidate_id=row.candidate_id,
        )
        for row in manifest.source_rows
    )
    try:
        validate_candidate_coverage(
            baseline=compiled.baseline,
            source_row_mappings=mappings,
        )
    except ValueError as exc:
        raise ScopeCompilationError(
            f"manifest source rows do not cover the registry baseline: {exc}"
        ) from exc

    guard = compiled.definition.requirement_guard
    code_owners: list[tuple[str, str]] = []
    for row in manifest.source_rows:
        code_owners.extend((code, row.source_row_id) for code in row.requirement_codes)
    for assertion in manifest.assertions:
        code_owners.extend((code, assertion.assertion_id) for code in assertion.requirement_codes)
    for clarification in manifest.clarifications:
        code_owners.extend(
            (code, clarification.clarification_id)
            for code in clarification.requirement_codes
        )
    rejected = sorted(
        f"{code} ({owner})" for code, owner in code_owners if not guard.allows(code)
    )
    if rejected:
        raise ScopeCompilationError(
            "manifest contains requirement codes outside the scope guard: "
            + ", ".join(rejected)
        )
