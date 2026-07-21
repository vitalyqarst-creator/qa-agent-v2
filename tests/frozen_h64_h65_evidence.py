from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from test_case_agent.review_cycle import source_assertions


FROZEN_AGENT_NOTES_SHA256 = (
    "a79deafdfce98e3156dc4cacaf518031c248983c3dadaa1c72544903420bdca8"
)
FROZEN_SUPPORT_DICTIONARY_SHA256 = (
    "a498cbd00237ff0ed9b48b5ffeade89a6914cff2f20f4fa231c566f7dbfc7e38"
)


def _frozen_digest_patch(
    repo_root: Path,
    *,
    freeze_package_note: bool,
):
    package_note = (repo_root / "fts/AutoFin/AGENT-NOTES.md").resolve()
    support_dictionary = (
        repo_root
        / "fts/AutoFin/support/PostFinal-v2/АФБ справочники 26.06.26.md"
    ).resolve()
    real_sha256_file = source_assertions.sha256_file

    def frozen_sha256_file(path: Path) -> str:
        resolved = path.resolve()
        if freeze_package_note and resolved == package_note:
            return FROZEN_AGENT_NOTES_SHA256
        if resolved == support_dictionary:
            return FROZEN_SUPPORT_DICTIONARY_SHA256
        return real_sha256_file(path)

    return patch.object(
        source_assertions,
        "sha256_file",
        side_effect=frozen_sha256_file,
    )


@contextmanager
def frozen_h64_h65_package_note(repo_root: Path):
    """Validate frozen H64/H65 evidence against its captured mutable digests.

    H64/H65 predate later edits to the package note and support dictionary.  The
    helper substitutes only those captured digests; every other registered file
    is still hashed from the current filesystem.  Production callers never use
    this helper and therefore retain strict freshness validation.
    """

    with _frozen_digest_patch(repo_root, freeze_package_note=True):
        yield


@contextmanager
def frozen_h64_h65_support_dictionary(repo_root: Path):
    """Freeze only the old support digest so package-note drift stays testable."""

    with _frozen_digest_patch(repo_root, freeze_package_note=False):
        yield
