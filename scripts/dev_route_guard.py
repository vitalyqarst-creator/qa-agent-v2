from __future__ import annotations

import os
import sys
from typing import TextIO


DEV_ROUTE_ENV = "FT_AGENT_ENABLE_DEV_ROUTES"


class DevRouteDisabledError(RuntimeError):
    pass


def require_dev_routes_enabled(route_name: str) -> None:
    """Fail closed for development-only orchestration entrypoints.

    The production agent must not accidentally enter benchmark, semantic bridge,
    semantic sharding, full-process observation, or compatibility orchestration
    routes. Those scripts may remain importable for historical analysis and
    tests, but their public `main()` entrypoints require an explicit opt-in.
    """

    if os.environ.get(DEV_ROUTE_ENV) == "1":
        return
    raise DevRouteDisabledError(
        f"{route_name} is disabled in the production agent profile. "
        f"Use the source-first controlled route instead. To run this "
        f"development-only route in a separate qualification repository, set "
        f"{DEV_ROUTE_ENV}=1 explicitly."
    )


def print_dev_route_disabled(
    exc: DevRouteDisabledError,
    *,
    stream: TextIO | None = None,
) -> None:
    print(str(exc), file=stream or sys.stderr)
