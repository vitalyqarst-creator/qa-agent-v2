from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Mapping


class CaseIdentityError(ValueError):
    """A stable test-case identity cannot be assigned safely."""


_KEY_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
_PREFIX = re.compile(r"[A-Z0-9][A-Z0-9-]{1,30}")
_TC_ID = re.compile(r"TC-[A-Z0-9][A-Z0-9-]{1,30}-[A-F0-9]{10}")


def _part(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaseIdentityError(f"{label} must be non-empty text")
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = re.sub(r"\s+", "-", normalized)
    if _KEY_PART.fullmatch(normalized) is None:
        raise CaseIdentityError(
            f"{label} must be a stable typed key, not free-form prose: {value!r}"
        )
    return normalized


def semantic_case_key(
    *,
    scope_slug: str,
    subject_key: str,
    property_kind: str,
    coverage_variant: str,
    condition_key: str = "always",
) -> str:
    """Build an order- and locator-independent semantic identity.

    Requirement codes, source locators, display wording and ordinal positions are
    deliberately absent. A caller must change a typed component only when the
    test intent changes.
    """

    parts = (
        _part(scope_slug, "scope_slug"),
        _part(subject_key, "subject_key"),
        _part(property_kind, "property_kind"),
        _part(coverage_variant, "coverage_variant"),
        _part(condition_key, "condition_key"),
    )
    return "|".join(parts)


def stable_tc_id(*, prefix: str, case_key: str) -> str:
    if _PREFIX.fullmatch(prefix) is None:
        raise CaseIdentityError(
            "prefix must match [A-Z0-9][A-Z0-9-]{1,30}"
        )
    if not isinstance(case_key, str) or case_key.count("|") != 4:
        raise CaseIdentityError("case_key must be produced by semantic_case_key")
    suffix = hashlib.sha256(case_key.encode("utf-8")).hexdigest()[:10].upper()
    return f"TC-{prefix}-{suffix}"


def assign_stable_ids(
    case_keys: Iterable[str],
    *,
    prefix: str,
    existing: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Assign stable IDs and fail closed on duplicate or conflicting identity."""

    keys = tuple(case_keys)
    if len(keys) != len(set(keys)):
        raise CaseIdentityError("case_keys contain a duplicate semantic identity")
    current = dict(existing or {})
    if len(current.values()) != len(set(current.values())):
        raise CaseIdentityError("existing identity registry reuses a TC-ID")
    for key, tc_id in current.items():
        if not isinstance(key, str) or key.count("|") != 4:
            raise CaseIdentityError("existing identity registry contains an invalid key")
        if _TC_ID.fullmatch(tc_id) is None:
            raise CaseIdentityError(
                f"existing identity registry contains an invalid TC-ID: {tc_id}"
            )
        expected = stable_tc_id(prefix=prefix, case_key=key)
        if tc_id != expected:
            raise CaseIdentityError(
                f"existing identity registry conflicts for {key}: {tc_id} != {expected}"
            )
    assigned = {key: current.get(key, stable_tc_id(prefix=prefix, case_key=key)) for key in keys}
    if len(assigned.values()) != len(set(assigned.values())):
        raise CaseIdentityError("stable TC-ID hash collision detected")
    return assigned
