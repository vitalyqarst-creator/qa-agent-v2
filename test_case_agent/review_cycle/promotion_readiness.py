from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .runtime import StageRuntimeError


SHA256 = re.compile(r"[0-9a-f]{64}")
TC_ID = re.compile(r"TC-[A-Za-z0-9][A-Za-z0-9_.-]*")


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageRuntimeError(f"promotion contract {name} must be non-empty text")
    return value.strip()


def _path(value: Any, name: str) -> str:
    text = _text(value, name)
    parsed = PurePosixPath(text)
    if parsed.as_posix() != text or any(part in {"", ".", ".."} for part in parsed.parts):
        raise StageRuntimeError(f"promotion contract {name} must be a normalized relative path")
    return text


def _strings(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise StageRuntimeError(f"promotion contract {name} must be a non-empty array")
    result = tuple(_text(item, f"{name}[]") for item in value)
    if len(result) != len(set(result)):
        raise StageRuntimeError(f"promotion contract {name} must not contain duplicates")
    return result


@dataclass(frozen=True)
class PromotionContract:
    contract_version: int
    canonical_test_cases: str
    canonical_title: str
    ft_slug: str
    scope_slug: str
    section_id: str
    domain_package_id: str
    test_design_dir: str
    test_case_ids: tuple[str, ...]
    expected_priorities: Mapping[str, str]
    required_requirement_ids: tuple[str, ...]
    required_sections: tuple[str, ...]
    required_gap_ids: tuple[str, ...]
    accepted_candidate: str
    accepted_candidate_sha256: str

    @classmethod
    def load(cls, path: Path, repo_root: Path) -> "PromotionContract":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StageRuntimeError(f"cannot load promotion contract: {exc}") from exc
        expected = {
            "contract_version", "canonical_test_cases", "canonical_title", "ft_slug",
            "scope_slug", "section_id", "domain_package_id", "test_case_ids",
            "test_design_dir", "expected_priorities", "required_requirement_ids",
            "required_sections", "required_gap_ids", "accepted_candidate",
            "accepted_candidate_sha256",
        }
        if not isinstance(payload, Mapping) or set(payload) != expected:
            raise StageRuntimeError("promotion contract has invalid fields")
        contract = cls(
            contract_version=payload["contract_version"],
            canonical_test_cases=_path(payload["canonical_test_cases"], "canonical_test_cases"),
            canonical_title=_text(payload["canonical_title"], "canonical_title"),
            ft_slug=_text(payload["ft_slug"], "ft_slug"),
            scope_slug=_text(payload["scope_slug"], "scope_slug"),
            section_id=_text(payload["section_id"], "section_id"),
            domain_package_id=_text(payload["domain_package_id"], "domain_package_id"),
            test_design_dir=_path(payload["test_design_dir"], "test_design_dir"),
            test_case_ids=_strings(payload["test_case_ids"], "test_case_ids"),
            expected_priorities=dict(payload["expected_priorities"]),
            required_requirement_ids=_strings(
                payload["required_requirement_ids"], "required_requirement_ids"
            ),
            required_sections=_strings(payload["required_sections"], "required_sections"),
            required_gap_ids=_strings(payload["required_gap_ids"], "required_gap_ids"),
            accepted_candidate=_path(payload["accepted_candidate"], "accepted_candidate"),
            accepted_candidate_sha256=_text(
                payload["accepted_candidate_sha256"], "accepted_candidate_sha256"
            ),
        )
        contract.validate(repo_root)
        return contract

    def validate(self, repo_root: Path) -> None:
        if self.contract_version != 1:
            raise StageRuntimeError("promotion contract_version must be 1")
        if any(not TC_ID.fullmatch(value) for value in self.test_case_ids):
            raise StageRuntimeError("promotion contract test_case_ids contain invalid ids")
        if set(self.expected_priorities) != set(self.test_case_ids):
            raise StageRuntimeError("promotion contract expected_priorities must cover every test case")
        if any(value not in {"High", "Medium", "Low"} for value in self.expected_priorities.values()):
            raise StageRuntimeError("promotion contract expected_priorities contain invalid values")
        if not SHA256.fullmatch(self.accepted_candidate_sha256):
            raise StageRuntimeError("promotion contract accepted_candidate_sha256 is invalid")
        candidate = (repo_root / self.accepted_candidate).resolve()
        try:
            candidate.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise StageRuntimeError("promotion accepted candidate escapes repository") from exc
        if not candidate.is_file():
            raise StageRuntimeError("promotion accepted candidate is missing")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != self.accepted_candidate_sha256:
            raise StageRuntimeError("promotion accepted candidate SHA-256 mismatch")


@dataclass(frozen=True)
class PromotionReadinessReport:
    passed: bool
    findings: tuple[dict[str, str], ...]
    checked_paths: tuple[str, ...]
    validator: str = "prepared-promotion-readiness-v1"

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": self.validator,
            "checked_paths": list(self.checked_paths),
            "findings": list(self.findings),
        }


