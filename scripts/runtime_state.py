from __future__ import annotations

import re


SCALAR_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$")


def scalar_values(content: str) -> dict[str, str]:
    """Read top-level YAML-like scalar values without adding a YAML dependency."""
    result: dict[str, str] = {}
    for line in content.splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        match = SCALAR_RE.fullmatch(line)
        if match is None:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[match.group(1)] = value
    return result
