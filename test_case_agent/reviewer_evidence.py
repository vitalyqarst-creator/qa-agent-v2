from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import CoverageGraph
from test_case_agent.review_cycle.prepared_package import (
    DICTIONARY_METADATA_NOT_DECLARED,
    EXTERNAL_FIXTURE_LIFECYCLE_POLICY,
    PreparedDictionaryFixtureProvenance,
    PreparedDictionaryValue,
    PreparedObligationSet,
    prepared_dictionary_value_set_sha256,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError
from test_case_agent.review_cycle.source_assertions import (
    SourceAssertionManifest,
    SourceAssertionReviewReceipt,
)
from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowBaselineValidationError,
    SourceRowBaseline,
    SourceRowExtractionSpec,
    resolve_xhtml_candidates_at_locators,
    resolve_xhtml_structural_contexts_at_locators,
    resolve_xhtml_table_cells_at_locators,
)
from test_case_agent.scope_compiler import CompiledScopeSource
from test_case_agent.scope_registry import ScopeDefinition
from test_case_agent.source_constraint_taxonomy import restricted_symbol_classes
from test_case_agent.source_parity import (
    SourceParityError,
    verify_bounded_source_parity,
)
from test_case_agent.stage_backend import SUPPORTED_IMAGE_SUFFIXES
from test_case_agent.test_design import TestCaseDesign


