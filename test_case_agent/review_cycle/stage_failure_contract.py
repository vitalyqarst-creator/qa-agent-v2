from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "stage",
        "return_code",
        "error_type",
        "error",
        "source",
    }
)


class StageFailureContractError(ValueError):
    """Raised when a failure envelope or orchestration event is invalid."""


class StageFailureReadError(StageFailureContractError):
    """Raised when a failure envelope cannot be read as JSON."""


class StageFailureWriteError(StageFailureContractError):
    """Raised when a failure envelope cannot be published safely."""


class StageFailureAlreadyExistsError(StageFailureWriteError):
    """Raised when exclusive publication would replace an existing artifact."""


def _require_exact_fields(payload: Mapping[str, Any]) -> None:
    actual = set(payload)
    missing = sorted(_ENVELOPE_FIELDS - actual)
    unknown = sorted(actual - _ENVELOPE_FIELDS)
    if not missing and not unknown:
        return
    details: list[str] = []
    if missing:
        details.append("missing=" + ",".join(missing))
    if unknown:
        details.append("unknown=" + ",".join(unknown))
    raise StageFailureContractError(
        "invalid stage failure envelope fields: " + "; ".join(details)
    )


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageFailureContractError(f"{field} must be a non-empty string")
    return value


def _validate_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise StageFailureContractError("stage failure envelope must be a JSON object")
    _require_exact_fields(payload)
    if type(payload["schema_version"]) is not int:  # bool is not a valid version.
        raise StageFailureContractError("schema_version must be an integer")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise StageFailureContractError(
            "unsupported stage failure schema_version: "
            f"{payload['schema_version']!r}; expected {SCHEMA_VERSION}"
        )
    _require_non_empty_string(payload["stage"], "stage")
    if type(payload["return_code"]) is not int:  # bool is not a process return code.
        raise StageFailureContractError("return_code must be an integer")
    if payload["return_code"] == 0:
        raise StageFailureContractError("return_code must be nonzero for a failure")
    _require_non_empty_string(payload["error_type"], "error_type")
    if not isinstance(payload["error"], str):
        raise StageFailureContractError("error must be a string")
    _require_non_empty_string(payload["source"], "source")


@dataclass(frozen=True)
class StageFailureEnvelope:
    schema_version: int
    stage: str
    return_code: int
    error_type: str
    error: str
    source: str

    @classmethod
    def create(
        cls,
        *,
        stage: str,
        return_code: int,
        error_type: str,
        error: str,
        source: str,
    ) -> StageFailureEnvelope:
        return cls.from_dict(
            {
                "schema_version": SCHEMA_VERSION,
                "stage": stage,
                "return_code": return_code,
                "error_type": error_type,
                "error": error,
                "source": source,
            }
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StageFailureEnvelope:
        _validate_payload(payload)
        return cls(
            schema_version=payload["schema_version"],
            stage=payload["stage"],
            return_code=payload["return_code"],
            error_type=payload["error_type"],
            error=payload["error"],
            source=payload["source"],
        )

    def validate(self) -> None:
        _validate_payload(
            {
                "schema_version": self.schema_version,
                "stage": self.stage,
                "return_code": self.return_code,
                "error_type": self.error_type,
                "error": self.error,
                "source": self.source,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "return_code": self.return_code,
            "error_type": self.error_type,
            "error": self.error,
            "source": self.source,
        }


@dataclass(frozen=True)
class FailedStageEvent:
    stage: str
    return_code: int
    event_index: int


def read_stage_failure(path: str | Path) -> StageFailureEnvelope:
    artifact = Path(path)
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StageFailureReadError(
            f"stage failure artifact does not exist: {artifact}"
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StageFailureReadError(
            f"cannot read stage failure artifact {artifact}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise StageFailureContractError("stage failure envelope must be a JSON object")
    return StageFailureEnvelope.from_dict(payload)


def write_stage_failure_exclusive(
    path: str | Path,
    failure: StageFailureEnvelope | Mapping[str, Any],
) -> None:
    """Atomically publish one complete envelope without replacing a prior one.

    A complete, flushed temporary file is linked into the final path.  The hard
    link is an atomic no-replace operation on the same filesystem: readers see
    either no artifact or the complete artifact, and an existing receipt wins.
    """

    artifact = Path(path)
    envelope = (
        failure
        if isinstance(failure, StageFailureEnvelope)
        else StageFailureEnvelope.from_dict(failure)
    )
    content = (
        json.dumps(
            envelope.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    if not artifact.parent.is_dir():
        raise StageFailureWriteError(
            f"stage failure parent directory does not exist: {artifact.parent}"
        )
    if os.path.lexists(artifact):
        raise StageFailureAlreadyExistsError(
            f"stage failure artifact already exists: {artifact}"
        )

    temporary = artifact.with_name(
        f".{artifact.name}.{os.getpid()}.{uuid.uuid4().hex}.stage-failure-tmp"
    )
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, artifact)
        except FileExistsError as exc:
            raise StageFailureAlreadyExistsError(
                f"stage failure artifact already exists: {artifact}"
            ) from exc
        except OSError as exc:
            raise StageFailureWriteError(
                f"cannot publish stage failure artifact {artifact}: {exc}"
            ) from exc
    except StageFailureContractError:
        raise
    except OSError as exc:
        raise StageFailureWriteError(
            f"cannot write stage failure artifact {artifact}: {exc}"
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)


def find_first_failed_stage(
    events: Iterable[Mapping[str, Any]],
) -> FailedStageEvent | None:
    """Return the first completed stage with a nonzero process return code."""

    if isinstance(events, (str, bytes, Mapping)):
        raise StageFailureContractError(
            "orchestration events must be an iterable of JSON objects"
        )
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise StageFailureContractError(
                f"orchestration event {index} must be a JSON object"
            )
        if event.get("event") != "stage-finished":
            continue
        stage = _require_non_empty_string(event.get("stage"), f"events[{index}].stage")
        return_code = event.get("return_code")
        if type(return_code) is not int:
            raise StageFailureContractError(
                f"events[{index}].return_code must be an integer"
            )
        if return_code != 0:
            return FailedStageEvent(
                stage=stage,
                return_code=return_code,
                event_index=index,
            )
    return None


__all__ = [
    "SCHEMA_VERSION",
    "FailedStageEvent",
    "StageFailureAlreadyExistsError",
    "StageFailureContractError",
    "StageFailureEnvelope",
    "StageFailureReadError",
    "StageFailureWriteError",
    "find_first_failed_stage",
    "read_stage_failure",
    "write_stage_failure_exclusive",
]
