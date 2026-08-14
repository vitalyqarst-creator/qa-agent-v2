from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "test-data-source-plan-v1"
PROVIDER_PROFILES: dict[str, dict[str, Any]] = {
    "source-literal": {"evidence": {"source-literal"}, "adapter": None},
    "package-dictionary": {"evidence": {"closed-dictionary-value"}, "adapter": None},
    "dadata-suggestions": {
        "evidence": {"integration-response", "business-valid-entity"},
        "adapter": "scripts/verify_dadata_positive_fixture.py", "integration": "dadata"},
    "randomdatatools-synthetic": {
        "evidence": {"neutral-format-value"},
        "adapter": "scripts/create_randomdatatools_synthetic_fixture.py"},
    "test-environment-setup": {"evidence": {"environment-state"}, "adapter": None},
}


class TestDataPlanError(ValueError):
    pass


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


def validate_plan(plan: dict[str, Any], *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if plan.get("contract_version") != CONTRACT_VERSION:
        errors.append("Некорректная contract_version")
    if not plan.get("scope_slug"):
        errors.append("Не указан scope_slug")
    sha = plan.get("matrix_sha256")
    if not isinstance(sha, str) or len(sha) != 64:
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
        if status == "blocked" and not item.get("blocker"):
            errors.append(f"{prefix}: blocked требует blocker")
        if not item.get("linked_scenarios"):
            errors.append(f"{prefix}: не указаны linked_scenarios")
        if not item.get("selection_reason"):
            errors.append(f"{prefix}: не указан selection_reason")
    return errors


def validate_plan_file(path: Path, *, repo_root: Path | None = None) -> list[str]:
    return validate_plan(json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root)

