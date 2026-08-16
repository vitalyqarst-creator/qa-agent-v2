from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "test-data-source-plan-v2"
PROVIDER_PROFILES: dict[str, dict[str, Any]] = {
    "source-literal": {"evidence": {"source-literal"}, "adapter": None},
    "package-dictionary": {"evidence": {"closed-dictionary-value"}, "adapter": None},
    "dadata-suggestions": {
        "evidence": {"integration-response", "business-valid-entity"},
        "adapter": "scripts/verify_dadata_positive_fixture.py",
        "integration": "dadata",
        "capabilities": {
            "party": {
                "party.suggestion", "party.name", "party.inn", "party.ogrn",
                "party.kpp", "party.legal_address",
            },
            "address": {
                "address.suggestion", "address.value", "address.city",
                "address.kladr_id",
            },
        },
    },
    "randomdatatools-synthetic": {
        "evidence": {"neutral-format-value"},
        "adapter": "scripts/create_randomdatatools_synthetic_fixture.py"},
    "local-binary-fixture": {
        "evidence": {"binary-file-artifact"},
        "adapter": "scripts/create_binary_file_fixture.py",
        "capabilities": {
            "file": {
                "file.jpg", "file.png", "file.pdf", "file.txt",
                "file.exact-size-bytes",
            },
        },
    },
    "test-environment-setup": {"evidence": {"environment-state"}, "adapter": None},
}


class TestDataPlanError(ValueError):
    pass


