from __future__ import annotations

import sys
from typing import TextIO


def _configure_stream(stream: TextIO | None) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="strict")


def configure_utf8_stdio() -> None:
    """Make public CLI JSON deterministic on Windows and other non-UTF-8 consoles."""

    _configure_stream(sys.stdout)
    _configure_stream(sys.stderr)
