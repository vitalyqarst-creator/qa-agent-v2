from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

from test_case_agent.review_cycle.prepared_package import SourceRegistryEntry


def _normalized(value: str) -> str:
    return value.replace("\\", "/").lower()


@dataclass(frozen=True)
class EvidenceAccessResult:
    passed: bool
    commands_checked: int
    fallback_authorizations: int
    accesses: tuple[dict[str, Any], ...]
    findings: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": "prepared-evidence-access-gate-v1",
            "commands_checked": self.commands_checked,
            "fallback_authorizations": self.fallback_authorizations,
            "accesses": list(self.accesses),
            "findings": list(self.findings),
        }


def validate_evidence_access(
    *,
    events_text: str,
    forbidden_roots: Sequence[str],
    source_registry: Sequence[SourceRegistryEntry],
    allowed_command_fragments: Sequence[str] = (),
    reject_unlisted_commands: bool = False,
) -> EvidenceAccessResult:
    fallback_messages: list[str] = []
    commands: list[tuple[str, str, tuple[str, ...]]] = []
    seen_commands: set[str] = set()

    for raw_line in events_text.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type in {"agent_message", "message"}:
            text = item.get("text") or item.get("content") or item.get("message")
            if isinstance(text, str) and "targeted_source_fallback" in text:
                fallback_messages.append(_normalized(text))
        if item_type != "command_execution":
            continue
        command = item.get("command")
        if not isinstance(command, str) or not command.strip():
            continue
        command_id = str(item.get("id") or command)
        if command_id in seen_commands:
            continue
        seen_commands.add(command_id)
        commands.append((command_id, command, tuple(fallback_messages)))

    findings: list[dict[str, Any]] = []
    accesses: list[dict[str, Any]] = []
    normalized_forbidden = [(_normalized(path), path) for path in forbidden_roots]
    normalized_allowed = tuple(_normalized(item) for item in allowed_command_fragments)

    for command_id, command, command_fallbacks in commands:
        normalized_command = _normalized(command)
        if reject_unlisted_commands and not any(
            allowed in normalized_command for allowed in normalized_allowed
        ):
            findings.append(
                {
                    "id": "unapproved-prepared-stage-command",
                    "severity": "error",
                    "command_id": command_id,
                    "message": "Prepared stage executed a command outside its explicit allowlist.",
                }
            )
        for root, original_root in normalized_forbidden:
            if root in normalized_command:
                findings.append(
                    {
                        "id": "forbidden-evidence-root-access",
                        "severity": "error",
                        "command_id": command_id,
                        "path": original_root,
                        "message": "Prepared stage command accessed a forbidden evidence root.",
                    }
                )
        broad_scan = (
            "rg --files" in normalized_command
            and not any(scope in normalized_command for scope in ("prepared-input", "runner-input"))
        ) or (
            "get-childitem" in normalized_command
            and "-recurse" in normalized_command
            and not any(scope in normalized_command for scope in ("prepared-input", "runner-input"))
        )
        if broad_scan:
            findings.append(
                {
                    "id": "unbounded-prepared-stage-scan",
                    "severity": "error",
                    "command_id": command_id,
                    "message": "Prepared stage used a broad filesystem scan outside prepared inputs.",
                }
            )
        for source in source_registry:
            source_path = _normalized(source.path)
            if source_path not in normalized_command:
                continue
            locator = _normalized(source.locator)
            authorized = any(
                source_path in message and locator in message for message in command_fallbacks
            )
            accesses.append(
                {
                    "command_id": command_id,
                    "path": source.path,
                    "locator": source.locator,
                    "authorized": authorized,
                }
            )
            if not authorized:
                findings.append(
                    {
                        "id": "unapproved-full-source-access",
                        "severity": "error",
                        "command_id": command_id,
                        "path": source.path,
                        "locator": source.locator,
                        "message": "Registered full source was accessed without exact targeted fallback authorization.",
                    }
                )

    return EvidenceAccessResult(
        passed=not findings,
        commands_checked=len(commands),
        fallback_authorizations=len(fallback_messages),
        accesses=tuple(accesses),
        findings=tuple(findings),
    )
