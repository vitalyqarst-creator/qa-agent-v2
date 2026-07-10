from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from test_case_agent.review_cycle.contracts import StageInputManifest, StageResult
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageRuntimeError,
    append_ndjson,
    resolve_repository_path,
    write_json_atomic,
)


TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "total_tokens")


@dataclass(frozen=True)
class StageMetrics:
    contract_version: int
    cycle_id: str
    stage_id: str
    attempt_id: str
    backend: str
    role: str
    scenario: str
    outcome: str
    duration_ms: int
    input_artifact_count: int
    input_artifact_bytes: int
    output_artifact_count: int
    output_artifact_bytes: int
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def validate(self) -> None:
        if self.contract_version != 2:
            raise StageRuntimeError("metrics contract_version must be 2")
        text_fields = ("cycle_id", "stage_id", "attempt_id", "backend", "role", "scenario", "outcome")
        for name in text_fields:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise StageRuntimeError(f"metrics {name} must be non-empty text")
        count_fields = (
            "duration_ms",
            "input_artifact_count",
            "input_artifact_bytes",
            "output_artifact_count",
            "output_artifact_bytes",
        )
        for name in count_fields:
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise StageRuntimeError(f"metrics {name} must be a non-negative integer")
        for name in TOKEN_FIELDS:
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise StageRuntimeError(f"metrics {name} must be a non-negative integer or null")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "cycle_id": self.cycle_id,
            "stage_id": self.stage_id,
            "attempt_id": self.attempt_id,
            "backend": self.backend,
            "role": self.role,
            "scenario": self.scenario,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "input_artifact_count": self.input_artifact_count,
            "input_artifact_bytes": self.input_artifact_bytes,
            "output_artifact_count": self.output_artifact_count,
            "output_artifact_bytes": self.output_artifact_bytes,
            **{name: getattr(self, name) for name in TOKEN_FIELDS},
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StageMetrics:
        expected = {
            "contract_version",
            "cycle_id",
            "stage_id",
            "attempt_id",
            "backend",
            "role",
            "scenario",
            "outcome",
            "duration_ms",
            "input_artifact_count",
            "input_artifact_bytes",
            "output_artifact_count",
            "output_artifact_bytes",
            *TOKEN_FIELDS,
        }
        if set(payload) != expected:
            raise StageRuntimeError("metrics payload has missing or unknown fields")
        metrics = cls(**{name: payload[name] for name in expected})
        metrics.validate()
        return metrics


def build_stage_metrics(
    manifest: StageInputManifest,
    result: StageResult,
    execution: BackendStageExecution,
    *,
    repo_root: Path,
) -> StageMetrics:
    result.validate_against(manifest)
    execution.validate()
    input_refs = (
        manifest.prompt_artifact,
        *manifest.instruction_artifacts,
        *manifest.source_artifacts,
        *manifest.handoff_artifacts,
    )
    input_bytes = sum(
        resolve_repository_path(reference.path, repo_root).stat().st_size
        for reference in input_refs
    )
    output_bytes = sum(
        resolve_repository_path(reference.path, repo_root).stat().st_size
        for reference in result.output_artifacts
    )
    usage = dict(execution.usage or {})
    metrics = StageMetrics(
        contract_version=manifest.contract_version,
        cycle_id=manifest.cycle_id,
        stage_id=manifest.stage_id,
        attempt_id=manifest.attempt_id,
        backend=execution.backend,
        role=manifest.role,
        scenario=manifest.scenario,
        outcome=result.outcome,
        duration_ms=execution.duration_ms,
        input_artifact_count=len(input_refs),
        input_artifact_bytes=input_bytes,
        output_artifact_count=len(result.output_artifacts),
        output_artifact_bytes=output_bytes,
        **{name: usage.get(name) for name in TOKEN_FIELDS},
    )
    metrics.validate()
    return metrics


class StageMetricsRecorder:
    def __init__(self, cycle_root: Path):
        self.cycle_root = cycle_root.resolve()

    @property
    def ledger_path(self) -> Path:
        return self.cycle_root / "stage-metrics.ndjson"

    def record(self, attempt_root: Path, metrics: StageMetrics) -> Path:
        metrics.validate()
        resolved_attempt = attempt_root.resolve()
        try:
            resolved_attempt.relative_to(self.cycle_root)
        except ValueError as exc:
            raise StageRuntimeError("metrics attempt root must be inside cycle root") from exc
        path = resolved_attempt / "metrics.json"
        if path.exists():
            raise StageRuntimeError("attempt metrics.json is immutable")
        write_json_atomic(path, metrics.to_dict())
        append_ndjson(self.ledger_path, metrics.to_dict())
        return path

    def load(self) -> tuple[StageMetrics, ...]:
        if not self.ledger_path.exists():
            return ()
        records: list[StageMetrics] = []
        for line_number, raw in enumerate(
            self.ledger_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise StageRuntimeError(f"invalid metrics NDJSON at line {line_number}") from exc
            records.append(StageMetrics.from_dict(payload))
        return tuple(records)


def summarize_metrics(records: Iterable[StageMetrics]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[StageMetrics]] = {}
    for record in records:
        record.validate()
        grouped.setdefault(record.backend, []).append(record)
    summary: dict[str, dict[str, Any]] = {}
    for backend, items in sorted(grouped.items()):
        durations = sorted(item.duration_ms for item in items)
        token_values = [item.total_tokens for item in items if item.total_tokens is not None]
        summary[backend] = {
            "stage_count": len(items),
            "non_blocked_count": sum(item.outcome != "blocked" for item in items),
            "blocked_count": sum(item.outcome == "blocked" for item in items),
            "duration_ms_total": sum(durations),
            "duration_ms_p50": _percentile(durations, 0.50),
            "duration_ms_p95": _percentile(durations, 0.95),
            "input_artifact_bytes_total": sum(item.input_artifact_bytes for item in items),
            "output_artifact_bytes_total": sum(item.output_artifact_bytes for item in items),
            "total_tokens": sum(token_values) if token_values else None,
        }
    return summary


def _percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    index = max(0, math.ceil(len(values) * fraction) - 1)
    return values[index]