def validate_promotion_readiness(
    *, draft_path: Path, contract: PromotionContract
) -> PromotionReadinessReport:
    text = draft_path.read_text(encoding="utf-8")
    findings: list[dict[str, str]] = []

    def add(finding_id: str, message: str) -> None:
        findings.append({"id": finding_id, "severity": "error", "message": message})

    if not text.startswith(f"# {contract.canonical_title}\n"):
        add("canonical-title-mismatch", "Draft does not start with the canonical title.")
    for section in contract.required_sections:
        if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, flags=re.MULTILINE):
            add("missing-canonical-section", f"Draft is missing canonical section: {section}")
    actual_ids = tuple(
        re.findall(r"^##\s+(TC-[A-Za-z0-9][A-Za-z0-9_.-]*)\s*$", text, flags=re.MULTILINE)
    )
    if actual_ids != contract.test_case_ids:
        add(
            "canonical-test-case-ids-mismatch",
            f"Expected ordered ids {contract.test_case_ids}, found {actual_ids}.",
        )
    if "TC-PREP-" in text:
        add("temporary-test-case-id", "Draft still contains a TC-PREP identifier.")
    for tc_id in contract.test_case_ids:
        match = re.search(
            rf"^##\s+{re.escape(tc_id)}\s*$([\s\S]*?)(?=^##\s+TC-|\Z)",
            text,
            flags=re.MULTILINE,
        )
        if match and not re.search(
            rf"\*\*package_id:\*\*\s*`?{re.escape(contract.domain_package_id)}`?",
            match.group(1),
        ):
            add("canonical-package-id-mismatch", f"{tc_id} does not use the canonical package_id.")
    metadata = {
        "ft_slug": contract.ft_slug,
        "scope_slug": contract.scope_slug,
        "section_id": contract.section_id,
        "package_id": contract.domain_package_id,
        "test_design_dir": contract.test_design_dir,
    }
    for field, value in metadata.items():
        if not re.search(
            rf"^\|\s*{re.escape(field)}\s*\|\s*`?{re.escape(value)}`?\s*\|\s*$",
            text,
            flags=re.MULTILINE,
        ):
            add("canonical-metadata-mismatch", f"Metadata does not bind {field}={value}.")
    for gap_id in contract.required_gap_ids:
        if not re.search(rf"\b{re.escape(gap_id)}\b", text):
            add("required-gap-missing", f"Draft does not preserve {gap_id}.")
    for requirement_id in contract.required_requirement_ids:
        if not re.search(rf"\b{re.escape(requirement_id)}\b", text):
            add("required-requirement-id-missing", f"Draft does not preserve {requirement_id}.")
    for tc_id, priority in contract.expected_priorities.items():
        match = re.search(
            rf"^##\s+{re.escape(tc_id)}\s*$([\s\S]*?)(?=^##\s+TC-|\Z)",
            text,
            flags=re.MULTILINE,
        )
        if match and not re.search(
            rf"\*\*Приоритет:\*\*\s*{re.escape(priority)}\s*$",
            match.group(1),
            flags=re.MULTILINE,
        ):
            add("canonical-priority-mismatch", f"{tc_id} must use priority {priority}.")
    return PromotionReadinessReport(
        passed=not findings,
        findings=tuple(findings),
        checked_paths=(str(draft_path), contract.canonical_test_cases, contract.accepted_candidate),
    )