class ReviewerEvidenceError(ValueError):
    """Qualified reviewer evidence is incomplete, stale, or internally inconsistent."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise ReviewerEvidenceError(code, message)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        _fail("registered-file-unreadable", f"cannot read {path}: {exc}")
    return digest.hexdigest(), size


def _inside_repo(repo_root: Path, relative_path: str, *, label: str) -> Path:
    parsed = PurePosixPath(relative_path)
    if (
        not relative_path
        or parsed.is_absolute()
        or parsed.as_posix() != relative_path
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        _fail("invalid-relative-path", f"{label} is not a normalized relative path")
    candidate = repo_root.joinpath(*parsed.parts).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        _fail("registered-path-escape", f"{label} escapes repo_root: {relative_path}")
    if not candidate.is_file():
        _fail("registered-file-missing", f"{label} is missing: {relative_path}")
    return candidate


def _package_prefix(compiled_scope: CompiledScopeSource) -> PurePosixPath:
    selected = PurePosixPath(
        compiled_scope.baseline.selected_xhtml.relative_path
    )
    package_relative = PurePosixPath(compiled_scope.definition.source_set.xhtml)
    if len(selected.parts) < len(package_relative.parts) or (
        selected.parts[-len(package_relative.parts) :] != package_relative.parts
    ):
        _fail(
            "compiled-source-path-mismatch",
            "registry XHTML path is not the suffix of the compiled selected XHTML",
        )
    prefix_parts = selected.parts[: -len(package_relative.parts)]
    return PurePosixPath(*prefix_parts) if prefix_parts else PurePosixPath(".")


def _package_path(prefix: PurePosixPath, relative_path: str) -> str:
    value = PurePosixPath(relative_path)
    if str(prefix) == ".":
        return value.as_posix()
    return (prefix / value).as_posix()


@dataclass(frozen=True)
class _RegisteredFileSnapshot:
    role: str
    relative_path: str
    path: Path
    sha256: str
    size_bytes: int

    def verify(self) -> None:
        actual_sha256, actual_size = _file_digest(self.path)
        if actual_sha256 != self.sha256 or actual_size != self.size_bytes:
            _fail(
                "registered-file-drift",
                f"registered file changed: {self.relative_path}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class ReviewerEvidenceBasis:
    repo_root: Path
    compiled_scope: CompiledScopeSource
    manifest: SourceAssertionManifest
    source_review_receipt: SourceAssertionReviewReceipt
    obligation_set: PreparedObligationSet
    registered_files: tuple[_RegisteredFileSnapshot, ...]
    mockup_files: tuple[_RegisteredFileSnapshot, ...]
    basis_digest: str
    compiled_snapshot_sha256: str
    review_receipt_sha256: str

    def verify(self) -> None:
        if _digest(self.compiled_scope.to_dict()) != self.compiled_snapshot_sha256:
            _fail("compiled-scope-drift", "compiled scope changed after basis creation")
        if _digest(self.source_review_receipt.to_dict()) != self.review_receipt_sha256:
            _fail("source-review-receipt-drift", "source review receipt changed")
        if self.manifest.digest != self.source_review_receipt.manifest_digest:
            _fail("source-review-binding-drift", "source review no longer binds manifest")
        self.obligation_set.validate()
        for item in self.registered_files:
            item.verify()
        expected = _basis_payload(
            compiled_scope=self.compiled_scope,
            manifest=self.manifest,
            source_review_receipt=self.source_review_receipt,
            obligation_set=self.obligation_set,
            registered_files=self.registered_files,
        )
        if _digest(expected) != self.basis_digest:
            _fail("evidence-basis-drift", "reviewer evidence basis changed")

    def to_document(self) -> dict[str, Any]:
        """Serialize every qualified input needed for an independent rebuild.

        The document is deliberately separate from the reviewer request.  Promotion
        reloads these typed contracts, revalidates every registered file, and
        rebuilds the pack instead of trusting the pack's self-declared hashes.
        """

        self.verify()
        return {
            "schema_version": 1,
            "contract": "reviewer-evidence-basis-document-v1",
            "compiled_scope": self.compiled_scope.to_dict(),
            "source_manifest": self.manifest.to_dict(),
            "source_review_receipt": self.source_review_receipt.to_dict(),
            "obligation_set": self.obligation_set.to_dict(),
            "basis_sha256": self.basis_digest,
        }


@dataclass(frozen=True)
class ReviewerEvidencePack:
    _payload_json: str
    _mockup_files: tuple[_RegisteredFileSnapshot, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = json.loads(self._payload_json)
        if not isinstance(payload, dict):  # pragma: no cover - constructor invariant
            _fail("invalid-pack-payload", "reviewer evidence pack is not an object")
        return payload

    @property
    def digest(self) -> str:
        return hashlib.sha256(self._payload_json.encode("utf-8")).hexdigest()

    @property
    def image_paths(self) -> tuple[Path, ...]:
        for item in self._mockup_files:
            item.verify()
        return tuple(item.path for item in self._mockup_files)


def _basis_payload(
    *,
    compiled_scope: CompiledScopeSource,
    manifest: SourceAssertionManifest,
    source_review_receipt: SourceAssertionReviewReceipt,
    obligation_set: PreparedObligationSet,
    registered_files: Sequence[_RegisteredFileSnapshot],
) -> dict[str, Any]:
    return {
        "contract": "reviewer-evidence-basis-v2",
        "scope_id": compiled_scope.scope_id,
        "compiled_scope_sha256": _digest(compiled_scope.to_dict()),
        "source_manifest_digest": manifest.digest,
        "source_review_receipt_sha256": _digest(
            source_review_receipt.to_dict()
        ),
        "obligation_set_digest": obligation_set.digest,
        "registered_files": [
            item.to_dict()
            for item in sorted(registered_files, key=lambda value: value.relative_path)
        ],
    }


def _snapshot_registered_file(
    *,
    repo_root: Path,
    relative_path: str,
    role: str,
    expected_sha256: str,
) -> _RegisteredFileSnapshot:
    path = _inside_repo(repo_root, relative_path, label=role)
    actual_sha256, size_bytes = _file_digest(path)
    if actual_sha256 != expected_sha256:
        _fail(
            "registered-file-hash-mismatch",
            f"registered SHA-256 is stale for {relative_path}",
        )
    return _RegisteredFileSnapshot(
        role=role,
        relative_path=relative_path,
        path=path,
        sha256=actual_sha256,
        size_bytes=size_bytes,
    )


def _validate_candidate_universe(
    compiled_scope: CompiledScopeSource,
    manifest: SourceAssertionManifest,
) -> None:
    if manifest.scope_slug != compiled_scope.scope_id:
        _fail("scope-mismatch", "source manifest differs from compiled scope")
    if (
        manifest.source_row_extraction_spec_digest
        != compiled_scope.extraction_spec.digest
        or manifest.source_row_baseline_digest != compiled_scope.baseline.digest
        or manifest.source_row_candidate_count
        != compiled_scope.baseline.candidate_count
    ):
        _fail("source-baseline-mismatch", "manifest differs from compiled source baseline")
    candidates = {item.candidate_id: item for item in compiled_scope.baseline.candidates}
    mapped = [item for item in manifest.source_rows if item.candidate_id is not None]
    mapped_ids = [item.candidate_id for item in mapped]
    if len(mapped_ids) != len(set(mapped_ids)) or set(mapped_ids) != set(candidates):
        _fail(
            "source-row-completeness",
            "manifest must map every compiled baseline candidate exactly once",
        )
    selected_path = compiled_scope.baseline.selected_xhtml.relative_path
    for row in mapped:
        assert row.candidate_id is not None
        candidate = candidates[row.candidate_id]
        if (
            row.source_path != selected_path
            or row.source_locator != candidate.canonical_xpath
            or row.bounded_source_text != candidate.bounded_source_text
            or row.source_context_class != candidate.source_context_class
        ):
            _fail(
                "source-row-content-mismatch",
                f"source row differs from compiled candidate: {row.source_row_id}",
            )


def prepare_reviewer_evidence_basis(
    repo_root: Path,
    compiled_scope: CompiledScopeSource,
    manifest: SourceAssertionManifest,
    source_review_receipt: SourceAssertionReviewReceipt,
    obligation_set: PreparedObligationSet,
) -> ReviewerEvidenceBasis:
    repo_root = Path(repo_root).resolve()
    if not repo_root.is_dir():
        _fail("repo-root-missing", f"repo_root is missing: {repo_root}")
    if not isinstance(compiled_scope, CompiledScopeSource):
        _fail("invalid-compiled-scope", "compiled_scope has the wrong type")
    if not isinstance(manifest, SourceAssertionManifest):
        _fail("invalid-source-manifest", "manifest has the wrong type")
    if not isinstance(source_review_receipt, SourceAssertionReviewReceipt):
        _fail("invalid-source-review", "source_review_receipt has the wrong type")
    if not isinstance(obligation_set, PreparedObligationSet):
        _fail("invalid-obligation-set", "obligation_set has the wrong type")
    _validate_candidate_universe(compiled_scope, manifest)
    manifest.validate(repo_root)
    source_review_receipt.validate(manifest)
    if source_review_receipt.decision != "accepted":
        _fail("source-review-not-accepted", "reviewer evidence requires accepted source review")
    obligation_set.validate()

    prefix = _package_prefix(compiled_scope)
    expected_source_roles: dict[str, str] = {
        _package_path(prefix, compiled_scope.definition.source_set.xhtml): (
            "machine-readable-xhtml"
        ),
        _package_path(prefix, compiled_scope.definition.source_set.docx): (
            "source-of-truth-docx"
        ),
    }
    if compiled_scope.definition.source_set.pdf is not None:
        expected_source_roles[
            _package_path(prefix, compiled_scope.definition.source_set.pdf)
        ] = "structural-visual-parity-pdf"
    registered_sha256: dict[str, str] = {
        item.path: item.sha256 for item in manifest.sources
    }
    evidence_roles = {item.path: item.role for item in manifest.evidence_sources}
    registered_sha256.update(
        {item.path: item.sha256 for item in manifest.evidence_sources}
    )
    registered_sha256.update({item.path: item.sha256 for item in manifest.mockups})
    registered_sha256[manifest.coverage_gaps_artifact.path] = (
        manifest.coverage_gaps_artifact.sha256
    )
    for path, role in expected_source_roles.items():
        if path not in registered_sha256:
            _fail("required-source-unregistered", f"{role} is not registered: {path}")
    docx_path = _package_path(prefix, compiled_scope.definition.source_set.docx)
    if evidence_roles.get(docx_path) != "semantic-source-of-truth":
        _fail("docx-role-mismatch", "DOCX is not registered as semantic source of truth")
    if compiled_scope.definition.source_set.pdf is not None:
        pdf_path = _package_path(prefix, compiled_scope.definition.source_set.pdf)
        if evidence_roles.get(pdf_path) != "structural-visual-parity":
            _fail("pdf-role-mismatch", "PDF is not registered as structural/visual parity")

    expected_mockups = {
        _package_path(prefix, path)
        for path in compiled_scope.definition.reference_paths
        if PurePosixPath(path).suffix.casefold() in SUPPORTED_IMAGE_SUFFIXES
    }
    actual_mockups = {item.path for item in manifest.mockups}
    if expected_mockups != actual_mockups:
        _fail(
            "scope-mockup-set-mismatch",
            "registered mockups differ from the selected scope reference set: "
            f"missing={sorted(expected_mockups - actual_mockups)}, "
            f"extra={sorted(actual_mockups - expected_mockups)}",
        )

    roles: dict[str, str] = dict(expected_source_roles)
    for item in manifest.evidence_sources:
        roles.setdefault(item.path, item.role)
    for item in manifest.sources:
        roles.setdefault(item.path, "literal-text-source")
    for item in manifest.mockups:
        roles[item.path] = "scope-mockup"
    roles[manifest.coverage_gaps_artifact.path] = "scope-coverage-gaps"
    snapshots = tuple(
        _snapshot_registered_file(
            repo_root=repo_root,
            relative_path=path,
            role=roles[path],
            expected_sha256=sha256,
        )
        for path, sha256 in sorted(registered_sha256.items())
    )
    mockup_files = tuple(
        item for item in snapshots if item.role == "scope-mockup"
    )
    payload = _basis_payload(
        compiled_scope=compiled_scope,
        manifest=manifest,
        source_review_receipt=source_review_receipt,
        obligation_set=obligation_set,
        registered_files=snapshots,
    )
    result = ReviewerEvidenceBasis(
        repo_root=repo_root,
        compiled_scope=compiled_scope,
        manifest=manifest,
        source_review_receipt=source_review_receipt,
        obligation_set=obligation_set,
        registered_files=snapshots,
        mockup_files=mockup_files,
        basis_digest=_digest(payload),
        compiled_snapshot_sha256=_digest(compiled_scope.to_dict()),
        review_receipt_sha256=_digest(source_review_receipt.to_dict()),
    )
    _coverage_gap_evidence(result)
    return result


def load_reviewer_evidence_basis_document(
    repo_root: Path,
    payload: Mapping[str, Any],
) -> ReviewerEvidenceBasis:
    """Reload and requalify an exported evidence basis against current files."""

    expected_fields = {
        "schema_version",
        "contract",
        "compiled_scope",
        "source_manifest",
        "source_review_receipt",
        "obligation_set",
        "basis_sha256",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_fields:
        _fail(
            "invalid-evidence-basis-document",
            "evidence basis document fields differ from the closed contract",
        )
    if (
        payload.get("schema_version") != 1
        or payload.get("contract") != "reviewer-evidence-basis-document-v1"
        or not isinstance(payload.get("compiled_scope"), Mapping)
        or not isinstance(payload.get("source_manifest"), Mapping)
        or not isinstance(payload.get("source_review_receipt"), Mapping)
        or not isinstance(payload.get("obligation_set"), Mapping)
        or not isinstance(payload.get("basis_sha256"), str)
    ):
        _fail(
            "invalid-evidence-basis-document",
            "evidence basis document has invalid typed fields",
        )
    compiled_payload = payload["compiled_scope"]
    expected_compiled_fields = {
        "schema_version",
        "registry_digest",
        "scope_id",
        "definition",
        "extraction_spec",
        "baseline",
    }
    if set(compiled_payload) != expected_compiled_fields:
        _fail(
            "invalid-evidence-basis-document",
            "compiled scope fields differ from the closed contract",
        )
    try:
        compiled = CompiledScopeSource(
            schema_version=compiled_payload["schema_version"],
            registry_digest=compiled_payload["registry_digest"],
            scope_id=compiled_payload["scope_id"],
            definition=ScopeDefinition.from_dict(compiled_payload["definition"]),
            extraction_spec=SourceRowExtractionSpec.from_dict(
                compiled_payload["extraction_spec"]
            ),
            baseline=SourceRowBaseline.from_dict(compiled_payload["baseline"]),
        )
        manifest = SourceAssertionManifest.from_dict(payload["source_manifest"])
        receipt = SourceAssertionReviewReceipt.from_dict(
            payload["source_review_receipt"]
        )
        obligations = PreparedObligationSet.from_dict(payload["obligation_set"])
    except (KeyError, TypeError, ValueError, StageRuntimeError) as exc:
        _fail(
            "invalid-evidence-basis-document",
            f"cannot reload typed evidence basis: {exc}",
        )
    try:
        rebuilt = prepare_reviewer_evidence_basis(
            Path(repo_root),
            compiled,
            manifest,
            receipt,
            obligations,
        )
    except ReviewerEvidenceError:
        raise
    except (ValueError, RuntimeError) as exc:
        _fail(
            "evidence-basis-document-requalification-failed",
            f"reloaded evidence basis is not qualified: {exc}",
        )
    if rebuilt.basis_digest != payload["basis_sha256"]:
        _fail(
            "evidence-basis-document-drift",
            "reloaded evidence basis differs from the exported basis digest",
        )
    return rebuilt


def _literal_source_evidence(
    basis: ReviewerEvidenceBasis,
) -> list[dict[str, Any]]:
    baseline = basis.compiled_scope.baseline
    candidates = {item.candidate_id: item for item in baseline.candidates}
    rows_by_candidate = {
        item.candidate_id: item
        for item in basis.manifest.source_rows
        if item.candidate_id is not None
    }
    noncandidate_rows = sorted(
        (item for item in basis.manifest.source_rows if item.candidate_id is None),
        key=lambda item: item.source_row_id,
    )
    ordered_rows = [rows_by_candidate[item.candidate_id] for item in baseline.candidates]
    ordered_rows.extend(noncandidate_rows)
    assertions_by_row: dict[str, list[str]] = {}
    for assertion in basis.manifest.assertions:
        assertions_by_row.setdefault(assertion.source_row_id, []).append(
            assertion.assertion_id
        )
    file_hashes = {item.relative_path: item.sha256 for item in basis.registered_files}
    registered_paths = {
        item.relative_path: item.path for item in basis.registered_files
    }
    xhtml_rows_by_path: dict[str, list[Any]] = {}
    for row in ordered_rows:
        if PurePosixPath(row.source_path).suffix.casefold() == ".xhtml":
            xhtml_rows_by_path.setdefault(row.source_path, []).append(row)

    resolved_elements: dict[str, Any] = {}
    structural_contexts: dict[str, Any] = {}
    table_cells: dict[str, Any] = {}
    for source_path, source_rows in sorted(xhtml_rows_by_path.items()):
        xhtml_path = registered_paths.get(source_path)
        if xhtml_path is None:
            _fail(
                "source-row-file-unregistered",
                f"XHTML source row file is absent from the qualified source set: {source_path}",
            )
        locators = tuple(row.source_locator for row in source_rows)
        if len(locators) != len(set(locators)):
            _fail(
                "duplicate-xhtml-source-locator",
                f"literal source rows repeat an XHTML locator in {source_path}",
            )
        try:
            resolved = resolve_xhtml_candidates_at_locators(
                xhtml_path=xhtml_path,
                canonical_xpaths=locators,
            )
            contexts = resolve_xhtml_structural_contexts_at_locators(
                xhtml_path=xhtml_path,
                canonical_xpaths=locators,
            )
            row_locators = tuple(
                locator
                for locator in locators
                if resolved[locator].element_kind == "tr"
            )
            cells = (
                resolve_xhtml_table_cells_at_locators(
                    xhtml_path=xhtml_path,
                    canonical_xpaths=row_locators,
                )
                if row_locators
                else {}
            )
        except SourceRowBaselineValidationError as exc:
            _fail(
                "literal-xhtml-structure-invalid",
                f"cannot resolve literal XHTML structure in {source_path}: {exc}",
            )
        for row in source_rows:
            current = resolved[row.source_locator]
            if current.bounded_source_text != row.bounded_source_text:
                _fail(
                    "literal-xhtml-text-mismatch",
                    f"current XHTML text differs for {row.source_row_id}",
                )
            resolved_elements[row.source_row_id] = current
            structural_contexts[row.source_row_id] = contexts[row.source_locator]
            table_cells[row.source_row_id] = cells.get(row.source_locator, ())
    result: list[dict[str, Any]] = []
    for row in ordered_rows:
        candidate = candidates.get(row.candidate_id) if row.candidate_id else None
        source_file_sha256 = file_hashes.get(row.source_path)
        if source_file_sha256 is None:
            _fail(
                "source-row-file-unregistered",
                f"source row file is absent from the qualified source set: {row.source_path}",
            )
        resolved_element = resolved_elements.get(row.source_row_id)
        structural_context = structural_contexts.get(row.source_row_id)
        cells = table_cells.get(row.source_row_id, ())
        result.append(
            {
                "source_row_id": row.source_row_id,
                "candidate_id": row.candidate_id,
                "candidate_hash": candidate.candidate_hash if candidate else None,
                "bounded_source_text": row.bounded_source_text,
                "bounded_source_text_sha256": hashlib.sha256(
                    row.bounded_source_text.encode("utf-8")
                ).hexdigest(),
                "source_path": row.source_path,
                "source_file_sha256": source_file_sha256,
                "source_locator": row.source_locator,
                "region_id": candidate.region_id if candidate else None,
                "element_kind": (
                    resolved_element.element_kind
                    if resolved_element is not None
                    else None
                ),
                "source_context_class": row.source_context_class,
                "scope_disposition": row.scope_disposition,
                "requirement_codes": list(row.requirement_codes),
                "assertion_ids": sorted(assertions_by_row.get(row.source_row_id, [])),
                "source_constraint_projection": [
                    {
                        "source_binding": "exclusive-allowed-set",
                        "restriction_type": item.restriction_type,
                        "literal_anchor": item.literal_anchor,
                        "negative_class": item.negative_class,
                        "representative_invalid_value": (
                            item.representative_invalid_value
                        ),
                        "coverage_requirement": "distinct-negative-class-chain",
                        "ui_oracle_derivation": "forbidden-from-restriction-alone",
                    }
                    for item in restricted_symbol_classes(row.bounded_source_text)
                ],
                "section_path": (
                    list(structural_context.section_path)
                    if structural_context is not None
                    else []
                ),
                "section_path_status": (
                    "materialized-from-preceding-xhtml-headings"
                    if structural_context is not None
                    else "not-applicable-to-non-xhtml-source-row"
                ),
                "section_heading_evidence": [
                    {
                        "heading_evidence_id": (
                            "XHTML-HEADING-"
                            + hashlib.sha256(
                                "\u001f".join(
                                    (
                                        row.source_path,
                                        item.canonical_xpath,
                                        item.bounded_source_text,
                                    )
                                ).encode("utf-8")
                            ).hexdigest()[:24].upper()
                        ),
                        "level": item.level,
                        "source_path": row.source_path,
                        "source_file_sha256": source_file_sha256,
                        "canonical_xpath": item.canonical_xpath,
                        "bounded_source_text": item.bounded_source_text,
                        "bounded_source_text_sha256": hashlib.sha256(
                            item.bounded_source_text.encode("utf-8")
                        ).hexdigest(),
                    }
                    for item in (
                        structural_context.section_headings
                        if structural_context is not None
                        else ()
                    )
                ],
                "table_identity": (
                    structural_context.table_identity
                    if structural_context is not None
                    else None
                ),
                "table_ancestry": [
                    {
                        "element_kind": item.element_kind,
                        "canonical_xpath": item.canonical_xpath,
                    }
                    for item in (
                        structural_context.table_ancestry
                        if structural_context is not None
                        else ()
                    )
                ],
                "list_ancestry": [
                    {
                        "element_kind": item.element_kind,
                        "canonical_xpath": item.canonical_xpath,
                    }
                    for item in (
                        structural_context.list_ancestry
                        if structural_context is not None
                        else ()
                    )
                ],
                "row_identity": row.source_locator,
                "structured_cells": [
                    {
                        "physical_column_index": cell.physical_column_index,
                        "canonical_xpath": cell.canonical_xpath,
                        "element_kind": cell.element_kind,
                        "bounded_source_text": cell.bounded_source_text,
                        "bounded_source_text_sha256": hashlib.sha256(
                            cell.bounded_source_text.encode("utf-8")
                        ).hexdigest(),
                    }
                    for cell in cells
                ],
            }
        )
    if len(result) != len(basis.manifest.source_rows):
        _fail("source-evidence-count-mismatch", "not every manifest source row was emitted")
    return result


_DICTIONARY_METADATA_MARKER_RE = re.compile(
    r"(?i)\b(?:dictionary\s+version|effective[- ]date|"
    r"версия\s+справочника|дата\s+актуальности\s+справочника|"
    r"справочник\s+действует\s+с)\b"
)
_DICTIONARY_VERSION_RE = re.compile(
    r"(?i)(?:(?P<dictionary_id>DICT-[A-Za-z0-9._-]+)\s+)?"
    r"(?:dictionary\s+version|версия\s+справочника)\s*[:=]\s*"
    r"(?P<value>[A-Za-zА-Яа-яЁё0-9._-]+)"
)
_DICTIONARY_EFFECTIVE_DATE_RE = re.compile(
    r"(?i)(?:(?P<dictionary_id>DICT-[A-Za-z0-9._-]+)\s+)?"
    r"(?:effective[- ]date|дата\s+актуальности\s+справочника|"
    r"справочник\s+действует\s+с)\s*[:=]?\s*"
    r"(?P<value>\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})"
)


def _dictionary_metadata(
    *,
    dictionary_id: str,
    row_ids: Sequence[str],
    source_rows: Mapping[str, Any],
    dictionary_ids_by_row: Mapping[str, set[str]],
) -> tuple[str | None, str | None, str, list[dict[str, str]]]:
    values: dict[str, set[str]] = {"version": set(), "effective_date": set()}
    evidence: list[dict[str, str]] = []
    for row_id in row_ids:
        row = source_rows[row_id]
        text = row.bounded_source_text
        recognized_spans: set[tuple[int, int]] = set()
        for field, pattern in (
            ("version", _DICTIONARY_VERSION_RE),
            ("effective_date", _DICTIONARY_EFFECTIVE_DATE_RE),
        ):
            for match in pattern.finditer(text):
                recognized_spans.add(match.span())
                declared_id = match.group("dictionary_id")
                if declared_id is not None:
                    if declared_id.upper() != dictionary_id:
                        continue
                elif dictionary_ids_by_row.get(row_id) != {dictionary_id}:
                    _fail(
                        "dictionary-metadata-ambiguous",
                        f"{row_id} declares dictionary metadata without a unique dictionary binding",
                    )
                value = match.group("value")
                values[field].add(value)
                fragment = match.group(0)
                evidence.append(
                    {
                        "field": field,
                        "value": value,
                        "source_row_id": row_id,
                        "source_path": row.source_path,
                        "source_locator": row.source_locator,
                        "exact_source_fragment": fragment,
                        "exact_source_fragment_sha256": hashlib.sha256(
                            fragment.encode("utf-8")
                        ).hexdigest(),
                    }
                )
        markers = tuple(_DICTIONARY_METADATA_MARKER_RE.finditer(text))
        if any(
            not any(start <= marker.start() < end for start, end in recognized_spans)
            for marker in markers
        ):
            _fail(
                "dictionary-metadata-unstructured",
                f"{row_id} appears to declare dictionary metadata that cannot be materialized",
            )
    for field, field_values in values.items():
        if len(field_values) > 1:
            _fail(
                "dictionary-metadata-conflict",
                f"{dictionary_id} has conflicting {field} declarations",
            )
    version = next(iter(values["version"]), None)
    effective_date = next(iter(values["effective_date"]), None)
    if version is not None and effective_date is not None:
        status = "version-and-effective-date-materialized-from-qualified-source"
    elif version is not None or effective_date is not None:
        status = "partial-metadata-materialized-from-qualified-source"
    else:
        status = "version-and-effective-date-not-declared-in-qualified-contract"
    return version, effective_date, status, evidence


def _registered_fixture_file(
    basis: ReviewerEvidenceBasis,
    *,
    relative_path: str,
    expected_sha256: str,
    label: str,
) -> _RegisteredFileSnapshot:
    matches = tuple(
        item for item in basis.registered_files if item.relative_path == relative_path
    )
    if len(matches) != 1:
        _fail(
            "dictionary-fixture-evidence-unregistered",
            f"{label} must name exactly one registered file: {relative_path}",
        )
    result = matches[0]
    if result.role != "supporting-material":
        _fail(
            "dictionary-fixture-evidence-role-invalid",
            f"{label} must be registered as supporting-material: {relative_path}",
        )
    if result.sha256 != expected_sha256:
        _fail(
            "dictionary-fixture-evidence-hash-mismatch",
            f"{label} SHA-256 differs from the registered file: {relative_path}",
        )
    result.verify()
    return result


def _load_fixture_json(
    snapshot: _RegisteredFileSnapshot,
    *,
    label: str,
) -> Any:
    try:
        return json.loads(snapshot.path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(
            "dictionary-fixture-evidence-invalid-json",
            f"{label} is not valid UTF-8 JSON ({snapshot.relative_path}): {exc}",
        )


def _resolve_json_pointer(document: Any, locator: str, *, label: str) -> Any:
    prefix = "json-pointer:"
    if not locator.startswith(prefix):
        _fail(
            "dictionary-fixture-locator-invalid",
            f"{label} must use an RFC 6901 json-pointer: locator",
        )
    pointer = locator[len(prefix) :]
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        _fail(
            "dictionary-fixture-locator-invalid",
            f"{label} JSON pointer must be empty or start with '/': {locator}",
        )
    current = document
    for raw_token in pointer[1:].split("/"):
        if re.search(r"~(?:[^01]|$)", raw_token):
            _fail(
                "dictionary-fixture-locator-invalid",
                f"{label} contains an invalid JSON pointer escape: {locator}",
            )
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                _fail(
                    "dictionary-fixture-locator-unresolved",
                    f"{label} does not resolve in the registered source: {locator}",
                )
            current = current[token]
        elif isinstance(current, list):
            if re.fullmatch(r"0|[1-9][0-9]*", token) is None:
                _fail(
                    "dictionary-fixture-locator-unresolved",
                    f"{label} list token is invalid: {locator}",
                )
            index = int(token)
            if index >= len(current):
                _fail(
                    "dictionary-fixture-locator-unresolved",
                    f"{label} list index is out of range: {locator}",
                )
            current = current[index]
        else:
            _fail(
                "dictionary-fixture-locator-unresolved",
                f"{label} traverses a scalar value: {locator}",
            )
    return current


def _json_fixture_literals(value: Any) -> set[str]:
    """Return exact scalar and canonical structured literals in a JSON subtree."""

    result: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, str):
            result.add(item)
            return
        if item is None or isinstance(item, (bool, int, float)):
            result.add(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            return
        if isinstance(item, Mapping):
            result.add(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            for key, child in item.items():
                result.add(str(key))
                visit(child)
            return
        if isinstance(item, list):
            result.add(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            for child in item:
                visit(child)

    visit(value)
    return result


_EXTERNAL_REVALIDATION_TRIGGERS = {
    "linked-test-failure",
    "confirmed-provider-contract-change",
    "explicit-user-request",
}


def _resolve_receipt_snapshot_path(
    receipt_path: str,
    raw_snapshot_path: Any,
) -> tuple[str, ...]:
    if not isinstance(raw_snapshot_path, str) or not raw_snapshot_path:
        _fail(
            "dictionary-fixture-receipt-invalid",
            "external fixture receipt must declare response_snapshot",
        )
    parsed = PurePosixPath(raw_snapshot_path)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != raw_snapshot_path
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        _fail(
            "dictionary-fixture-receipt-invalid",
            "external fixture receipt response_snapshot must be a normalized "
            "relative POSIX path",
        )
    # Receipts in existing packages use both a sibling filename and a full
    # repository-relative path.  Both are unambiguous once compared with the
    # separately registered source snapshot.
    return tuple(
        dict.fromkeys(
            (
                parsed.as_posix(),
                (PurePosixPath(receipt_path).parent / parsed).as_posix(),
            )
        )
    )


def _validate_external_request(provider: str, request: Any) -> Mapping[str, Any]:
    if not isinstance(request, Mapping):
        _fail(
            "dictionary-fixture-request-invalid",
            "external fixture attestation must bind the verified request",
        )
    method = request.get("method")
    endpoint = request.get("endpoint")
    parameters = request.get("parameters")
    if (
        not isinstance(method, str)
        or not method
        or not isinstance(endpoint, str)
        or not endpoint.startswith("https://")
        or not isinstance(parameters, Mapping)
        or not parameters
    ):
        _fail(
            "dictionary-fixture-request-invalid",
            "external fixture request requires method, HTTPS endpoint, and parameters",
        )
    if provider.casefold() == "dadata":
        query = parameters.get("query")
        if (
            method != "POST"
            or not endpoint.startswith("https://suggestions.dadata.ru/")
            or not isinstance(query, str)
            or not query.strip()
        ):
            _fail(
                "dictionary-fixture-request-invalid",
                "DaData fixture requires POST, an official suggestions.dadata.ru "
                "endpoint, and a non-empty parameters.query",
            )
    return request


def _validate_external_expected_response(
    source_document: Any,
    expected_response: Any,
) -> Mapping[str, Any]:
    if not isinstance(source_document, Mapping) or not isinstance(
        expected_response, Mapping
    ):
        _fail(
            "dictionary-fixture-expected-response-invalid",
            "external fixture requires a structured response snapshot and expectation",
        )
    suggestions = source_document.get("suggestions")
    outcome = expected_response.get("outcome")
    if not isinstance(suggestions, list) or outcome not in {
        "suggestions-found",
        "suggestions-empty",
    }:
        _fail(
            "dictionary-fixture-expected-response-invalid",
            "external fixture expectation must classify the suggestions outcome",
        )
    if outcome == "suggestions-empty":
        if suggestions != [] or expected_response.get("exact_suggestion") not in {
            None,
            "not_applicable",
        }:
            _fail(
                "dictionary-fixture-expected-response-mismatch",
                "external empty-result fixture differs from its response snapshot",
            )
        return expected_response
    exact_suggestion = expected_response.get("exact_suggestion")
    exact_components = expected_response.get("exact_components", {})
    if (
        not isinstance(exact_suggestion, str)
        or not exact_suggestion
        or not isinstance(exact_components, Mapping)
    ):
        _fail(
            "dictionary-fixture-expected-response-invalid",
            "suggestions-found requires exact_suggestion and exact_components",
        )
    matching = [
        item
        for item in suggestions
        if isinstance(item, Mapping) and item.get("value") == exact_suggestion
    ]
    if not matching:
        _fail(
            "dictionary-fixture-expected-response-mismatch",
            "expected external suggestion is absent from the response snapshot",
        )
    if exact_components and not any(
        isinstance(item.get("data"), Mapping)
        and all(item["data"].get(key) == value for key, value in exact_components.items())
        for item in matching
    ):
        _fail(
            "dictionary-fixture-expected-response-mismatch",
            "expected external components differ from the response snapshot",
        )
    return expected_response


def _validate_upstream_external_receipt(
    *,
    source: _RegisteredFileSnapshot,
    upstream: _RegisteredFileSnapshot,
    document: Any,
    fixture_id: str,
    provider: str,
    request: Mapping[str, Any],
    expected_response: Mapping[str, Any],
) -> tuple[str, int]:
    if not isinstance(document, Mapping):
        _fail(
            "dictionary-fixture-upstream-receipt-invalid",
            "upstream provider receipt must be a JSON object",
        )
    if (
        document.get("status") != "verified"
        or document.get("fixture_id") != fixture_id
        or not isinstance(document.get("provider"), str)
        or document["provider"].casefold() != provider.casefold()
        or document.get("request") != request
        or document.get("response_sha256") != source.sha256
    ):
        _fail(
            "dictionary-fixture-upstream-receipt-mismatch",
            "upstream provider receipt differs from the normalized attestation",
        )
    if "expected_response" in document and document.get("expected_response") != expected_response:
        _fail(
            "dictionary-fixture-upstream-receipt-mismatch",
            "upstream expected response differs from the normalized attestation",
        )
    if source.relative_path not in _resolve_receipt_snapshot_path(
        upstream.relative_path,
        document.get("response_snapshot"),
    ):
        _fail(
            "dictionary-fixture-snapshot-path-mismatch",
            "upstream provider receipt points to a different response snapshot",
        )
    verification = document.get("verification")
    attempts = verification.get("attempts") if isinstance(verification, Mapping) else None
    if not isinstance(attempts, list) or not attempts:
        _fail(
            "dictionary-fixture-upstream-receipt-invalid",
            "upstream provider receipt must contain verified attempts",
        )
    if verification.get("attempt_count") != len(attempts):
        _fail(
            "dictionary-fixture-upstream-receipt-invalid",
            "upstream receipt attempt_count differs from its attempts",
        )
    outcome = expected_response["outcome"]
    required_attempt_checks = (
        ("exact_empty_suggestions",)
        if outcome == "suggestions-empty"
        else (
            "exact_suggestion_matched",
            *(("exact_components_matched",) if expected_response.get("exact_components") else ()),
        )
    )
    required_aggregate_checks = tuple(
        f"all_{name}" for name in required_attempt_checks
    )
    if verification.get("all_http_200") is not True or any(
        verification.get(name) is not True for name in required_aggregate_checks
    ):
        _fail(
            "dictionary-fixture-upstream-receipt-invalid",
            "upstream receipt lacks the expected named aggregate checks",
        )
    normalized_attempts: list[tuple[int, str]] = []
    for index, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, Mapping):
            _fail(
                "dictionary-fixture-upstream-receipt-invalid",
                f"upstream provider attempt {index} must be an object",
            )
        number = attempt.get("attempt")
        checked_at = attempt.get("checked_at_utc")
        if (
            type(number) is not int
            or number < 1
            or not isinstance(checked_at, str)
            or re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
                checked_at,
            )
            is None
            or attempt.get("http_status") != 200
            or attempt.get("response_sha256") != source.sha256
            or any(attempt.get(name) is not True for name in required_attempt_checks)
        ):
            _fail(
                "dictionary-fixture-upstream-attempt-invalid",
                f"upstream provider attempt {index} lacks exact named checks",
            )
        normalized_attempts.append((number, checked_at))
    if sorted(number for number, _ in normalized_attempts) != list(
        range(1, len(attempts) + 1)
    ):
        _fail(
            "dictionary-fixture-upstream-attempt-invalid",
            "upstream provider attempt numbers must be unique and contiguous",
        )
    return max(normalized_attempts)[1], len(attempts)


def _validate_external_fixture_receipt(
    *,
    basis: ReviewerEvidenceBasis,
    provenance: PreparedDictionaryFixtureProvenance,
    source: _RegisteredFileSnapshot,
    source_document: Any,
    receipt: _RegisteredFileSnapshot,
    receipt_document: Any,
) -> tuple[dict[str, Any], set[str]]:
    if not isinstance(receipt_document, Mapping):
        _fail(
            "dictionary-fixture-receipt-invalid",
            "external fixture verification receipt must be a JSON object",
        )
    provider = receipt_document.get("provider")
    if (
        not isinstance(provider, str)
        or not isinstance(provenance.provider, str)
        or provider.casefold() != provenance.provider.casefold()
    ):
        _fail(
            "dictionary-fixture-provider-mismatch",
            "external fixture provider differs from its verification receipt",
        )
    if str(receipt_document.get("schema_version")) != provenance.version:
        _fail(
            "dictionary-fixture-version-mismatch",
            "external fixture receipt schema version differs from provenance",
        )
    request = _validate_external_request(provider, receipt_document.get("request"))
    raw_expected_response = receipt_document.get("expected_response")
    if raw_expected_response is None and (
        receipt_document.get("evidence_kind") == "verified-live-negative-response"
    ):
        raw_expected_response = {
            "outcome": "suggestions-empty",
            "exact_suggestion": "not_applicable",
            "exact_components": {},
        }
    expected_response = _validate_external_expected_response(
        source_document,
        raw_expected_response,
    )
    latest_checked_at, attempt_count = _validate_upstream_external_receipt(
        source=source,
        upstream=receipt,
        document=receipt_document,
        fixture_id=provenance.fixture_id,
        provider=provider,
        request=request,
        expected_response=expected_response,
    )
    if (
        provenance.verified_at != latest_checked_at
        or provenance.effective_date != latest_checked_at[:10]
    ):
        _fail(
            "dictionary-fixture-verification-time-mismatch",
            "external fixture provenance differs from verified provider evidence",
        )
    assert provenance.lifecycle_source_path is not None
    assert provenance.lifecycle_source_sha256 is not None
    assert provenance.lifecycle_source_locator is not None
    lifecycle_source = _registered_fixture_file(
        basis,
        relative_path=provenance.lifecycle_source_path,
        expected_sha256=provenance.lifecycle_source_sha256,
        label=f"{provenance.dictionary_id} fixture lifecycle catalog",
    )
    try:
        lifecycle_text = lifecycle_source.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(
            "dictionary-fixture-lifecycle-invalid",
            f"cannot read registered fixture lifecycle catalog: {exc}",
        )
    locator_prefix = "markdown-table-row:"
    located_fixture_id = provenance.lifecycle_source_locator.removeprefix(
        locator_prefix
    )
    if located_fixture_id != provenance.fixture_id:
        _fail(
            "dictionary-fixture-identity-mismatch",
            "lifecycle catalog locator names a different fixture",
        )
    matching_rows = []
    for line in lifecycle_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if cells and cells[0] == provenance.fixture_id:
            matching_rows.append(stripped)
    if len(matching_rows) != 1:
        _fail(
            "dictionary-fixture-lifecycle-invalid",
            "lifecycle catalog must contain exactly one fixture row",
        )
    lifecycle_row = matching_rows[0]
    catalog_parent = PurePosixPath(lifecycle_source.relative_path).parent

    def relative_to_catalog(path: str) -> str:
        parsed = PurePosixPath(path)
        try:
            return parsed.relative_to(catalog_parent).as_posix()
        except ValueError:
            return path

    query = request["parameters"].get("query")
    exact_suggestion = expected_response.get("exact_suggestion")
    if (
        provenance.lifecycle_policy != EXTERNAL_FIXTURE_LIFECYCLE_POLICY
        or EXTERNAL_FIXTURE_LIFECYCLE_POLICY not in lifecycle_row
        or "verified-live-response" not in lifecycle_row
        or latest_checked_at not in lifecycle_row
        or source.sha256 not in lifecycle_row
        or relative_to_catalog(source.relative_path) not in lifecycle_row
        or relative_to_catalog(receipt.relative_path) not in lifecycle_row
        or (isinstance(query, str) and query not in lifecycle_row)
        or (
            isinstance(exact_suggestion, str)
            and exact_suggestion != "not_applicable"
            and exact_suggestion not in lifecycle_row
        )
    ):
        _fail(
            "dictionary-fixture-lifecycle-invalid",
            "registered fixture catalog row does not bind lifecycle, response, "
            "receipt, query, and expected suggestion",
        )
    response_binding = {
        "path": source.relative_path,
        "sha256": source.sha256,
        "locator": provenance.source_locator,
    }
    receipt_binding = {
        "path": receipt.relative_path,
        "sha256": receipt.sha256,
        "locator": provenance.verification_receipt_locator,
    }
    lifecycle_binding = {
        "path": lifecycle_source.relative_path,
        "sha256": lifecycle_source.sha256,
        "locator": provenance.lifecycle_source_locator,
        "exact_row_sha256": hashlib.sha256(
            lifecycle_row.encode("utf-8")
        ).hexdigest(),
    }
    return (
        {
            "status": "verified-once",
            "provider": provider,
            "verified_at": latest_checked_at,
            "attempt_count": attempt_count,
            "request": request,
            "request_sha256": _digest(request),
            "expected_response": expected_response,
            "expected_response_sha256": _digest(expected_response),
            "response_snapshot": response_binding,
            "verification_receipt": receipt_binding,
            "lifecycle_catalog": lifecycle_binding,
            "routine_live_revalidation": "prohibited",
            "revalidation_triggers": sorted(_EXTERNAL_REVALIDATION_TRIGGERS),
        },
        _json_fixture_literals(receipt_document) | _json_fixture_literals(expected_response),
    )


def _validated_fixture_provenance(
    basis: ReviewerEvidenceBasis,
    *,
    dictionary_id: str,
    fixture_values: Sequence[PreparedDictionaryValue],
    provenance: PreparedDictionaryFixtureProvenance | None,
    external_dynamic: bool,
) -> dict[str, Any] | None:
    if not fixture_values:
        if provenance is not None:
            _fail(
                "dictionary-fixture-provenance-without-values",
                f"{dictionary_id} declares fixture provenance without fixture values",
            )
        return None
    if provenance is None:
        _fail(
            "dictionary-fixture-provenance-missing",
            f"{dictionary_id} fixture values are not bound to registered evidence",
        )
    try:
        provenance.validate()
    except StageRuntimeError as exc:
        _fail(
            "dictionary-fixture-provenance-invalid",
            f"{dictionary_id} fixture provenance is invalid: {exc}",
        )
    expected_value_set_sha256 = prepared_dictionary_value_set_sha256(fixture_values)
    if provenance.dictionary_id != dictionary_id:
        _fail(
            "dictionary-fixture-identity-mismatch",
            f"{dictionary_id} differs from its provenance dictionary identity",
        )
    if provenance.value_set_sha256 != expected_value_set_sha256:
        _fail(
            "dictionary-fixture-value-set-drift",
            f"{dictionary_id} fixture values differ from their provenance binding",
        )
    if external_dynamic != (
        provenance.evidence_kind == "external-dynamic-fixture"
    ):
        _fail(
            "dictionary-fixture-provenance-kind-mismatch",
            f"{dictionary_id} dictionary type differs from its fixture evidence kind",
        )
    source = _registered_fixture_file(
        basis,
        relative_path=provenance.source_path,
        expected_sha256=provenance.source_sha256,
        label=f"{dictionary_id} fixture source",
    )
    source_document = _load_fixture_json(source, label=f"{dictionary_id} fixture source")
    source_subtree = _resolve_json_pointer(
        source_document,
        provenance.source_locator,
        label=f"{dictionary_id} fixture source_locator",
    )
    evidence_literals = _json_fixture_literals(source_subtree)
    receipt_payload: dict[str, Any] | None = None
    receipt_literals: set[str] = set()
    if external_dynamic:
        assert provenance.verification_receipt_path is not None
        assert provenance.verification_receipt_sha256 is not None
        receipt = _registered_fixture_file(
            basis,
            relative_path=provenance.verification_receipt_path,
            expected_sha256=provenance.verification_receipt_sha256,
            label=f"{dictionary_id} verification receipt",
        )
        if receipt.relative_path == source.relative_path:
            _fail(
                "dictionary-fixture-receipt-not-independent",
                f"{dictionary_id} response snapshot and verification receipt must differ",
            )
        receipt_document = _load_fixture_json(
            receipt,
            label=f"{dictionary_id} verification receipt",
        )
        assert provenance.verification_receipt_locator is not None
        receipt_document = _resolve_json_pointer(
            receipt_document,
            provenance.verification_receipt_locator,
            label=f"{dictionary_id} verification_receipt_locator",
        )
        receipt_payload, upstream_literals = _validate_external_fixture_receipt(
            basis=basis,
            provenance=provenance,
            source=source,
            source_document=source_document,
            receipt=receipt,
            receipt_document=receipt_document,
        )
        receipt_literals = (
            _json_fixture_literals(receipt_document) | upstream_literals
        )
    elif not isinstance(source_document, Mapping):
        _fail(
            "dictionary-fixture-evidence-invalid-json",
            f"{dictionary_id} registered fixture source must be a JSON object",
        )
    elif (
        source_document.get("dictionary_id") != dictionary_id
        or source_document.get("fixture_id") != provenance.fixture_id
    ):
        _fail(
            "dictionary-fixture-identity-mismatch",
            f"{dictionary_id} registered fixture source names a different identity",
        )
    elif (
        source_document.get("fixture_value_set_sha256")
        != expected_value_set_sha256
    ):
        _fail(
            "dictionary-fixture-value-set-drift",
            f"{dictionary_id} registered fixture source does not bind the exact "
            "prepared value set",
        )
    missing_values = sorted(
        {
            item.value
            for item in fixture_values
            if item.value not in evidence_literals | receipt_literals
        }
    )
    if missing_values:
        _fail(
            "dictionary-fixture-value-unattested",
            f"{dictionary_id} has values absent from its registered evidence: "
            + ", ".join(missing_values),
        )
    payload = provenance.to_dict()
    payload["registration_status"] = "registered-and-hash-verified"
    payload["attested_value_count"] = len(fixture_values)
    payload["verification"] = receipt_payload or {
        "status": "registered-static-fixture",
        "routine_live_revalidation": "not-applicable",
    }
    payload["content_sha256"] = _digest(payload)
    return payload


def _qualified_closed_fixture_subset_provenance(
    basis: ReviewerEvidenceBasis,
    *,
    dictionary_id: str,
    required_values: Sequence[PreparedDictionaryValue],
    fixture_values: Sequence[PreparedDictionaryValue],
    source_row_ids: Sequence[str],
) -> dict[str, Any]:
    """Bind bounded branch fixtures to a complete qualified closed dictionary."""

    required_identities = {
        (item.hierarchy_path, item.value_kind, item.value)
        for item in required_values
    }
    fixture_identities = {
        (item.hierarchy_path, item.value_kind, item.value)
        for item in fixture_values
    }
    if not required_identities or not fixture_identities.issubset(required_identities):
        _fail(
            "dictionary-fixture-not-qualified-subset",
            f"{dictionary_id} branch fixtures are not a subset of its complete "
            "qualified value set",
        )
    rows_by_id = {item.source_row_id: item for item in basis.manifest.source_rows}
    registered = {
        item.relative_path: item for item in basis.registered_files
    }
    def contains_exact_value(text: str, value: str) -> bool:
        return (
            re.search(
                rf"(?<!\w){re.escape(value)}(?!\w)",
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    qualified_source_rows = [
        rows_by_id[row_id]
        for row_id in dict.fromkeys(source_row_ids)
        if row_id in rows_by_id
    ]
    value_bindings: list[dict[str, Any]] = []
    for value in sorted(required_values, key=lambda item: (
        item.hierarchy_path,
        item.value_kind,
        item.value,
    )):
        matching_rows = [
            row
            for row in qualified_source_rows
            if contains_exact_value(row.bounded_source_text, value.value)
        ]
        if not matching_rows:
            _fail(
                "dictionary-qualified-value-unattested",
                f"{dictionary_id} qualified source rows do not attest required "
                f"value {value.value!r}",
            )
        value_bindings.append(
            {
                **value.to_dict(),
                "source_rows": [
                    {
                        "source_row_id": row.source_row_id,
                        "source_path": row.source_path,
                        "source_locator": row.source_locator,
                        "source_file_sha256": registered[row.source_path].sha256,
                        "bounded_source_text_sha256": hashlib.sha256(
                            row.bounded_source_text.encode("utf-8")
                        ).hexdigest(),
                    }
                    for row in matching_rows
                ],
            }
        )
    payload: dict[str, Any] = {
        "contract": "qualified-closed-dictionary-fixture-subset-v1",
        "evidence_kind": "qualified-closed-dictionary-subset",
        "dictionary_id": dictionary_id,
        "version": DICTIONARY_METADATA_NOT_DECLARED,
        "effective_date": DICTIONARY_METADATA_NOT_DECLARED,
        "fixture_value_set_sha256": prepared_dictionary_value_set_sha256(
            fixture_values
        ),
        "qualified_complete_value_set_sha256": (
            prepared_dictionary_value_set_sha256(required_values)
        ),
        "attested_fixture_value_count": len(fixture_values),
        "qualified_complete_value_count": len(required_values),
        "source_value_bindings": value_bindings,
        "registration_status": "qualified-source-membership-verified",
        "verification": {
            "status": "closed-dictionary-subset",
            "routine_live_revalidation": "not-applicable",
        },
    }
    payload["content_sha256"] = _digest(payload)
    return payload


def _dictionary_slice(
    basis: ReviewerEvidenceBasis,
    graph: CoverageGraph,
) -> list[dict[str, Any]]:
    relevant_obligations = {item.obligation_id for item in graph.obligations}
    graph_obligations = {
        item.obligation_id: item for item in graph.obligations
    }
    graph_properties = {item.property_id: item for item in graph.properties}
    prepared = {
        item.obligation_id: item for item in basis.obligation_set.obligations
    }
    unknown = relevant_obligations - set(prepared)
    if unknown:
        _fail(
            "graph-obligation-unregistered",
            "graph references obligations absent from the qualified set: "
            + ", ".join(sorted(unknown)),
        )
    source_rows = {item.source_row_id: item for item in basis.manifest.source_rows}
    assertions = basis.manifest.assertions
    case_by_obligation: dict[str, list[tuple[str, str]]] = {}
    for case in graph.cases:
        for obligation_id in case.obligation_ids:
            case_by_obligation.setdefault(obligation_id, []).append(
                (case.case_key, case.tc_id)
            )
    aggregated: dict[str, dict[str, Any]] = {}
    mode_value_sets: dict[tuple[str, str], set[tuple[tuple[str, ...], str, str]]] = {}
    for obligation_id in sorted(relevant_obligations):
        obligation = prepared[obligation_id]
        assertion_rows = {
            assertion.source_row_id
            for assertion in assertions
            if obligation_id in assertion.obligation_ids
        }
        assertion_rows.update(
            ref for ref in obligation.source_refs if ref in source_rows
        )
        for requirement in obligation.dictionary_requirements:
            entry = aggregated.setdefault(
                requirement.dictionary_id,
                {
                    "dictionary_id": requirement.dictionary_id,
                    "coverage_modes": set(),
                    "required_values": {},
                    "fixture_values": {},
                    "fixture_provenance": None,
                    "fixture_provenance_missing": False,
                    "source_row_ids": set(),
                    "obligation_ids": set(),
                    "case_keys": set(),
                    "tc_ids": set(),
                },
            )
            entry["coverage_modes"].add(requirement.coverage_mode)
            entry["source_row_ids"].update(assertion_rows)
            entry["obligation_ids"].add(obligation_id)
            for case_key, tc_id in case_by_obligation.get(obligation_id, []):
                entry["case_keys"].add(case_key)
                entry["tc_ids"].add(tc_id)
            current_values = {
                (item.hierarchy_path, item.value_kind, item.value)
                for item in requirement.required_values
            }
            mode_key = (requirement.dictionary_id, requirement.coverage_mode)
            if current_values:
                previous = mode_value_sets.get(mode_key)
                if previous is not None and previous != current_values:
                    _fail(
                        "dictionary-definition-conflict",
                        f"{requirement.dictionary_id} has conflicting complete value sets",
                    )
                mode_value_sets[mode_key] = current_values
            for item in requirement.required_values:
                entry["required_values"][(
                    item.hierarchy_path,
                    item.value_kind,
                    item.value,
                )] = item.to_dict()
            for item in requirement.fixture_values:
                entry["fixture_values"][(
                    item.hierarchy_path,
                    item.value_kind,
                    item.value,
                )] = item.to_dict()
            if requirement.fixture_values:
                if requirement.fixture_provenance is None:
                    entry["fixture_provenance_missing"] = True
                existing_provenance = entry["fixture_provenance"]
                if (
                    existing_provenance is not None
                    and existing_provenance != requirement.fixture_provenance
                ):
                    _fail(
                        "dictionary-fixture-provenance-conflict",
                        f"{requirement.dictionary_id} has conflicting fixture provenance",
                    )
                entry["fixture_provenance"] = requirement.fixture_provenance
    dictionary_ids_by_row: dict[str, set[str]] = {}
    for aggregated_dictionary_id, raw in aggregated.items():
        for row_id in raw["source_row_ids"]:
            dictionary_ids_by_row.setdefault(row_id, set()).add(
                aggregated_dictionary_id
            )
    result: list[dict[str, Any]] = []
    for dictionary_id in sorted(aggregated):
        raw = aggregated[dictionary_id]
        modes = sorted(raw["coverage_modes"])
        closed = any(mode != "reference-only" for mode in modes)
        row_ids = sorted(raw["source_row_ids"])
        locators = [
            {
                "source_row_id": row_id,
                "source_path": source_rows[row_id].source_path,
                "source_locator": source_rows[row_id].source_locator,
                "source_file_sha256": next(
                    item.sha256
                    for item in basis.registered_files
                    if item.relative_path == source_rows[row_id].source_path
                ),
                "bounded_source_text_sha256": hashlib.sha256(
                    source_rows[row_id].bounded_source_text.encode("utf-8")
                ).hexdigest(),
            }
            for row_id in row_ids
        ]
        version, effective_date, metadata_status, metadata_evidence = (
            _dictionary_metadata(
                dictionary_id=dictionary_id,
                row_ids=row_ids,
                source_rows=source_rows,
                dictionary_ids_by_row=dictionary_ids_by_row,
            )
        )
        type_evidence: list[dict[str, Any]] = []
        reference_contracts: set[str] = set()
        for obligation_id in sorted(raw["obligation_ids"]):
            obligation = prepared[obligation_id]
            obligation_modes = sorted(
                requirement.coverage_mode
                for requirement in obligation.dictionary_requirements
                if requirement.dictionary_id == dictionary_id
            )
            dependency_refs = {
                ref for ref in obligation.source_refs if ref.startswith("DEP-")
            }
            explicit_declarations: dict[str, set[str]] = {}
            for match in re.finditer(
                r"(?i)\bexternal-dynamic\s+dictionary\s+"
                r"(?P<dictionary_id>DICT-[A-Za-z0-9._-]+)\s+dependency:\s*"
                r"(?P<dependency_id>DEP-[A-Za-z0-9._-]+)\b",
                obligation.notes,
            ):
                explicit_declarations.setdefault(
                    match.group("dictionary_id").upper(), set()
                ).add(match.group("dependency_id").upper())
            generic_declarations = {
                item.upper()
                for item in re.findall(
                    r"(?i)\bexternal-dynamic\s+dictionary\s+dependency:\s*"
                    r"(DEP-[A-Za-z0-9._-]+)\b",
                    obligation.notes,
                )
            }
            reference_only_ids = {
                requirement.dictionary_id
                for requirement in obligation.dictionary_requirements
                if requirement.coverage_mode == "reference-only"
            }
            if dictionary_id in explicit_declarations:
                declared_dependencies = explicit_declarations[dictionary_id]
                dependency_binding = "dictionary-specific"
            elif len(reference_only_ids) == 1 and dictionary_id in reference_only_ids:
                declared_dependencies = generic_declarations
                dependency_binding = (
                    "generic-unambiguous" if generic_declarations else "none"
                )
            else:
                declared_dependencies = set()
                dependency_binding = (
                    "generic-ambiguous" if generic_declarations else "none"
                )
            if any(mode != "reference-only" for mode in obligation_modes):
                contract = "closed-qualified-value-set"
            elif (
                declared_dependencies
                and declared_dependencies.issubset(dependency_refs)
            ):
                contract = "external-dynamic-dependency"
            else:
                contract = "reference-only-type-not-declared"
            reference_contracts.add(contract)
            type_evidence.append(
                {
                    "obligation_id": obligation_id,
                    "coverage_modes": obligation_modes,
                    "contract": contract,
                    "dependency_binding": dependency_binding,
                    "dependency_ids": sorted(declared_dependencies),
                }
            )
        if closed:
            dictionary_type = "closed"
        elif reference_contracts == {"external-dynamic-dependency"}:
            dictionary_type = "external-dynamic"
        elif reference_contracts == {"reference-only-type-not-declared"}:
            dictionary_type = "reference-only-unspecified"
        else:
            dictionary_type = "reference-only-mixed-provenance"
        fixture_values = tuple(
            PreparedDictionaryValue.from_dict(raw["fixture_values"][key])
            for key in sorted(raw["fixture_values"])
        )
        required_values = tuple(
            PreparedDictionaryValue.from_dict(raw["required_values"][key])
            for key in sorted(raw["required_values"])
        )
        if fixture_values and raw["fixture_provenance"] is None and closed:
            fixture_provenance = _qualified_closed_fixture_subset_provenance(
                basis,
                dictionary_id=dictionary_id,
                required_values=required_values,
                fixture_values=fixture_values,
                source_row_ids=row_ids,
            )
        else:
            fixture_provenance = _validated_fixture_provenance(
                basis,
                dictionary_id=dictionary_id,
                fixture_values=fixture_values,
                provenance=raw["fixture_provenance"],
                external_dynamic=dictionary_type == "external-dynamic",
            )
        if fixture_provenance is not None:
            provenance_version = fixture_provenance["version"]
            provenance_effective_date = fixture_provenance["effective_date"]
            normalized_version = (
                None
                if provenance_version == DICTIONARY_METADATA_NOT_DECLARED
                else provenance_version
            )
            normalized_effective_date = (
                None
                if provenance_effective_date == DICTIONARY_METADATA_NOT_DECLARED
                else provenance_effective_date
            )
            if version is not None and normalized_version not in {None, version}:
                _fail(
                    "dictionary-metadata-conflict",
                    f"{dictionary_id} fixture version conflicts with qualified source metadata",
                )
            if (
                effective_date is not None
                and normalized_effective_date not in {None, effective_date}
            ):
                _fail(
                    "dictionary-metadata-conflict",
                    f"{dictionary_id} fixture effective date conflicts with qualified "
                    "source metadata",
                )
            version = version or normalized_version
            effective_date = effective_date or normalized_effective_date
            if version is not None and effective_date is not None:
                metadata_status = (
                    "version-and-effective-date-materialized-from-qualified-source-"
                    "and-registered-fixture"
                )
            elif version is not None or effective_date is not None:
                metadata_status = (
                    "partial-metadata-materialized-from-qualified-source-or-"
                    "registered-fixture"
                )
        payload = {
            "dictionary_id": dictionary_id,
            "dictionary_type": dictionary_type,
            "dictionary_type_evidence": type_evidence,
            "coverage_modes": modes,
            "required_values": [
                raw["required_values"][key]
                for key in sorted(raw["required_values"])
            ],
            "fixture_values": [
                raw["fixture_values"][key]
                for key in sorted(raw["fixture_values"])
            ],
            "fixture_provenance": fixture_provenance,
            "source_locators": locators,
            "version": version,
            "effective_date": effective_date,
            "metadata_status": metadata_status,
            "metadata_evidence": metadata_evidence,
            "obligation_bindings": [
                {
                    "obligation_id": obligation_id,
                    "property_id": graph_obligations[obligation_id].property_id,
                    "subject_key": graph_properties[
                        graph_obligations[obligation_id].property_id
                    ].subject_key,
                    "atomic_statement": graph_obligations[
                        obligation_id
                    ].atomic_statement,
                    "case_keys": sorted(
                        case_key
                        for case_key, _tc_id in case_by_obligation.get(
                            obligation_id,
                            [],
                        )
                    ),
                    "tc_ids": sorted(
                        tc_id
                        for _case_key, tc_id in case_by_obligation.get(
                            obligation_id,
                            [],
                        )
                    ),
                }
                for obligation_id in sorted(raw["obligation_ids"])
            ],
            "obligation_ids": sorted(raw["obligation_ids"]),
            "case_keys": sorted(raw["case_keys"]),
            "tc_ids": sorted(raw["tc_ids"]),
        }
        payload["source_binding_sha256"] = _digest(
            {
                "dictionary_id": dictionary_id,
                "source_locators": locators,
                "obligation_set_digest": basis.obligation_set.digest,
                "obligation_ids": sorted(raw["obligation_ids"]),
            }
        )
        payload["content_sha256"] = _digest(payload)
        result.append(payload)
    return result


_GAP_ID_RE = re.compile(r"\bGAP-[A-Za-z0-9._-]+\b")


def _coverage_gap_evidence(basis: ReviewerEvidenceBasis) -> dict[str, Any]:
    registered = next(
        (
            item
            for item in basis.registered_files
            if item.role == "scope-coverage-gaps"
        ),
        None,
    )
    if registered is None:  # pragma: no cover - basis constructor invariant
        _fail("coverage-gaps-unregistered", "coverage gap artifact is not registered")
    try:
        content = registered.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(
            "coverage-gaps-unreadable",
            f"coverage gap artifact is not valid UTF-8 text: {exc}",
        )
    if not content.strip():
        _fail("coverage-gaps-empty", "coverage gap artifact is empty")
    expected_ids = set(basis.compiled_scope.definition.gap_ids)
    actual_ids = set(_GAP_ID_RE.findall(content))
    if actual_ids != expected_ids:
        _fail(
            "coverage-gap-id-mismatch",
            "registered coverage gap artifact differs from scope registry: "
            f"missing={sorted(expected_ids - actual_ids)}, "
            f"extra={sorted(actual_ids - expected_ids)}",
        )
    return {
        "artifact": registered.to_dict(),
        "registered_gap_ids": sorted(expected_ids),
        "materialized_gap_ids": sorted(actual_ids),
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "complete-literal-registered-artifact",
    }


def _coverage_mapping(
    basis: ReviewerEvidenceBasis,
    graph: CoverageGraph,
) -> list[dict[str, str]]:
    properties_by_row: dict[str, list[Any]] = {}
    for prop in graph.properties:
        properties_by_row.setdefault(prop.source_row_id, []).append(prop)
    obligations_by_property: dict[str, list[Any]] = {}
    for obligation in graph.obligations:
        obligations_by_property.setdefault(obligation.property_id, []).append(obligation)
    cases_by_obligation: dict[str, list[Any]] = {}
    for case in graph.cases:
        for obligation_id in case.obligation_ids:
            cases_by_obligation.setdefault(obligation_id, []).append(case)
    result: list[dict[str, str]] = []
    for row in sorted(basis.manifest.source_rows, key=lambda item: item.source_row_id):
        properties = sorted(
            properties_by_row.get(row.source_row_id, []),
            key=lambda item: item.property_id,
        )
        if not properties:
            result.append(
                {
                    "source_row_id": row.source_row_id,
                    "assertion_id": "",
                    "property_id": "",
                    "obligation_id": "",
                    "case_key": "",
                    "tc_id": "",
                }
            )
            continue
        for prop in properties:
            obligations = sorted(
                obligations_by_property.get(prop.property_id, []),
                key=lambda item: item.obligation_id,
            )
            if not obligations:
                result.append(
                    {
                        "source_row_id": row.source_row_id,
                        "assertion_id": prop.assertion_id,
                        "property_id": prop.property_id,
                        "obligation_id": "",
                        "case_key": "",
                        "tc_id": "",
                    }
                )
                continue
            for obligation in obligations:
                cases = sorted(
                    cases_by_obligation.get(obligation.obligation_id, []),
                    key=lambda item: item.case_key,
                )
                if not cases:
                    result.append(
                        {
                            "source_row_id": row.source_row_id,
                            "assertion_id": prop.assertion_id,
                            "property_id": prop.property_id,
                            "obligation_id": obligation.obligation_id,
                            "case_key": "",
                            "tc_id": "",
                        }
                    )
                    continue
                for case in cases:
                    result.append(
                        {
                            "source_row_id": row.source_row_id,
                            "assertion_id": prop.assertion_id,
                            "property_id": prop.property_id,
                            "obligation_id": obligation.obligation_id,
                            "case_key": case.case_key,
                            "tc_id": case.tc_id,
                        }
                    )
    return result


def _supporting_evidence_mapping(
    basis: ReviewerEvidenceBasis,
    graph: CoverageGraph,
) -> list[dict[str, str]]:
    rows = {item.source_row_id: item for item in basis.manifest.source_rows}
    properties = {item.assertion_id: item for item in graph.properties}
    obligations_by_property: dict[str, list[Any]] = {}
    for obligation in graph.obligations:
        obligations_by_property.setdefault(obligation.property_id, []).append(obligation)
    cases_by_obligation: dict[str, list[Any]] = {}
    for case in graph.cases:
        for obligation_id in case.obligation_ids:
            cases_by_obligation.setdefault(obligation_id, []).append(case)
    result: list[dict[str, str]] = []
    for assertion in sorted(
        basis.manifest.assertions,
        key=lambda item: item.assertion_id,
    ):
        prop = properties.get(assertion.assertion_id)
        if prop is None:  # guarded by build_reviewer_evidence_pack
            continue
        downstream: list[tuple[str, str, str]] = []
        obligations = sorted(
            obligations_by_property.get(prop.property_id, []),
            key=lambda item: item.obligation_id,
        )
        if not obligations:
            downstream.append(("", "", ""))
        for obligation in obligations:
            cases = sorted(
                cases_by_obligation.get(obligation.obligation_id, []),
                key=lambda item: item.case_key,
            )
            if not cases:
                downstream.append((obligation.obligation_id, "", ""))
            else:
                downstream.extend(
                    (obligation.obligation_id, case.case_key, case.tc_id)
                    for case in cases
                )
        for binding in sorted(
            assertion.supporting_source_bindings,
            key=lambda item: (
                item.source_row_id,
                item.evidence_role,
                item.exact_source_fragment,
            ),
        ):
            source_row = rows.get(binding.source_row_id)
            if source_row is None:  # manifest validation should reject this first
                _fail(
                    "supporting-source-row-missing",
                    f"{assertion.assertion_id} references {binding.source_row_id}",
                )
            for obligation_id, case_key, tc_id in downstream:
                result.append(
                    {
                        "source_row_id": binding.source_row_id,
                        "source_path": source_row.source_path,
                        "source_locator": source_row.source_locator,
                        "evidence_role": binding.evidence_role,
                        "exact_source_fragment": binding.exact_source_fragment,
                        "exact_source_fragment_sha256": hashlib.sha256(
                            binding.exact_source_fragment.encode("utf-8")
                        ).hexdigest(),
                        "primary_source_row_id": assertion.source_row_id,
                        "assertion_id": assertion.assertion_id,
                        "property_id": prop.property_id,
                        "obligation_id": obligation_id,
                        "case_key": case_key,
                        "tc_id": tc_id,
                    }
                )
    return result


def build_design_support_mapping(
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
) -> list[dict[str, Any]]:
    """Bind source-backed sibling actions embedded in another obligation's TC.

    Deterministic designs may use a sibling obligation to prepare state, perform
    a source-backed transition, or clean up.  Those obligations belong in the
    design traceability, but they must not be promoted to an additional primary
    coverage owner for the case.  This projection keeps the primary mapping
    atomic while giving the reviewer an exact, role-tagged chain for each
    materialized sibling action.
    """

    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    graph_cases = {item.case_key: item for item in graph.cases}
    sections = (
        ("setup", "preconditions"),
        ("action", "steps"),
        ("cleanup", "postconditions"),
    )
    result: list[dict[str, Any]] = []
    for design in sorted(cases, key=lambda item: item.case_key):
        graph_case = graph_cases.get(design.case_key)
        if graph_case is None or len(graph_case.obligation_ids) != 1:
            _fail(
                "design-support-primary-binding-invalid",
                f"{design.case_key} must have exactly one primary graph obligation",
            )
        primary_obligation_id = graph_case.obligation_ids[0]
        traced_siblings = sorted(
            {
                token
                for token in design.traceability
                if token in obligations and token != primary_obligation_id
            }
        )
        for obligation_id in traced_siblings:
            obligation = obligations[obligation_id]
            prop = properties.get(obligation.property_id)
            if prop is None:  # pragma: no cover - coverage graph validation owns this
                _fail(
                    "design-support-property-missing",
                    f"{obligation_id} references unknown {obligation.property_id}",
                )
            source_fragments = tuple(
                dict.fromkeys(
                    fragment.strip()
                    for fragment in (
                        obligation.validation_trigger,
                        obligation.cleanup_strategy,
                    )
                    if fragment.strip()
                )
            )
            materialized = False
            for support_role, field_name in sections:
                field_items = getattr(design, field_name)
                for item_index, materialized_text in enumerate(field_items):
                    matching_fragments = [
                        fragment
                        for fragment in source_fragments
                        if fragment in materialized_text
                    ]
                    if not matching_fragments:
                        continue
                    materialized = True
                    # The longer exact fragment is the most specific binding if
                    # a contract contains nested action text.
                    source_fragment = sorted(
                        matching_fragments,
                        key=lambda value: (-len(value), value),
                    )[0]
                    result.append(
                        {
                            "support_role": support_role,
                            "test_case_field": field_name,
                            "item_index": item_index,
                            "materialized_text": materialized_text,
                            "materialized_text_sha256": hashlib.sha256(
                                materialized_text.encode("utf-8")
                            ).hexdigest(),
                            "source_action_fragment": source_fragment,
                            "source_row_id": prop.source_row_id,
                            "assertion_id": prop.assertion_id,
                            "property_id": prop.property_id,
                            "obligation_id": obligation.obligation_id,
                            "case_key": design.case_key,
                            "tc_id": design.tc_id,
                        }
                    )
            if not materialized:
                _fail(
                    "design-support-traceability-not-materialized",
                    f"{design.tc_id} traces sibling {obligation_id} without an exact "
                    "setup/action/cleanup action",
                )
    return result


def build_reviewer_evidence_pack(
    basis: ReviewerEvidenceBasis,
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
    draft_markdown: str,
    draft_sha256: str,
    acceptance_contract: Mapping[str, Any],
) -> ReviewerEvidencePack:
    if not isinstance(basis, ReviewerEvidenceBasis):
        _fail("invalid-evidence-basis", "basis has the wrong type")
    basis.verify()
    if not isinstance(graph, CoverageGraph):
        _fail("invalid-coverage-graph", "graph has the wrong type")
    if (
        graph.scope_slug != basis.manifest.scope_slug
        or graph.source_manifest_digest != basis.manifest.digest
        or graph.obligation_set_digest != basis.obligation_set.digest
    ):
        _fail("graph-binding-mismatch", "coverage graph differs from qualified inputs")
    manifest_assertions = {
        item.assertion_id: item for item in basis.manifest.assertions
    }
    graph_assertion_ids = [item.assertion_id for item in graph.properties]
    if (
        len(graph_assertion_ids) != len(set(graph_assertion_ids))
        or set(graph_assertion_ids) != set(manifest_assertions)
    ):
        _fail(
            "source-projection-assertion-loss",
            "normalized projection must preserve every manifest assertion exactly once",
        )
    for prop in graph.properties:
        assertion = manifest_assertions[prop.assertion_id]
        if (
            prop.source_row_id != assertion.source_row_id
            or prop.source_path != assertion.source_path
            or prop.source_locator != assertion.locator
            or prop.source_text_sha256
            != hashlib.sha256(assertion.exact_source_text.encode("utf-8")).hexdigest()
        ):
            _fail(
                "source-projection-binding-mismatch",
                f"normalized property differs from assertion {prop.assertion_id}",
            )
    expected_obligations = {
        obligation_id
        for assertion in basis.manifest.assertions
        for obligation_id in assertion.obligation_ids
    }
    if {item.obligation_id for item in graph.obligations} != expected_obligations:
        _fail(
            "source-projection-obligation-loss",
            "normalized projection must preserve every assertion obligation",
        )
    if not isinstance(draft_markdown, str) or not draft_markdown:
        _fail("draft-missing", "reviewer evidence requires the complete draft")
    actual_draft_sha256 = hashlib.sha256(draft_markdown.encode("utf-8")).hexdigest()
    if actual_draft_sha256 != draft_sha256:
        _fail("draft-digest-mismatch", "draft text differs from suite gate digest")
    graph_cases = {item.case_key: item for item in graph.cases}
    case_designs = sorted(cases, key=lambda item: item.case_key)
    if [item.case_key for item in case_designs] != sorted(graph_cases):
        _fail("test-case-set-mismatch", "test-case designs differ from coverage graph")
    for design in case_designs:
        graph_case = graph_cases[design.case_key]
        if design.tc_id != graph_case.tc_id or design.status != graph_case.status:
            _fail(
                "test-case-binding-mismatch",
                f"test-case design differs from graph: {design.case_key}",
            )
    if not isinstance(acceptance_contract, Mapping):
        _fail("acceptance-contract-missing", "acceptance contract must be an object")

    literal_source_evidence = _literal_source_evidence(basis)
    try:
        source_parity = verify_bounded_source_parity(
            basis.manifest,
            basis.registered_files,
            literal_source_evidence,
            requirement_guard=(
                basis.compiled_scope.definition.requirement_guard
            ),
        )
    except SourceParityError as exc:
        _fail(f"source-parity-{exc.code}", str(exc))
    dictionaries = _dictionary_slice(basis, graph)
    coverage_gaps = _coverage_gap_evidence(basis)
    coverage_mapping = _coverage_mapping(basis, graph)
    supporting_evidence_mapping = _supporting_evidence_mapping(basis, graph)
    design_support_mapping = build_design_support_mapping(graph, case_designs)
    mockup_by_path = {item.path: item for item in basis.manifest.mockups}
    mockup_attachments = [
        {
            "path": item.relative_path,
            "role": "scope-mockup",
            "scope_id": basis.compiled_scope.scope_id,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "screen_description": mockup_by_path[item.relative_path].screen_name,
            "locators": list(mockup_by_path[item.relative_path].locators),
        }
        for item in basis.mockup_files
    ]
    source_files = [
        item.to_dict()
        for item in basis.registered_files
        if item.role not in {"scope-mockup", "scope-coverage-gaps"}
    ]
    receipt = basis.source_review_receipt
    payload = {
        "schema_version": 2,
        "identity": {
            "contract": "reviewer-evidence-pack-v2",
            "scope_id": basis.compiled_scope.scope_id,
            "ft_slug": graph.ft_slug,
            "registry_digest": basis.compiled_scope.registry_digest,
            "source_row_extraction_spec_digest": (
                basis.compiled_scope.extraction_spec.digest
            ),
            "source_row_baseline_digest": basis.compiled_scope.baseline.digest,
            "source_manifest_digest": basis.manifest.digest,
            "source_review_receipt_sha256": basis.review_receipt_sha256,
            "obligation_set_digest": basis.obligation_set.digest,
            "coverage_graph_digest": graph.digest,
            "graph_digest": graph.digest,
            "draft_sha256": draft_sha256,
            "evidence_basis_sha256": basis.basis_digest,
        },
        "literal_source_evidence": literal_source_evidence,
        "source_structure": {
            "scope_definition": basis.compiled_scope.definition.to_dict(),
            "selected_xhtml": (
                basis.compiled_scope.baseline.selected_xhtml.to_dict()
            ),
            "candidate_count": basis.compiled_scope.baseline.candidate_count,
            "source_files": source_files,
            "docx_xhtml_pdf_parity": source_parity,
            "source_review_attestation": {
                "status": "accepted-source-review",
                "review_decision": receipt.decision,
                "source_inventory_verdict": receipt.source_inventory_review.verdict,
                "scope_boundary_verdict": receipt.scope_boundary_review.verdict,
                "receipt_sha256": basis.review_receipt_sha256,
            },
            "section_path_status": "materialized-for-all-xhtml-literal-rows",
        },
        "dictionaries": dictionaries,
        "coverage_gaps": coverage_gaps,
        "mockup_attachments": mockup_attachments,
        "normalized_projection": graph.to_dict(),
        "test_cases": {
            "draft_markdown": draft_markdown,
            "designs": [item.to_dict() for item in case_designs],
        },
        "coverage_mapping": coverage_mapping,
        "supporting_evidence_mapping": supporting_evidence_mapping,
        "design_support_mapping": design_support_mapping,
        "acceptance": dict(acceptance_contract),
    }
    rendered = _canonical_bytes(payload).decode("utf-8")
    return ReviewerEvidencePack(rendered, basis.mockup_files)


__all__ = [
    "ReviewerEvidenceBasis",
    "ReviewerEvidenceError",
    "ReviewerEvidencePack",
    "build_design_support_mapping",
    "build_reviewer_evidence_pack",
    "load_reviewer_evidence_basis_document",
    "prepare_reviewer_evidence_basis",
]
