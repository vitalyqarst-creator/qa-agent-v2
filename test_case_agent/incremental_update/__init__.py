"""Incremental FT-version update pipeline."""

from .engine import (
    IncrementalUpdateError,
    IncrementalUpdateResult,
    run_incremental_update,
)

__all__ = [
    "IncrementalUpdateError",
    "IncrementalUpdateResult",
    "run_incremental_update",
]
