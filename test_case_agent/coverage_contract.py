from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError
from test_case_agent.review_cycle.source_assertions import (
    EmbeddedSourceAssertionContract,
    SourceAssertion,
    SourceAssertionContractError,
    SourceAssertionManifest,
    SourceAssertionReviewReceipt,
    normalize_exact_source_text,
)


class CoverageContractError(ValueError):
    """An accepted source contract cannot be bound to a prepared package."""


_SHA256 = re.compile(r"[0-9a-f]{64}")


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expected_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CoverageContractError(f"{label} must be non-empty trimmed text")
    return value


def _expected_digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise CoverageContractError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class AcceptedCoverageContractBinding:
    """Deterministic receipt for one accepted source/package pair."""

    schema_version: int
    scope_slug: str
    package_id: str
    package_version: int
    source_manifest_digest: str
    source_review_receipt_digest: str
    obligation_set_digest: str
    obligation_ids: tuple[str, ...]
    source_hashes: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope_slug": self.scope_slug,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "source_manifest_digest": self.source_manifest_digest,
            "source_review_receipt_digest": self.source_review_receipt_digest,
            "obligation_set_digest": self.obligation_set_digest,
            "obligation_ids": list(self.obligation_ids),
            "source_hashes": [
                {"path": path, "sha256": digest}
                for path, digest in self.source_hashes
            ],
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.to_dict())


def _normalize_manifest(
    manifest: SourceAssertionManifest,
) -> SourceAssertionManifest:
    """Run the existing shape parser without inventing a second FT parser."""

    try:
        normalized = SourceAssertionManifest.from_dict(manifest.to_dict())
    except (AttributeError, SourceAssertionContractError) as exc:
        raise CoverageContractError(f"invalid source assertion manifest: {exc}") from exc
    if normalized.digest != manifest.digest:
        raise CoverageContractError(
            "source assertion manifest changed during canonical normalization"
        )
    # Keep the original instance: the existing repository validator stores its
    # authenticated source texts in the private, non-serialized validation cache.
    # Replacing it with the round-tripped shape would discard that evidence before
    # ScopeBoundaryReview validates source-bound exclusions.
    return manifest


def _source_hashes(
    manifest: SourceAssertionManifest,
) -> tuple[tuple[str, str], ...]:
    paths = [source.path for source in manifest.sources]
    if len(paths) != len(set(paths)):
        raise CoverageContractError("source assertion manifest has duplicate source paths")
    return tuple(sorted((source.path, source.sha256) for source in manifest.sources))


def _validate_expected_source_hashes(
    actual: tuple[tuple[str, str], ...],
    expected: Mapping[str, str],
) -> None:
    if not isinstance(expected, Mapping):
        raise CoverageContractError("expected_source_hashes must be a path-to-SHA mapping")
    normalized: dict[str, str] = {}
    for path, digest in expected.items():
        normalized[_expected_text(path, "expected_source_hashes path")] = (
            _expected_digest(digest, f"expected_source_hashes[{path!r}]")
        )
    actual_by_path = dict(actual)
    if normalized != actual_by_path:
        missing = sorted(set(actual_by_path) - set(normalized))
        unexpected = sorted(set(normalized) - set(actual_by_path))
        changed = sorted(
            path
            for path in set(normalized) & set(actual_by_path)
            if normalized[path] != actual_by_path[path]
        )
        raise CoverageContractError(
            "expected source hashes do not match the accepted manifest: "
            f"missing={missing or 'none'}, unexpected={unexpected or 'none'}, "
            f"changed={changed or 'none'}"
        )


def _source_obligation_owners(
    manifest: SourceAssertionManifest,
) -> dict[str, SourceAssertion]:
    owners: dict[str, SourceAssertion] = {}
    for assertion in manifest.assertions:
        if assertion.semantic_disposition != "testable":
            continue
        for obligation_id in assertion.obligation_ids:
            if obligation_id in owners:
                raise CoverageContractError(
                    f"source obligation {obligation_id} is owned by multiple assertions"
                )
            owners[obligation_id] = assertion
    if not owners:
        raise CoverageContractError(
            "accepted source contract has no testable obligation set to bind"
        )
    return owners


def _normalized(value: str) -> str:
    return normalize_exact_source_text(value).casefold()


