from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageSequence

from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.exec_events import TOOL_EVENT_ITEM_TYPES
from test_case_agent.strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)


class StageBackendError(RuntimeError):
    """A model stage could not complete through the isolated execution backend."""


SUPPORTED_IMAGE_SUFFIXES = frozenset(
    {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_IMAGE_SIGNATURE_READ_BYTES = 4096
_EXPECTED_IMAGE_FORMATS = {
    ".avif": "AVIF",
    ".bmp": "BMP",
    ".gif": "GIF",
    ".jpeg": "JPEG",
    ".jpg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}


@dataclass(frozen=True)
class RegisteredImageInput:
    """One digest-bound image already admitted by the caller's scope registry."""

    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class StageResult:
    payload: dict[str, Any]
    receipt: dict[str, Any]


def _file_sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise StageBackendError(f"cannot read registered image {path}: {exc}") from exc
    return digest.hexdigest(), size


def _has_avif_signature(header: bytes) -> bool:
    """Recognize an AVIF ISO-BMFF ``ftyp`` box without decoding the image."""

    if len(header) < 16 or header[4:8] != b"ftyp":
        return False
    box_size = int.from_bytes(header[:4], "big")
    payload_offset = 8
    if box_size == 1:
        if len(header) < 24:
            return False
        box_size = int.from_bytes(header[8:16], "big")
        payload_offset = 16
    elif box_size == 0:
        box_size = len(header)
    if box_size < payload_offset + 8:
        return False
    payload = header[payload_offset : min(box_size, len(header))]
    if len(payload) < 8:
        return False
    brands = (payload[:4],) + tuple(
        payload[index : index + 4]
        for index in range(8, len(payload) - 3, 4)
    )
    return any(brand in {b"avif", b"avis"} for brand in brands)


def _validate_image_signature(path: Path) -> None:
    """Fail closed unless an admitted image matches its suffix and fully decodes."""

    suffix = path.suffix.casefold()
    try:
        with path.open("rb") as stream:
            header = stream.read(_IMAGE_SIGNATURE_READ_BYTES)
    except OSError as exc:
        raise StageBackendError(f"cannot read registered image {path}: {exc}") from exc

    matches = {
        ".png": lambda value: value.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": lambda value: value.startswith(b"\xff\xd8\xff"),
        ".jpeg": lambda value: value.startswith(b"\xff\xd8\xff"),
        ".gif": lambda value: value.startswith((b"GIF87a", b"GIF89a")),
        ".bmp": lambda value: value.startswith(b"BM"),
        ".webp": lambda value: (
            len(value) >= 12
            and value[:4] == b"RIFF"
            and value[8:12] == b"WEBP"
        ),
        ".avif": _has_avif_signature,
    }
    validator = matches.get(suffix)
    if validator is None:  # pragma: no cover - suffix is checked by the caller
        raise StageBackendError(f"unsupported registered image suffix: {suffix}")
    if not validator(header):
        raise StageBackendError(
            f"registered image has invalid {suffix} signature: {path}"
        )

    expected_format = _EXPECTED_IMAGE_FORMATS[suffix]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as decoded:
                actual_format = decoded.format
                if actual_format != expected_format:
                    raise StageBackendError(
                        "registered image format does not match its suffix: "
                        f"{path} expected={expected_format} "
                        f"actual={actual_format or 'unknown'}"
                    )
                decoded.verify()

            # ``verify`` checks structure but deliberately does not decode pixels.
            # Reopen and load every frame so truncated or corrupt payloads fail.
            with Image.open(path) as decoded:
                actual_format = decoded.format
                if actual_format != expected_format:
                    raise StageBackendError(
                        "registered image format changed while decoding: "
                        f"{path} expected={expected_format} "
                        f"actual={actual_format or 'unknown'}"
                    )
                frame_count = 0
                for frame in ImageSequence.Iterator(decoded):
                    frame.load()
                    frame_count += 1
                if frame_count == 0:  # pragma: no cover - Pillow yields the base frame
                    raise StageBackendError(
                        f"registered image contains no decodable frames: {path}"
                    )
    except StageBackendError:
        raise
    except (
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise StageBackendError(
            f"registered image cannot be fully decoded as {expected_format}: {path}: {exc}"
        ) from exc


def _normalize_registered_images(
    images: tuple[RegisteredImageInput, ...],
) -> tuple[RegisteredImageInput, ...]:
    if not isinstance(images, tuple):
        raise StageBackendError("images must be an immutable tuple")
    normalized: list[RegisteredImageInput] = []
    seen: set[str] = set()
    for index, image in enumerate(images):
        label = f"images[{index}]"
        if not isinstance(image, RegisteredImageInput):
            raise StageBackendError(f"{label} must be RegisteredImageInput")
        if not isinstance(image.path, Path) or not image.path.is_absolute():
            raise StageBackendError(f"{label}.path must be an absolute Path")
        if (
            not isinstance(image.sha256, str)
            or _SHA256_RE.fullmatch(image.sha256) is None
        ):
            raise StageBackendError(f"{label}.sha256 must be lowercase SHA-256")
        if type(image.size_bytes) is not int or image.size_bytes <= 0:
            raise StageBackendError(f"{label}.size_bytes must be a positive integer")
        try:
            resolved = image.path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise StageBackendError(
                f"{label}.path is missing or cannot be resolved: {image.path}"
            ) from exc
        if not resolved.is_file():
            raise StageBackendError(f"{label}.path is not a file: {resolved}")
        if resolved.suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
            raise StageBackendError(
                f"{label}.path has an unsupported image suffix: {resolved.suffix}"
            )
        duplicate_key = os.path.normcase(str(resolved))
        if duplicate_key in seen:
            raise StageBackendError(f"duplicate registered image path: {resolved}")
        seen.add(duplicate_key)
        normalized.append(
            RegisteredImageInput(
                path=resolved,
                sha256=image.sha256,
                size_bytes=image.size_bytes,
            )
        )
    result = tuple(normalized)
    _verify_registered_images(result)
    return result


def verify_registered_image_inputs(
    images: tuple[RegisteredImageInput, ...],
) -> tuple[RegisteredImageInput, ...]:
    """Validate immutable registered images even when no live backend is called."""

    return _normalize_registered_images(images)


def _verify_registered_images(images: tuple[RegisteredImageInput, ...]) -> None:
    for image in images:
        if not image.path.is_file():
            raise StageBackendError(f"registered image is missing: {image.path}")
        actual_sha256, actual_size = _file_sha256_and_size(image.path)
        if actual_size != image.size_bytes or actual_sha256 != image.sha256:
            raise StageBackendError(
                "registered image bytes changed: "
                f"{image.path} expected_sha256={image.sha256} "
                f"actual_sha256={actual_sha256} expected_size={image.size_bytes} "
                f"actual_size={actual_size}"
            )
        _validate_image_signature(image.path)


def _stage_registered_images(
    images: tuple[RegisteredImageInput, ...],
    destination: Path,
) -> tuple[Path, ...]:
    if not images:
        return ()
    destination.mkdir()
    staged: list[Path] = []
    for index, image in enumerate(images):
        staged_path = destination / f"{index:04d}{image.path.suffix.casefold()}"
        digest = hashlib.sha256()
        size = 0
        try:
            with image.path.open("rb") as source, staged_path.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        except OSError as exc:
            raise StageBackendError(
                f"cannot stage registered image {image.path}: {exc}"
            ) from exc
        if digest.hexdigest() != image.sha256 or size != image.size_bytes:
            raise StageBackendError(
                f"registered image changed while staging: {image.path}"
            )
        _validate_image_signature(image.path)
        _validate_image_signature(staged_path)
        staged.append(staged_path)
    return tuple(staged)


def _verify_staged_images(
    staged_paths: tuple[Path, ...],
    images: tuple[RegisteredImageInput, ...],
) -> None:
    if len(staged_paths) != len(images):  # pragma: no cover - internal invariant
        raise StageBackendError("staged image count differs from registered image count")
    for staged_path, image in zip(staged_paths, images, strict=True):
        actual_sha256, actual_size = _file_sha256_and_size(staged_path)
        if actual_sha256 != image.sha256 or actual_size != image.size_bytes:
            raise StageBackendError(
                f"staged image bytes changed during model execution: {image.path}"
            )
        _validate_image_signature(staged_path)


def _usage_from_events(text: str) -> dict[str, Any] | str:
    candidates: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            usage = value.get("usage")
            if isinstance(usage, Mapping):
                candidates.append(dict(usage))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for line in text.splitlines():
        try:
            visit(json.loads(line))
        except json.JSONDecodeError:
            continue
    return candidates[-1] if candidates else "unavailable"


def _tool_event_count(text: str) -> int:
    count = 0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        item = event.get("item")
        if isinstance(item, Mapping) and item.get("type") in TOOL_EVENT_ITEM_TYPES:
            count += 1
    return count


class CodexExecStageBackend:
    """Fresh, tool-free Codex process per stage; no model timeout by default."""

    def __init__(
        self,
        *,
        codex_command: str | None = None,
        timeout_seconds: float | None = None,
        probe_timeout_seconds: float = 15,
    ) -> None:
        self.codex_command = codex_command
        self.timeout_seconds = timeout_seconds
        self.probe_timeout_seconds = probe_timeout_seconds

    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
        images: tuple[RegisteredImageInput, ...] = (),
    ) -> StageResult:
        registered_images = _normalize_registered_images(images)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        schema_path = artifact_dir / f"{stage}-output-schema.json"
        output_path = artifact_dir / f"{stage}-response.json"
        events_path = artifact_dir / f"{stage}-events.jsonl"
        stderr_path = artifact_dir / f"{stage}-stderr.txt"
        reserved_paths = {
            os.path.normcase(str(path.resolve()))
            for path in (schema_path, output_path, events_path, stderr_path)
        }
        overlap = [
            image.path
            for image in registered_images
            if os.path.normcase(str(image.path)) in reserved_paths
        ]
        if overlap:
            raise StageBackendError(
                f"registered image overlaps backend artifact path: {overlap[0]}"
            )
        try:
            validate_openai_strict_output_schema(schema)
        except ValueError as exc:
            raise StageBackendError(f"{stage} output schema is invalid: {exc}") from exc
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        schema_bytes = schema_path.stat().st_size
        prompt_bytes = len(prompt.encode("utf-8"))
        required_flags = [
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--color",
        ]
        if registered_images:
            required_flags.append("--image")
        resolution = resolve_verified_exec_capability(
            self.codex_command,
            total_timeout_seconds=self.probe_timeout_seconds,
            additional_required_flags=tuple(required_flags),
            required_disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
        )
        _verify_registered_images(registered_images)
        if not resolution.verified:
            capability = resolution.selection_capability()
            raise StageBackendError(
                "no verified codex exec backend: "
                + (capability.error or ", ".join(capability.missing_flags))
            )
        started = time.perf_counter_ns()
        with tempfile.TemporaryDirectory(prefix=f"stage-{stage}-") as raw_cwd:
            staged_images = _stage_registered_images(
                registered_images,
                Path(raw_cwd) / "registered-images",
            )
            _verify_registered_images(registered_images)
            command = [
                resolution.selected_executable,
                "exec",
                "--cd",
                raw_cwd,
                *resolution.disable_args,
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "--json",
                "--output-schema",
                str(schema_path.resolve()),
                "--output-last-message",
                str(output_path.resolve()),
                "--color",
                "never",
            ]
            for image_path in staged_images:
                command.extend(("--image", str(image_path)))
            command.append("-")
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=raw_cwd,
                    env=env,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                _verify_registered_images(registered_images)
                _verify_staged_images(staged_images, registered_images)
                raise StageBackendError(
                    f"{stage} exceeded explicit timeout {self.timeout_seconds}s"
                ) from exc
            except (OSError, subprocess.SubprocessError) as exc:
                _verify_registered_images(registered_images)
                _verify_staged_images(staged_images, registered_images)
                raise StageBackendError(f"{stage} process failed: {exc}") from exc
            _verify_registered_images(registered_images)
            _verify_staged_images(staged_images, registered_images)
        duration_ms = (time.perf_counter_ns() - started) // 1_000_000
        events_path.write_text(completed.stdout, encoding="utf-8", newline="\n")
        stderr_path.write_text(completed.stderr, encoding="utf-8", newline="\n")
        tool_events = _tool_event_count(completed.stdout)
        if completed.returncode != 0:
            raise StageBackendError(
                f"{stage} codex exec exited with code {completed.returncode}: "
                f"{completed.stderr[-1000:]}"
            )
        if tool_events:
            raise StageBackendError(f"{stage} emitted {tool_events} forbidden tool events")
        if not output_path.is_file() or not output_path.stat().st_size:
            raise StageBackendError(f"{stage} completed without structured output")
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StageBackendError(f"{stage} output is not JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise StageBackendError(f"{stage} output must be a JSON object")
        try:
            validate_openai_strict_output_instance(payload, schema)
        except ValueError as exc:
            raise StageBackendError(
                f"{stage} output failed strict schema validation: {exc}"
            ) from exc
        return StageResult(
            payload=payload,
            receipt={
                "stage": stage,
                "backend": "codex-exec-tool-free",
                "attempts": 1,
                "duration_ms": duration_ms,
                "capability_probe_ms": resolution.duration_ms,
                "tokens": _usage_from_events(completed.stdout),
                "tool_event_count": tool_events,
                "codex_version": resolution.selected.version if resolution.selected else "",
                "timeout_seconds": self.timeout_seconds,
                "image_attachments": {
                    "count": len(registered_images),
                    "bytes": sum(image.size_bytes for image in registered_images),
                },
                "input_artifacts": {
                    "count": 2 + len(registered_images),
                    "bytes": (
                        prompt_bytes
                        + schema_bytes
                        + sum(image.size_bytes for image in registered_images)
                    ),
                },
                "output_artifacts": {
                    "count": 3,
                    "bytes": (
                        output_path.stat().st_size
                        + events_path.stat().st_size
                        + stderr_path.stat().st_size
                    ),
                },
            },
        )
