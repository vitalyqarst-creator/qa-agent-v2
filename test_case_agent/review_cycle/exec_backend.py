from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Mapping, Sequence


REQUIRED_EXEC_HELP_FLAGS = (
    "--sandbox",
    "--cd",
    "--json",
    "--output-schema",
    "--output-last-message",
)

PLUGIN_ISOLATION_DISABLE_FEATURES = (
    "remote_plugin",
    "plugins",
    "apps",
)

MODEL_TOOL_ISOLATION_DISABLE_FEATURES = (
    *PLUGIN_ISOLATION_DISABLE_FEATURES,
    "shell_tool",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "computer_use",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "workspace_dependencies",
    "goals",
    "skill_search",
    "skill_mcp_dependency_install",
    "tool_suggest",
)


@dataclass(frozen=True)
class ExecCapability:
    command: str
    available: bool
    verified: bool
    returncode: int | None
    duration_ms: int
    missing_flags: tuple[str, ...]
    error: str = ""
    version: str = ""
    resolved_command: str = ""


AnyProbe = Callable[..., ExecCapability]


@dataclass(frozen=True)
class ExecCapabilityResolution:
    requested_command: str
    probes: tuple[ExecCapability, ...]
    selected: ExecCapability | None
    disable_features: tuple[str, ...] = ()
    duration_ms: int = 0

    @property
    def verified(self) -> bool:
        return self.selected is not None and _verified_postcondition(self.selected) is None

    @property
    def total_duration_ms(self) -> int:
        return self.duration_ms or sum(probe.duration_ms for probe in self.probes)

    @property
    def selected_executable(self) -> str:
        if self.selected is None or _verified_postcondition(self.selected) is not None:
            return ""
        return str(Path(self.selected.resolved_command).resolve())

    @property
    def disable_args(self) -> tuple[str, ...]:
        result: list[str] = []
        for feature in self.disable_features:
            result.extend(("--disable", feature))
        return tuple(result)

    def selection_capability(self) -> ExecCapability:
        if self.selected is not None:
            postcondition_error = _verified_postcondition(self.selected)
            if postcondition_error is None:
                return self.selected
            return replace(
                self.selected,
                verified=False,
                error=postcondition_error,
            )
        commands = [probe.command for probe in self.probes]
        errors = [
            f"{probe.command}: {probe.error or 'missing ' + ', '.join(probe.missing_flags)}"
            for probe in self.probes
        ]
        missing = tuple(
            dict.fromkeys(
                flag
                for probe in self.probes
                for flag in probe.missing_flags
            )
        )
        return ExecCapability(
            command=self.requested_command or (commands[0] if commands else "codex"),
            available=any(probe.available for probe in self.probes),
            verified=False,
            returncode=None,
            duration_ms=sum(probe.duration_ms for probe in self.probes),
            missing_flags=missing,
            error="; ".join(errors) or "no codex exec candidates were available",
        )