def _intent_contains_authenticated_clause(intent: str, clause: str) -> bool:
    """Match a complete reviewed clause inside compiler-owned intent framing.

    Source-first packages may wrap an action/condition in labelled deterministic
    metadata (for example ``Action contract: ...``), so the whole intent cannot be
    byte-identical to the action tuple.  The reviewed clauses themselves must still
    survive exactly after transport-whitespace normalization.  An arbitrary intent
    sharing only an OBL/ATOM id is therefore not admitted.
    """

    normalized_intent = _normalized(intent)
    normalized_clause = _normalized(clause)
    if not normalized_clause:
        return False
    offset = normalized_intent.find(normalized_clause)
    while offset >= 0:
        end = offset + len(normalized_clause)
        cuts_left = (
            normalized_clause[0].isalnum()
            and offset > 0
            and normalized_intent[offset - 1].isalnum()
        )
        cuts_right = (
            normalized_clause[-1].isalnum()
            and end < len(normalized_intent)
            and normalized_intent[end].isalnum()
        )
        if not cuts_left and not cuts_right:
            return True
        offset = normalized_intent.find(normalized_clause, offset + 1)
    return False


def _validate_obligation_fields(
    obligation_id: str,
    obligation: PreparedObligation,
    assertion: SourceAssertion,
) -> None:
    if _normalized(obligation.atomic_statement) != _normalized(
        assertion.canonical_statement
    ):
        raise CoverageContractError(
            f"prepared obligation {obligation_id} atomic_statement does not match "
            f"accepted {assertion.assertion_id}.canonical_statement"
        )

    expected_oracle = "; ".join(assertion.oracle_clauses)
    if _normalized(obligation.observable_oracle) != _normalized(expected_oracle):
        raise CoverageContractError(
            f"prepared obligation {obligation_id} observable_oracle does not match "
            f"accepted {assertion.assertion_id}.oracle_clauses"
        )

    missing_intent_clauses = tuple(
        clause
        for clause in assertion.action_clauses
        if not _intent_contains_authenticated_clause(obligation.test_intent, clause)
    )
    if missing_intent_clauses:
        raise CoverageContractError(
            f"prepared obligation {obligation_id} test_intent omits accepted "
            f"action clauses from {assertion.assertion_id}"
        )

    canonical_refs = (
        assertion.requirement_codes
        if assertion.requirement_codes
        else (assertion.source_row_id,)
    )
    missing_refs = sorted(set(canonical_refs) - set(obligation.source_refs))
    if missing_refs:
        raise CoverageContractError(
            f"prepared obligation {obligation_id} source_refs omit accepted "
            f"references: {missing_refs}"
        )


def _validate_obligation_exactness(
    manifest: SourceAssertionManifest,
    obligations: PreparedObligationSet,
) -> tuple[str, ...]:
    source_owners = _source_obligation_owners(manifest)
    prepared = {item.obligation_id: item for item in obligations.obligations}
    assertions_by_atom = {item.atom_id: item for item in manifest.assertions}
    closed_context_ids: set[str] = set()
    for obligation_id, item in prepared.items():
        if item.coverage_status != "not-applicable":
            continue
        assertion = assertions_by_atom.get(item.traceability_atom_id)
        if (
            assertion is not None
            and assertion.semantic_disposition != "testable"
            and not assertion.obligation_ids
            and not item.observable_oracle
            and not item.gap_id
            and not item.dictionary_refs
            and not item.dictionary_requirements
            and item.calibration_status == "none"
            and not item.planned_test_case_id
            and assertion.source_row_id in item.source_refs
        ):
            closed_context_ids.add(obligation_id)

    prepared_testable = {
        obligation_id
        for obligation_id, item in prepared.items()
        if item.coverage_status == "testable"
    }
    missing = sorted(set(source_owners) - prepared_testable)
    unexpected = sorted(
        set(prepared) - set(source_owners) - closed_context_ids
    )
    if missing or unexpected:
        raise CoverageContractError(
            "prepared obligation set is not exact for the accepted source contract: "
            f"missing={missing or 'none'}, unexpected={unexpected or 'none'}"
        )
    wrong_atoms = sorted(
        obligation_id
        for obligation_id, assertion in source_owners.items()
        if prepared[obligation_id].traceability_atom_id != assertion.atom_id
    )
    if wrong_atoms:
        raise CoverageContractError(
            "prepared obligations do not preserve their source ATOM owners: "
            + ", ".join(wrong_atoms)
        )
    for obligation_id, assertion in source_owners.items():
        _validate_obligation_fields(
            obligation_id,
            prepared[obligation_id],
            assertion,
        )
    return tuple(sorted(source_owners))