def _safe_artifact_path(artifact_root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw_path = Path(value)
    if raw_path.is_absolute():
        return None
    root = artifact_root.resolve()
    candidate = (root / raw_path).resolve()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate


def _json_pointer(payload: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise TestDataPlanError("evidence path must start with '/'")
    current = payload
    for raw_segment in pointer.split("/")[1:]:
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not segment.isdigit() or int(segment) >= len(current):
                raise TestDataPlanError("evidence path does not exist")
            current = current[int(segment)]
        elif isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            raise TestDataPlanError("evidence path does not exist")
    return current


def recommend_source(required_evidence: str, *, integration: str | None = None,
                     existing_fixture_source: str | None = None) -> str:
    if existing_fixture_source:
        return existing_fixture_source
    fixed = {"source-literal": "source-literal",
             "closed-dictionary-value": "package-dictionary",
             "environment-state": "test-environment-setup",
             "neutral-format-value": "randomdatatools-synthetic"}
    if required_evidence in fixed:
        return fixed[required_evidence]
    if integration:
        matches = [name for name, profile in PROVIDER_PROFILES.items()
                   if profile.get("integration") == integration.lower()
                   and required_evidence in profile["evidence"]]
        if len(matches) == 1:
            return matches[0]
    raise TestDataPlanError(f"Нет зарегистрированного источника для evidence={required_evidence!r}")


def register_provider(name: str, *, evidence: set[str], adapter: str,
                      integration: str | None = None) -> None:
    if not name or not evidence or not adapter:
        raise TestDataPlanError("Профиль provider-а требует name, evidence и adapter")
    PROVIDER_PROFILES[name] = {"evidence": set(evidence), "adapter": adapter,
                               **({"integration": integration.lower()} if integration else {})}


def validate_plan(
    plan: dict[str, Any], *, repo_root: Path | None = None, artifact_root: Path | None = None
) -> list[str]:
    errors: list[str] = []
    if plan.get("contract_version") != CONTRACT_VERSION:
        errors.append("Некорректная contract_version")
    if not plan.get("scope_slug"):
        errors.append("Не указан scope_slug")
    sha = plan.get("matrix_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(char not in "0123456789abcdef" for char in sha.lower()):
        errors.append("matrix_sha256 должен содержать 64 hex-символа")
    items = plan.get("items")
    if not isinstance(items, list):
        return errors + ["items должен быть массивом"]
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        prefix = f"items[{index}]"
        item_id = item.get("id")
        if not item_id or item_id in seen:
            errors.append(f"{prefix}: отсутствует или повторяется id")
        seen.add(item_id)
        evidence, source = item.get("required_evidence"), item.get("selected_source")
        profile = PROVIDER_PROFILES.get(source)
        if profile is None:
            errors.append(f"{prefix}: provider {source!r} не зарегистрирован")
        elif evidence not in profile["evidence"]:
            errors.append(f"{prefix}: provider {source!r} не доказывает {evidence!r}")
        elif repo_root and profile.get("adapter") and not (repo_root / profile["adapter"]).is_file():
            errors.append(f"{prefix}: adapter {profile['adapter']!r} не найден")

        required_properties = item.get("required_properties")
        if not isinstance(required_properties, list) or not required_properties or any(
            not isinstance(value, str) or not value.strip() for value in required_properties
        ):
            errors.append(f"{prefix}: required_properties должен быть непустым списком свойств")

        provider_context = item.get("provider_context")
        required_capabilities = item.get("required_capabilities")
        capabilities_by_context = profile.get("capabilities", {}) if profile else {}
        unsupported_capabilities: set[str] = set()
        if capabilities_by_context:
            if not isinstance(provider_context, str) or provider_context not in capabilities_by_context:
                errors.append(f"{prefix}: для provider-а {source!r} не указан допустимый provider_context")
            if not isinstance(required_capabilities, list) or not required_capabilities or any(
                not isinstance(value, str) or not value.strip() for value in required_capabilities
            ):
                errors.append(f"{prefix}: для provider-а {source!r} required_capabilities обязателен")
            elif provider_context in capabilities_by_context:
                unsupported_capabilities = set(required_capabilities) - set(
                    capabilities_by_context[provider_context]
                )
        status = item.get("materialization_status")
        if status not in {"not-required", "pending", "materialized", "blocked"}:
            errors.append(f"{prefix}: некорректный materialization_status")
        if status == "materialized":
            for field in ("fixture_id", "snapshot_path", "receipt_path"):
                if not item.get(field):
                    errors.append(f"{prefix}: materialized требует {field}")
            item_sha = item.get("snapshot_sha256")
            if not isinstance(item_sha, str) or len(item_sha) != 64:
                errors.append(f"{prefix}: materialized требует snapshot_sha256")
            bindings = item.get("evidence_bindings")
            if not isinstance(bindings, list) or not bindings:
                errors.append(f"{prefix}: materialized требует evidence_bindings")
            else:
                bound_properties = {
                    binding.get("required_property")
                    for binding in bindings
                    if isinstance(binding, dict)
                    and isinstance(binding.get("required_property"), str)
                    and isinstance(binding.get("evidence_path"), str)
                    and binding.get("evidence_path").strip()
                    and "verified_value" in binding
                }
                if isinstance(required_properties, list) and set(required_properties) - bound_properties:
                    errors.append(
                        f"{prefix}: evidence_bindings не подтверждает все required_properties"
                    )
                if artifact_root:
                    snapshot_path = _safe_artifact_path(artifact_root, item.get("snapshot_path"))
                    receipt_path = _safe_artifact_path(artifact_root, item.get("receipt_path"))
                    if snapshot_path is None or receipt_path is None:
                        errors.append(f"{prefix}: snapshot_path и receipt_path должны быть относительными путями scope")
                    elif not snapshot_path.is_file() or not receipt_path.is_file():
                        errors.append(f"{prefix}: materialized evidence files не найдены")
                    else:
                        actual_sha256 = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
                        if actual_sha256 != item.get("snapshot_sha256"):
                            errors.append(f"{prefix}: snapshot_sha256 не совпадает с файлом snapshot")
                        try:
                            receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
                        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                            errors.append(f"{prefix}: receipt_path не содержит корректный UTF-8 JSON")
                            receipt_payload = None
                        if isinstance(receipt_payload, dict):
                            if receipt_payload.get("fixture_id") != item.get("fixture_id"):
                                errors.append(f"{prefix}: fixture_id receipt не совпадает с plan")
                            try:
                                snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
                            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                                snapshot_payload = None
                            for binding in bindings:
                                if not isinstance(binding, dict):
                                    continue
                                evidence_path = binding.get("evidence_path")
                                if not isinstance(evidence_path, str) or ":" not in evidence_path:
                                    errors.append(f"{prefix}: evidence_path должен иметь вид snapshot:/... или receipt:/...")
                                    continue
                                source_name, pointer = evidence_path.split(":", 1)
                                payload = snapshot_payload if source_name == "snapshot" else receipt_payload if source_name == "receipt" else None
                                if payload is None:
                                    errors.append(f"{prefix}: evidence_path указывает на недоступный {source_name}")
                                    continue
                                try:
                                    actual_value = _json_pointer(payload, pointer)
                                except TestDataPlanError:
                                    errors.append(f"{prefix}: evidence_path не найден: {evidence_path}")
                                    continue
                                if actual_value != binding.get("verified_value"):
                                    errors.append(f"{prefix}: verified_value не совпадает с {evidence_path}")
            if unsupported_capabilities:
                errors.append(
                    f"{prefix}: provider {source!r} не доказывает capabilities: "
                    + ", ".join(sorted(unsupported_capabilities))
                )
        if status == "blocked" and not item.get("blocker"):
            errors.append(f"{prefix}: blocked требует blocker")
        if status == "blocked" and unsupported_capabilities:
            blocker = str(item.get("blocker") or "")
            if "BAQ-" not in blocker and "GAP-" not in blocker:
                errors.append(
                    f"{prefix}: semantic provider gap требует ссылку на BAQ-* или GAP-* в blocker"
                )
        if not item.get("linked_scenarios"):
            errors.append(f"{prefix}: не указаны linked_scenarios")
        if not item.get("selection_reason"):
            errors.append(f"{prefix}: не указан selection_reason")
    return errors


def validate_plan_file(path: Path, *, repo_root: Path | None = None) -> list[str]:
    return validate_plan(
        json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root, artifact_root=path.parent
    )