def default_exec_candidates(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> tuple[str, ...]:
    values = os.environ if environ is None else environ
    candidates: list[str] = []
    configured = values.get("CODEX_EXEC_COMMAND", "").strip()
    if configured:
        candidates.append(configured)
    user_home = Path.home() if home is None else home
    candidates.append(str(user_home / ".codex" / "plugins" / ".plugin-appserver" / "codex.exe"))
    discovered = shutil.which("codex")
    if discovered:
        candidates.append(discovered)
    return _deduplicate_candidates(candidates)


def resolve_exec_command(explicit: str | None = None) -> str:
    candidates = (explicit,) if explicit else default_exec_candidates()
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        discovered = shutil.which(candidate)
        if path.is_file() or discovered:
            return str(path if path.is_file() else discovered or candidate)
    return str(candidates[0]) if candidates else "codex"


def probe_exec_capability(
    command: str,
    *,
    timeout_seconds: float | None = 15,
    additional_required_flags: Sequence[str] = (),
    required_disable_features: Sequence[str] = (),
) -> ExecCapability:
    started = time.perf_counter()
    deadline = None if timeout_seconds is None else started + timeout_seconds
    disable_features = _validated_disable_features(required_disable_features)
    required_flags = tuple(
        dict.fromkeys(
            (
                *REQUIRED_EXEC_HELP_FLAGS,
                *additional_required_flags,
                *(('--disable',) if disable_features else ()),
            )
        )
    )
    resolved = _resolved_command(command)
    if timeout_seconds is not None and timeout_seconds <= 0:
        return ExecCapability(
            command=command,
            available=False,
            verified=False,
            returncode=None,
            duration_ms=0,
            missing_flags=required_flags,
            error="codex exec capability probe budget exhausted",
            resolved_command=resolved,
        )
    try:
        if disable_features:
            feature_result = subprocess.run(
                [resolved, "features", "list"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_remaining_seconds(deadline),
                check=False,
            )
            feature_names = {
                line.split()[0]
                for line in feature_result.stdout.splitlines()
                if line.split()
            }
            unsupported = tuple(
                feature for feature in disable_features if feature not in feature_names
            )
            if feature_result.returncode != 0 or unsupported:
                detail = (
                    feature_result.stdout
                    or feature_result.stderr
                    or "feature registry unavailable"
                ).strip()
                error = (
                    "unsupported disable features: " + ", ".join(unsupported)
                    if unsupported
                    else f"codex features list failed: {detail[-1000:]}"
                )
                return ExecCapability(
                    command=command,
                    available=feature_result.returncode == 0,
                    verified=False,
                    returncode=feature_result.returncode,
                    duration_ms=_elapsed_ms(started),
                    missing_flags=(),
                    error=error,
                    resolved_command=resolved,
                )
        completed = subprocess.run(
            [resolved, "exec", *plugin_isolation_exec_args(disable_features), "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_remaining_seconds(deadline),
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ExecCapability(
            command=command,
            available=False,
            verified=False,
            returncode=None,
            duration_ms=_elapsed_ms(started),
            missing_flags=required_flags,
            error=str(exc),
            resolved_command=resolved,
        )
    help_text = f"{completed.stdout}\n{completed.stderr}"
    missing = tuple(flag for flag in required_flags if flag not in help_text)
    if completed.returncode != 0 or missing:
        return ExecCapability(
            command=command,
            available=completed.returncode == 0,
            verified=False,
            returncode=completed.returncode,
            duration_ms=_elapsed_ms(started),
            missing_flags=missing,
            error="" if completed.returncode == 0 else help_text[-1000:].strip(),
            resolved_command=resolved,
        )
    try:
        version_result = subprocess.run(
            [resolved, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_remaining_seconds(deadline),
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ExecCapability(
            command=command,
            available=True,
            verified=False,
            returncode=completed.returncode,
            duration_ms=_elapsed_ms(started),
            missing_flags=(),
            error=f"codex --version failed: {exc}",
            resolved_command=resolved,
        )
    version = version_result.stdout.strip()
    if version_result.returncode != 0 or not version:
        detail = (version_result.stdout or version_result.stderr or "no version text").strip()
        return ExecCapability(
            command=command,
            available=True,
            verified=False,
            returncode=version_result.returncode,
            duration_ms=_elapsed_ms(started),
            missing_flags=(),
            error=f"codex --version probe failed: {detail[-1000:]}",
            resolved_command=resolved,
        )
    return ExecCapability(
        command=command,
        available=True,
        verified=True,
        returncode=completed.returncode,
        duration_ms=_elapsed_ms(started),
        missing_flags=(),
        version=version,
        resolved_command=resolved,
    )


def resolve_verified_exec_capability(
    explicit: str | None = None,
    *,
    candidates: Sequence[str] | None = None,
    total_timeout_seconds: float | None = 15,
    additional_required_flags: Sequence[str] = (),
    required_disable_features: Sequence[str] = (),
    probe: AnyProbe | None = None,
) -> ExecCapabilityResolution:
    if total_timeout_seconds is not None and total_timeout_seconds <= 0:
        raise ValueError("total_timeout_seconds must be positive")
    disable_features = _validated_disable_features(required_disable_features)
    required_flags = tuple(
        dict.fromkeys(
            (*additional_required_flags, *(('--disable',) if disable_features else ()))
        )
    )
    if explicit:
        commands = (explicit,)
    elif candidates is not None:
        commands = _deduplicate_candidates(candidates)
    else:
        commands = default_exec_candidates()
    started = time.perf_counter()
    deadline = (
        None
        if total_timeout_seconds is None
        else started + total_timeout_seconds
    )
    probe_function = probe_exec_capability if probe is None else probe
    probes: list[ExecCapability] = []
    for command in commands:
        remaining = (
            None if deadline is None else deadline - time.perf_counter()
        )
        if remaining is not None and remaining <= 0:
            probes.append(
                ExecCapability(
                    command=command,
                    available=False,
                    verified=False,
                    returncode=None,
                    duration_ms=0,
                    missing_flags=required_flags,
                    error="shared codex exec capability probe budget exhausted",
                    resolved_command=_resolved_command(command),
                )
            )
            break
        capability = probe_function(
            command,
            timeout_seconds=remaining,
            additional_required_flags=required_flags,
            required_disable_features=disable_features,
        )
        postcondition_error = _verified_postcondition(capability)
        if capability.verified and postcondition_error is not None:
            capability = replace(
                capability,
                verified=False,
                error=postcondition_error,
            )
        probes.append(capability)
        if capability.verified:
            return ExecCapabilityResolution(
                requested_command=explicit or "",
                probes=tuple(probes),
                selected=capability,
                disable_features=disable_features,
                duration_ms=_elapsed_ms(started),
            )
    return ExecCapabilityResolution(
        requested_command=explicit or "",
        probes=tuple(probes),
        selected=None,
        disable_features=disable_features,
        duration_ms=_elapsed_ms(started),
    )


def plugin_isolation_exec_args(
    features: Sequence[str] = PLUGIN_ISOLATION_DISABLE_FEATURES,
) -> tuple[str, ...]:
    normalized = _validated_disable_features(features)
    result: list[str] = []
    for feature in normalized:
        result.extend(("--disable", feature))
    return tuple(result)


def tool_free_exec_args() -> tuple[str, ...]:
    """Return the fail-closed model-tool isolation arguments."""

    return plugin_isolation_exec_args(MODEL_TOOL_ISOLATION_DISABLE_FEATURES)


def _resolved_command(command: str) -> str:
    path = Path(command)
    if path.is_file():
        return str(path.resolve())
    discovered = shutil.which(command)
    if discovered:
        return str(Path(discovered).resolve())
    return command


def _deduplicate_candidates(candidates: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = str(candidate).strip()
        if not value:
            continue
        resolved = _resolved_command(value)
        key = (
            os.path.normcase(os.path.abspath(resolved))
            if Path(resolved).is_absolute()
            else resolved.casefold()
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return tuple(result)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise subprocess.TimeoutExpired("codex exec capability probe", 0)
    return remaining


def _validated_disable_features(features: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", feature):
            raise ValueError("disable features must be non-empty CLI identifiers")
        if feature not in seen:
            seen.add(feature)
            result.append(feature)
    return tuple(result)


def _verified_postcondition(capability: ExecCapability) -> str | None:
    if not capability.verified:
        return "capability probe did not verify the executable"
    if not capability.version.strip():
        return "verified codex exec capability did not pin a non-empty version"
    resolved = capability.resolved_command.strip()
    if not resolved or not Path(resolved).is_absolute():
        return "verified codex exec capability did not pin an absolute executable"
    return None


__all__ = [
    "ExecCapability",
    "ExecCapabilityResolution",
    "REQUIRED_EXEC_HELP_FLAGS",
    "PLUGIN_ISOLATION_DISABLE_FEATURES",
    "MODEL_TOOL_ISOLATION_DISABLE_FEATURES",
    "default_exec_candidates",
    "plugin_isolation_exec_args",
    "probe_exec_capability",
    "resolve_exec_command",
    "resolve_verified_exec_capability",
    "tool_free_exec_args",
]
