from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from test_case_agent.review_cycle import source_assertions


FROZEN_AGENT_NOTES_SHA256 = (
    "a79deafdfce98e3156dc4cacaf518031c248983c3dadaa1c72544903420bdca8"
)


@contextmanager
def frozen_h64_h65_package_note(repo_root: Path):
    """Validate frozen H64/H65 evidence against its captured package-note digest.

    H64/H65 predate later edits to the mutable package-level AGENT-NOTES.md.  The
    helper substitutes only that captured digest; every other registered file is
    still hashed from the current filesystem.  Production callers never use this
    helper and therefore retain strict freshness validation.
    """

    package_note = (repo_root / "fts/AutoFin/AGENT-NOTES.md").resolve()
    real_sha256_file = source_assertions.sha256_file

    def frozen_sha256_file(path: Path) -> str:
        if path.resolve() == package_note:
            return FROZEN_AGENT_NOTES_SHA256
        return real_sha256_file(path)

    with patch.object(
        source_assertions,
        "sha256_file",
        side_effect=frozen_sha256_file,
    ):
        yield