def bind_accepted_source_contract(
    *,
    contract: EmbeddedSourceAssertionContract,
    obligation_set: PreparedObligationSet,
    expected_scope_slug: str,
    expected_manifest_digest: str | None = None,
    expected_review_receipt_digest: str | None = None,
    expected_package_id: str | None = None,
    expected_obligation_set_digest: str | None = None,
    expected_source_hashes: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> AcceptedCoverageContractBinding:
    """Bind reviewed source semantics to one exact prepared obligation package.

    The function only follows typed ASSERT/ATOM/OBL fields and registered digests.
    It deliberately does not derive coverage properties from requirement prose.
    Passing ``repo_root`` additionally invokes the existing manifest validator so
    every registered source/evidence hash is checked against the filesystem.
    """

    if not isinstance(contract, EmbeddedSourceAssertionContract):
        raise CoverageContractError(
            "contract must be an EmbeddedSourceAssertionContract"
        )
    if not isinstance(obligation_set, PreparedObligationSet):
        raise CoverageContractError("obligation_set must be a PreparedObligationSet")

    expected_scope = _expected_text(expected_scope_slug, "expected_scope_slug")
    manifest = _normalize_manifest(contract.manifest)
    if manifest.scope_slug != expected_scope:
        raise CoverageContractError(
            "accepted source contract scope does not match the requested scope: "
            f"expected={expected_scope}, actual={manifest.scope_slug}"
        )
    if expected_manifest_digest is not None:
        expected = _expected_digest(
            expected_manifest_digest, "expected_manifest_digest"
        )
        if manifest.digest != expected:
            raise CoverageContractError(
                "accepted source contract does not match expected manifest digest"
            )

    receipt = contract.review_receipt
    if not isinstance(receipt, SourceAssertionReviewReceipt):
        raise CoverageContractError(
            "contract review_receipt must be a SourceAssertionReviewReceipt"
        )
    if receipt.decision != "accepted":
        raise CoverageContractError(
            "source assertion review receipt must have decision=accepted"
        )

    if repo_root is not None:
        try:
            manifest.validate(Path(repo_root))
        except (OSError, SourceAssertionContractError) as exc:
            raise CoverageContractError(
                f"registered source hash validation failed: {exc}"
            ) from exc

    try:
        receipt.validate(manifest)
    except (AttributeError, SourceAssertionContractError) as exc:
        raise CoverageContractError(
            f"source assertion review receipt is not valid for the manifest: {exc}"
        ) from exc
    receipt_digest = _canonical_digest(receipt.to_dict())
    if expected_review_receipt_digest is not None:
        expected = _expected_digest(
            expected_review_receipt_digest,
            "expected_review_receipt_digest",
        )
        if receipt_digest != expected:
            raise CoverageContractError(
                "source assertion review receipt digest does not match the expected digest"
            )

    try:
        obligation_set.validate()
    except StageRuntimeError as exc:
        raise CoverageContractError(
            f"prepared obligation package is invalid: {exc}"
        ) from exc
    if expected_package_id is not None:
        expected_id = _expected_text(expected_package_id, "expected_package_id")
        if obligation_set.package_id != expected_id:
            raise CoverageContractError(
                "prepared obligation package_id does not match the expected package"
            )
    if expected_obligation_set_digest is not None:
        expected = _expected_digest(
            expected_obligation_set_digest,
            "expected_obligation_set_digest",
        )
        if obligation_set.digest != expected:
            raise CoverageContractError(
                "prepared obligation set digest does not match the expected digest"
            )

    source_hashes = _source_hashes(manifest)
    if expected_source_hashes is not None:
        _validate_expected_source_hashes(source_hashes, expected_source_hashes)
    obligation_ids = _validate_obligation_exactness(manifest, obligation_set)
    return AcceptedCoverageContractBinding(
        schema_version=1,
        scope_slug=manifest.scope_slug,
        package_id=obligation_set.package_id,
        package_version=obligation_set.package_version,
        source_manifest_digest=manifest.digest,
        source_review_receipt_digest=receipt_digest,
        obligation_set_digest=obligation_set.digest,
        obligation_ids=obligation_ids,
        source_hashes=source_hashes,
    )
