from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .runtime import StageRuntimeError


DIMENSION_BINDING_CONTRACT = "reviewer-dimension-source-bindings-v1"
DIMENSION_BINDING_BEGIN = "<!-- REVIEWER-DIMENSION-SOURCE-BINDINGS:BEGIN -->"
DIMENSION_BINDING_END = "<!-- REVIEWER-DIMENSION-SOURCE-BINDINGS:END -->"
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


@dataclass(frozen=True)
class ReviewerDimensionSourceBindings:
    dimension_source_refs: tuple[tuple[str, tuple[str, ...]], ...]

    @classmethod
    def create(
        cls,
        values: Mapping[str, Sequence[str]],
    ) -> ReviewerDimensionSourceBindings:
        if any(not isinstance(dimension, str) for dimension in values):
            raise StageRuntimeError(
                "reviewer dimension binding dimensions must be strings"
            )
        normalized: list[tuple[str, tuple[str, ...]]] = []
        for dimension in sorted(values):
            raw_refs = values[dimension]
            if isinstance(raw_refs, (str, bytes)) or not isinstance(raw_refs, Sequence):
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} source refs must be an array"
                )
            if any(not isinstance(value, str) for value in raw_refs):
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} source refs must be strings"
                )
            refs = tuple(sorted(dict.fromkeys(raw_refs)))
            normalized.append((dimension, refs))
        result = cls(tuple(normalized))
        result.validate()
        return result

    def validate(self) -> None:
        dimensions = [dimension for dimension, _ in self.dimension_source_refs]
        if dimensions != sorted(dimensions) or len(dimensions) != len(set(dimensions)):
            raise StageRuntimeError(
                "reviewer dimension bindings must contain unique sorted dimensions"
            )
        for dimension, source_refs in self.dimension_source_refs:
            if not IDENTIFIER.fullmatch(dimension):
                raise StageRuntimeError(
                    "reviewer dimension binding dimension must be a stable identifier"
                )
            if not source_refs:
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} must bind at least one source ref"
                )
            if source_refs != tuple(sorted(source_refs)) or len(source_refs) != len(
                set(source_refs)
            ):
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} source refs must be unique and sorted"
                )
            if any(not isinstance(value, str) or not value.strip() for value in source_refs):
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} source refs must be non-empty strings"
                )

    def as_mapping(self) -> dict[str, tuple[str, ...]]:
        return dict(self.dimension_source_refs)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "contract": DIMENSION_BINDING_CONTRACT,
            "dimension_source_refs": {
                dimension: list(source_refs)
                for dimension, source_refs in self.dimension_source_refs
            },
        }

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> ReviewerDimensionSourceBindings:
        if not isinstance(payload, Mapping) or set(payload) != {
            "contract",
            "dimension_source_refs",
        }:
            raise StageRuntimeError(
                "reviewer dimension binding payload has invalid fields"
            )
        if payload.get("contract") != DIMENSION_BINDING_CONTRACT:
            raise StageRuntimeError("reviewer dimension binding contract mismatch")
        raw_mapping = payload.get("dimension_source_refs")
        if not isinstance(raw_mapping, Mapping):
            raise StageRuntimeError(
                "reviewer dimension binding dimension_source_refs must be an object"
            )
        values: dict[str, tuple[str, ...]] = {}
        for dimension, raw_refs in raw_mapping.items():
            if not isinstance(dimension, str) or not isinstance(raw_refs, list):
                raise StageRuntimeError(
                    "reviewer dimension binding entries must map strings to arrays"
                )
            if any(not isinstance(value, str) for value in raw_refs):
                raise StageRuntimeError(
                    f"reviewer dimension {dimension} source refs must be strings"
                )
            values[dimension] = tuple(raw_refs)
        result = cls(tuple((key, values[key]) for key in raw_mapping))
        result.validate()
        return result


def render_reviewer_dimension_source_bindings(
    bindings: ReviewerDimensionSourceBindings,
) -> str:
    payload = json.dumps(
        bindings.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "\n".join(
        (
            DIMENSION_BINDING_BEGIN,
            "```json",
            payload,
            "```",
            DIMENSION_BINDING_END,
        )
    )


def parse_reviewer_dimension_source_bindings(
    evidence_text: str,
) -> ReviewerDimensionSourceBindings:
    pattern = re.compile(
        re.escape(DIMENSION_BINDING_BEGIN)
        + r"\s*```json\s*(\{.*?\})\s*```\s*"
        + re.escape(DIMENSION_BINDING_END),
        flags=re.DOTALL,
    )
    matches = pattern.findall(evidence_text)
    if len(matches) != 1:
        raise StageRuntimeError(
            "source evidence must contain exactly one reviewer dimension binding block"
        )
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise StageRuntimeError(
            "reviewer dimension binding block is not valid JSON"
        ) from exc
    if not isinstance(payload, Mapping):
        raise StageRuntimeError("reviewer dimension binding payload must be an object")
    return ReviewerDimensionSourceBindings.from_dict(payload)
