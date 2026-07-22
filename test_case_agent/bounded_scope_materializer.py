from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .bounded_scope_boundary import (
    BoundedScopeBoundaryError,
    validate_publication_owner_token,
    validate_stable_path_segment,
)
from .review_cycle.source_assertions import (
    ApprovedClarification,
    SourceAssertion,
    SourceRow,
    build_source_assertion_manifest,
)
from .review_cycle.source_row_baseline import (
    load_extraction_spec,
    load_source_row_baseline,
)
from .semantic_design_bridge import (
    SEMANTIC_DESIGN_VERSION,
    legacy_v1_projection,
    normalize_semantic_design_source_property_transport,
    validate_bridge_boundary,
    validate_semantic_design_binding,
)


class BoundedScopeMaterializationError(ValueError):
    pass


def _object(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BoundedScopeMaterializationError(f"{label} must be an object")
    return value


def _array(value: Any, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise BoundedScopeMaterializationError(f"{label} must be an array")
    return value


def _text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BoundedScopeMaterializationError(f"{label} must be non-empty text")
    return value.strip()


def _stable_ft_slug(context: Mapping[str, Any]) -> str:
    try:
        return validate_stable_path_segment(
            context.get("ft_slug"), label="context.ft_slug"
        )
    except BoundedScopeBoundaryError as exc:
        raise BoundedScopeMaterializationError(str(exc)) from exc


def _publication_owner_token(value: Any) -> str:
    try:
        return validate_publication_owner_token(
            value, label="publication_owner_token"
        )
    except BoundedScopeBoundaryError as exc:
        raise BoundedScopeMaterializationError(str(exc)) from exc


def _repo_path(repo_root: Path, value: Any, *, label: str) -> Path:
    raw = PurePosixPath(_text(value, label=label))
    if raw.is_absolute():
        raise BoundedScopeMaterializationError(f"{label} must be repository-relative")
    path = (repo_root / Path(*raw.parts)).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise BoundedScopeMaterializationError(f"{label} escapes repository") from exc
    if not path.is_file():
        raise BoundedScopeMaterializationError(f"{label} is missing: {raw.as_posix()}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


_FIXTURE_TOKEN = re.compile(r"\b(?:FX|FIX)-[A-Za-z0-9_.-]+\b")
_DIRECT_CALIBRATION_TARGET = re.compile(
    r"(?:TC-[A-Za-z0-9_.-]+|candidate:[A-Za-z0-9][A-Za-z0-9_.-]*)"
)


def _is_explicit_direct_calibration_candidate(
    obligation: Mapping[str, Any],
) -> bool:
    """Recognize the typed direct-candidate contract without trusting notes."""

    return (
        str(obligation.get("obligation_class", "")).strip().casefold()
        == "candidate-ui-calibration"
        and str(obligation.get("oracle_source", "")).strip().casefold()
        == "not_found"
        and obligation.get("scope_obligation_ids") == []
        and _DIRECT_CALIBRATION_TARGET.fullmatch(
            str(obligation.get("planned_tc_id", "")).strip()
        )
        is not None
        and bool(str(obligation.get("single_expected_behavior", "")).strip())
        and bool(str(obligation.get("test_data", "")).strip())
    )


def _portable_fixture_contract_lines(
    *,
    repo_root: Path,
    source_entries: Sequence[Mapping[str, Any]],
    obligations: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    """Render exact inline contracts for named verified external fixtures."""

    referenced = {
        fixture_id
        for obligation in obligations
        for fixture_id in _FIXTURE_TOKEN.findall(
            json.dumps(obligation, ensure_ascii=False, sort_keys=True)
        )
    }
    if not referenced:
        return ()
    contracts: dict[str, str] = {}
    registered_paths = {str(entry.get("path", "")) for entry in source_entries}
    for entry in source_entries:
        repo_path = str(entry.get("path", ""))
        if not repo_path.casefold().endswith(".verification.json"):
            continue
        verification_path = _repo_path(
            repo_root,
            repo_path,
            label="fixture verification source.path",
        )
        try:
            verification = json.loads(verification_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BoundedScopeMaterializationError(
                f"fixture verification is unreadable: {repo_path}"
            ) from exc
        if not isinstance(verification, Mapping):
            raise BoundedScopeMaterializationError(
                f"fixture verification must be an object: {repo_path}"
            )
        fixture_id = str(verification.get("fixture_id", ""))
        if fixture_id not in referenced:
            continue
        request = verification.get("request", {})
        expected_response = verification.get("expected_response")
        response_sha256 = str(verification.get("response_sha256", ""))
        status = str(verification.get("status", ""))
        if (
            not isinstance(request, Mapping)
            or not isinstance(request.get("parameters"), Mapping)
            or not isinstance(expected_response, Mapping)
            or re.fullmatch(r"[0-9a-f]{64}", response_sha256) is None
            or status not in {"verified", "accepted"}
        ):
            raise BoundedScopeMaterializationError(
                f"fixture verification lacks a portable exact contract: {fixture_id}"
            )
        expected_response = copy.deepcopy(dict(expected_response))
        snapshot_name = verification.get("response_snapshot")
        if isinstance(snapshot_name, str) and snapshot_name.strip():
            snapshot_relative = (
                PurePosixPath(repo_path).parent / snapshot_name
            ).as_posix()
            if snapshot_relative in registered_paths:
                snapshot_path = _repo_path(
                    repo_root,
                    snapshot_relative,
                    label="fixture response source.path",
                )
                snapshot_raw = snapshot_path.read_bytes()
                if hashlib.sha256(snapshot_raw).hexdigest() != response_sha256:
                    raise BoundedScopeMaterializationError(
                        f"fixture response hash mismatch: {fixture_id}"
                    )
                try:
                    snapshot = json.loads(snapshot_raw.decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise BoundedScopeMaterializationError(
                        f"fixture response is unreadable: {fixture_id}"
                    ) from exc
                suggestions = (
                    snapshot.get("suggestions", [])
                    if isinstance(snapshot, Mapping)
                    else []
                )
                matches = [
                    item
                    for item in suggestions
                    if isinstance(item, Mapping)
                    and item.get("value")
                    == expected_response.get("exact_suggestion")
                    and isinstance(item.get("data"), Mapping)
                ] if isinstance(suggestions, list) else []
                if len(matches) != 1:
                    raise BoundedScopeMaterializationError(
                        f"fixture response does not uniquely bind exact suggestion: {fixture_id}"
                    )
                matched_data = matches[0]["data"]
                address = matched_data.get("address")
                address_value = (
                    str(address.get("value", "")).strip()
                    if isinstance(address, Mapping)
                    else ""
                )
                if address_value:
                    exact_components = expected_response.get("exact_components")
                    if not isinstance(exact_components, Mapping):
                        exact_components = {}
                    else:
                        exact_components = copy.deepcopy(dict(exact_components))
                    registered_address = str(
                        exact_components.get("address.value", "")
                    ).strip()
                    if registered_address and registered_address != address_value:
                        raise BoundedScopeMaterializationError(
                            f"fixture address component conflicts with response: {fixture_id}"
                        )
                    exact_components["address.value"] = address_value
                    expected_response["exact_components"] = exact_components
        request_json = json.dumps(
            request["parameters"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        expected_json = json.dumps(
            expected_response,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        contracts[fixture_id] = (
            f"- `{fixture_id}`: request_parameters=`{request_json}`; "
            f"expected_response=`{expected_json}`; "
            f"response_sha256=`{response_sha256}`; status=`{status}`; "
            "runtime_api_call=`prohibited`; product_input=`stored_literals`."
        )
    missing = sorted(referenced - contracts.keys())
    if missing:
        raise BoundedScopeMaterializationError(
            "named fixture lacks a registered verified portable contract: "
            + ", ".join(missing)
        )
    return tuple(contracts[fixture_id] for fixture_id in sorted(referenced))


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_json_fresh(path: Path, payload: Mapping[str, Any]) -> str:
    """Publish one JSON file without overwriting a concurrent or prior result.

    The temporary file is created beside the destination so ``os.link`` is an
    atomic no-clobber publication on the same filesystem.  The returned digest
    identifies the exact bytes that were published.
    """

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise BoundedScopeMaterializationError(
            f"summary output must be fresh: {path}"
        )
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise BoundedScopeMaterializationError(
                f"summary output appeared concurrently; refusing overwrite: {path}"
            ) from exc
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


def _cell(value: Any) -> str:
    text = (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
        .replace("|", "\\|")
    )
    # Paths are rendered in the same tables as prose.  Internal spaces are
    # semantically significant for a filesystem path and must survive the
    # Markdown round trip used by the downstream source gate.
    return text.strip()


def _tokens(values: Sequence[str]) -> str:
    return "; ".join(values) if values else "none_required"


def _table(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    rendered = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    rendered.extend(
        "| " + " | ".join(_cell(item) for item in row) + " |" for row in rows
    )
    return "\n".join(rendered)


def _ft_relative(repo_root: Path, ft_root: Path, repo_path: str) -> str:
    path = _repo_path(repo_root, repo_path, label="source.path")
    try:
        return path.relative_to(ft_root).as_posix()
    except ValueError as exc:
        raise BoundedScopeMaterializationError(
            f"selected source is outside FT package: {repo_path}"
        ) from exc


def _copy_exact(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if source.read_bytes() != target.read_bytes():
            raise BoundedScopeMaterializationError(
                f"immutable materialization target already differs: {target}"
            )
        return
    shutil.copyfile(source, target)


def _decision_registry(
    context: Mapping[str, Any], decision: Mapping[str, Any]
) -> tuple[list[Mapping[str, Any]], dict[str, Mapping[str, Any]], list[Mapping[str, Any]]]:
    source_rows = [
        _object(item, label="context.source_rows[]")
        for item in _array(context.get("source_rows"), label="context.source_rows")
    ]
    decisions = [
        _object(item, label="decision.source_decisions[]")
        for item in _array(decision.get("source_decisions"), label="decision.source_decisions")
    ]
    expected = [_text(item.get("source_row_id"), label="source_row_id") for item in source_rows]
    actual = [_text(item.get("source_row_id"), label="source_decision.source_row_id") for item in decisions]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise BoundedScopeMaterializationError(
            "source decisions must account for every context row exactly once"
        )
    by_row = {str(item["source_row_id"]): item for item in decisions}
    assertions: list[Mapping[str, Any]] = []
    for source_row in source_rows:
        source_row_id = str(source_row["source_row_id"])
        row_assertions = [
            _object(item, label=f"{source_row_id}.assertions[]")
            for item in _array(by_row[source_row_id].get("assertions"), label=f"{source_row_id}.assertions")
        ]
        if not row_assertions:
            raise BoundedScopeMaterializationError(
                f"{source_row_id} requires at least one explicit assertion"
            )
        has_testable = any(
            item.get("semantic_disposition") == "testable"
            for item in row_assertions
        )
        has_ambiguous = any(
            item.get("semantic_disposition") == "ambiguous"
            for item in row_assertions
        )
        expected_disposition = (
            "yes" if has_testable else ("unclear" if has_ambiguous else "no")
        )
        if by_row[source_row_id].get("scope_disposition") != expected_disposition:
            raise BoundedScopeMaterializationError(
                f"{source_row_id} scope_disposition must be {expected_disposition}"
            )
        assertions.extend(row_assertions)
    return source_rows, by_row, assertions


def _assertion_payload(
    source_row: Mapping[str, Any],
    assertion: Mapping[str, Any],
    *,
    primary_gap_id: str | None = None,
) -> dict[str, Any]:
    row_id = str(source_row["source_row_id"])
    row_text = str(source_row["bounded_source_text"])
    requirement_bindings = []
    for item in _array(
        assertion.get("requirement_code_evidence"),
        label=f"{assertion.get('assertion_id')}.requirement_code_evidence",
    ):
        binding = _object(item, label="requirement_code_evidence[]")
        provenance_role = str(binding.get("provenance_role", "xhtml-row"))
        def optional_evidence(value: Any) -> Any:
            return None if value in {None, "none_required"} else value

        if provenance_role == "pdf-parity":
            fragment = optional_evidence(binding.get("exact_source_fragment"))
            evidence_source_path = optional_evidence(
                binding.get("evidence_source_path")
            )
            evidence_locator = optional_evidence(binding.get("evidence_locator"))
        else:
            fragment = _text(
                binding.get("exact_source_fragment"),
                label="exact_source_fragment",
            )
            if fragment not in row_text and str(binding.get("source_row_id")) == row_id:
                raise BoundedScopeMaterializationError(
                    f"requirement fragment is not literal evidence for {row_id}: {fragment}"
                )
            evidence_source_path = optional_evidence(
                binding.get("evidence_source_path")
            )
            evidence_locator = optional_evidence(binding.get("evidence_locator"))
        requirement_bindings.append(
            {
                "requirement_code": binding["requirement_code"],
                "source_row_id": binding["source_row_id"],
                "provenance_role": provenance_role,
                "exact_source_fragment": fragment,
                "evidence_source_path": evidence_source_path,
                "evidence_locator": evidence_locator,
            }
        )
    clause_bindings = []
    for item in _array(
        assertion.get("clause_evidence"),
        label=f"{assertion.get('assertion_id')}.clause_evidence",
    ):
        binding = _object(item, label="clause_evidence[]")
        clause_bindings.append(
            {
                "clause_kind": binding["clause_kind"],
                "clause_index": binding["clause_index"],
                "source_row_id": binding["source_row_id"],
                "evidence_role": binding["clause_kind"],
                "exact_source_fragment": binding["exact_source_fragment"],
            }
        )
    return {
        "assertion_id": assertion["assertion_id"],
        "source_path": source_row["source_path"],
        "source_context_class": source_row["source_context_class"],
        "locator": source_row["source_locator"],
        "exact_source_text": source_row["bounded_source_text"],
        "canonical_statement": assertion["canonical_statement"],
        "polarity": assertion["polarity"],
        "semantic_disposition": assertion["semantic_disposition"],
        "execution_readiness": assertion["execution_readiness"],
        "execution_readiness_rationale": (
            assertion["execution_readiness_rationale"]
            if assertion["execution_readiness"] == "dependency-blocked"
            else "none_required"
        ),
        "risk": assertion["risk"],
        "condition_clauses": assertion["condition_clauses"],
        "action_clauses": assertion["action_clauses"],
        "oracle_clauses": assertion["oracle_clauses"],
        "requirement_codes": assertion["requirement_codes"],
        "requirement_code_bindings": requirement_bindings,
        "clause_evidence_bindings": clause_bindings,
        "source_row_id": row_id,
        "atom_id": assertion["atom_id"],
        "obligation_ids": assertion["obligation_ids"],
        "execution_dependency_gap_ids": [],
        "primary_gap_id": primary_gap_id,
        "disposition_rationale": assertion["disposition_rationale"],
        "supporting_source_bindings": list(
            assertion.get("supporting_source_bindings", [])
        ),
        "clarification_clause_bindings": list(
            assertion.get("clarification_clause_bindings", [])
        ),
    }


def _relative_handoff_path(ft_root: Path, handoff: Path, name: str) -> str:
    return (handoff / name).relative_to(ft_root).as_posix()


def _render_coverage_gaps(
    *,
    scope_slug: str,
    clarifications: Sequence[Mapping[str, Any]],
    boundary_gaps: Sequence[Mapping[str, Any]],
    requirement_codes_by_row: Mapping[str, Sequence[str]],
    gap_links: Mapping[str, Mapping[str, Sequence[str]]],
) -> str:
    if not boundary_gaps and not clarifications:
        return (
            "# Scope Coverage Gaps\n\n"
            "## Контекст\n\n"
            f"- `scope_slug`: `{scope_slug}`\n\n"
            "## Summary\n\n"
            "- Найдено gaps: `0`\n"
            "- Есть blocking gaps: `no`\n"
            "- Writing можно стартовать: `yes`\n\n"
            "## Coverage Gaps\n\n- none_required\n\n"
            "## Что Можно Покрывать Несмотря На Gaps\n\n- Весь подтверждённый scope.\n\n"
            "## Что Нельзя Домысливать\n\n- Поведение вне source evidence.\n\n"
            "## Требуемые Уточнения\n\n- none_required\n"
        )
    sections = []
    for record in boundary_gaps:
        gap_id = _text(record.get("gap_id"), label="boundary_gap.gap_id")
        if record.get("blocking") is not False:
            raise BoundedScopeMaterializationError(
                f"ready semantic boundary gap {gap_id} must be explicitly non-blocking"
            )
        source_row_ids = [
            str(item)
            for item in _array(
                record.get("source_row_ids"),
                label=f"boundary_gap.{gap_id}.source_row_ids",
            )
        ]
        source_refs = [
            str(item)
            for item in _array(
                record.get("source_refs"),
                label=f"boundary_gap.{gap_id}.source_refs",
            )
        ]
        exact_fragments = [
            str(item)
            for item in _array(
                record.get("exact_source_fragments"),
                label=f"boundary_gap.{gap_id}.exact_source_fragments",
            )
        ]
        links = gap_links.get(gap_id, {})
        requirement_codes = (
            list(dict.fromkeys(map(str, links["requirement_codes"])))
            if "requirement_codes" in links
            else list(
                dict.fromkeys(
                    code
                    for source_row_id in source_row_ids
                    for code in requirement_codes_by_row.get(source_row_id, ())
                )
            )
        )
        assertion_ids = list(links.get("assertion_ids", ()))
        atom_ids = list(links.get("atom_ids", ()))
        clarification_question = _text(
            record.get("clarification_question"),
            label=f"boundary_gap.{gap_id}.clarification_question",
        )
        downstream_handling = _text(
            record.get("downstream_handling"),
            label=f"boundary_gap.{gap_id}.downstream_handling",
        )
        gap_type = _text(
            record.get("gap_type"), label=f"boundary_gap.{gap_id}.gap_type"
        )
        sections.append(
            f"### {gap_id}\n\n"
            "| field | value |\n| --- | --- |\n"
            f"| gap_id | {gap_id} |\n"
            f"| gap_type | {gap_type} |\n"
            "| impact | non-blocking |\n"
            "| blocking | no |\n"
            "| blocks_ready_for_review | no |\n"
            "| status | open |\n"
            "| resolution | unresolved |\n"
            f"| source_row_ids | {_tokens(source_row_ids)} |\n"
            f"| source_refs | {_tokens(source_refs)} |\n"
            f"| requirement_codes | {_tokens(requirement_codes)} |\n"
            f"| exact_source_fragments | {_tokens(exact_fragments)} |\n"
            f"| clarification_question | {clarification_question} |\n"
            f"| reason | {clarification_question} |\n"
            f"| downstream_handling | {downstream_handling} |\n"
            f"| handling | {downstream_handling} |\n"
            f"| affected_assertion_id | {_tokens(assertion_ids) if assertion_ids else ''} |\n"
            f"| affected_atom_id | {_tokens(atom_ids) if atom_ids else ''} |\n"
            "| execution_assertion_ids |  |\n"
            "| execution_atom_ids |  |\n"
            "| execution_obligation_ids |  |\n\n"
            "Открытый non-blocking GAP сохранён из authoritative scope boundary; "
            "он ограничивает linked ATOM и не заменяет candidate/executable obligation.\n"
        )
    for record in clarifications:
        gap_id = _text(record.get("gap_id"), label="clarification.gap_id")
        clarification_id = _text(
            record.get("clarification_id"), label="clarification.clarification_id"
        )
        links = gap_links.get(gap_id, {})
        assertion_ids = list(links.get("assertion_ids", ()))
        atom_ids = list(links.get("atom_ids", ()))
        sections.append(
            f"### {gap_id}\n\n"
            "| field | value |\n| --- | --- |\n"
            f"| gap_id | {gap_id} |\n"
            "| impact | blocking |\n"
            "| blocks_ready_for_review | no |\n"
            "| status | resolved |\n"
            f"| resolution | approved-clarification:{clarification_id} |\n"
            f"| affected_assertion_id | {_tokens(assertion_ids) if assertion_ids else ''} |\n"
            f"| affected_atom_id | {_tokens(atom_ids) if atom_ids else ''} |\n"
            "| execution_assertion_ids |  |\n"
            "| execution_atom_ids |  |\n"
            "| execution_obligation_ids |  |\n\n"
            f"Уточнение `{clarification_id}` подтверждено и связано по SHA-256.\n"
        )
    if boundary_gaps:
        coverable_scope = (
            "- Исполнимые obligations, не зависящие от открытых GAP.\n"
            "- Linked ATOM для open GAP сохраняются только с явной GAP-трассировкой; "
            "неизвестное поведение не домысливается.\n"
        )
        required_clarifications = "".join(
            f"- `{record['gap_id']}`: {record['clarification_question']} "
            "Ответ фиксируется в `scope-clarification-requests.md`.\n"
            for record in boundary_gaps
        )
    else:
        coverable_scope = (
            "- Весь подтверждённый scope; перечисленные gaps уже закрыты typed "
            "approved clarifications.\n"
        )
        required_clarifications = "- none_required\n"
    return (
        "# Scope Coverage Gaps\n\n"
        "## Контекст\n\n"
        f"- `scope_slug`: `{scope_slug}`\n\n"
        "## Summary\n\n"
        f"- Открытых gaps: `{len(boundary_gaps)}`; resolved gaps: `{len(clarifications)}`.\n"
        "- Есть blocking gaps: `no`\n"
        "- Writing можно стартовать: `yes`\n\n"
        "## Coverage Gaps\n\n"
        + "\n".join(sections)
        + "\n## Что Можно Покрывать Несмотря На Gaps\n\n"
        + coverable_scope
        + "\n"
        "## Что Нельзя Домысливать\n\n- Любые неподтверждённые трактовки.\n\n"
        "## Требуемые Уточнения\n\n"
        + required_clarifications
    )


def _resolved_scope_exclusion_gap_links(
    *,
    clarifications: Sequence[Mapping[str, Any]],
    dependencies: Sequence[Mapping[str, Any]],
    requirement_codes_by_row: Mapping[str, Sequence[str]],
    decisions_by_row: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, tuple[str, ...]]]:
    """Bind resolved partial scope exclusions to their code-less N/A sibling."""

    result: dict[str, dict[str, tuple[str, ...]]] = {}
    scope_excluded_dependencies = [
        item for item in dependencies if item.get("resolution") == "scope-excluded"
    ]
    for clarification in clarifications:
        gap_id = str(clarification.get("gap_id", ""))
        clarification_codes = set(map(str, clarification.get("requirement_codes", [])))
        if not gap_id or not clarification_codes:
            continue
        linked_assertions: list[str] = []
        linked_atoms: list[str] = []
        for dependency in scope_excluded_dependencies:
            dependency_name = str(dependency.get("name", "")).strip().casefold()
            for source_row_id in map(str, dependency.get("source_row_ids", [])):
                if not clarification_codes.intersection(
                    requirement_codes_by_row.get(source_row_id, ())
                ):
                    continue
                row_decision = decisions_by_row.get(source_row_id)
                if row_decision is None:
                    raise BoundedScopeMaterializationError(
                        f"resolved clarification {gap_id} references unknown row "
                        f"{source_row_id}"
                    )
                candidates = [
                    assertion
                    for assertion in row_decision["assertions"]
                    if assertion.get("semantic_disposition") == "not-applicable"
                    and str(assertion.get("field_or_block", "")).strip().casefold()
                    == dependency_name
                ]
                if len(candidates) != 1:
                    raise BoundedScopeMaterializationError(
                        f"resolved clarification {gap_id} requires exactly one "
                        f"N/A sibling for {dependency.get('dependency_id')} on "
                        f"{source_row_id}"
                    )
                linked_assertions.append(str(candidates[0]["assertion_id"]))
                linked_atoms.append(str(candidates[0]["atom_id"]))
        if linked_assertions:
            result[gap_id] = {
                "assertion_ids": tuple(dict.fromkeys(linked_assertions)),
                "atom_ids": tuple(dict.fromkeys(linked_atoms)),
            }
    return result


def _render_oracle_inventory(
    *, scope_slug: str, kind: str, rows: Sequence[Mapping[str, Any]]
) -> str:
    if kind == "negative":
        columns = (
            "signal_id", "requirement_codes", "scope_obligation_id",
            "source_row_id", "source_ref", "field_or_block",
            "restriction_type", "negative_class", "source_statement",
            "representative_invalid_value", "observable_oracle_found", "oracle_source",
            "oracle_status", "decision", "planned_tc_or_gap", "gap_id",
            "analyst_question", "handoff_rule", "calibration_notes",
            "linked_atom_id", "linked_obligation_id",
        )
        title = "Negative Oracle Inventory"
    else:
        columns = (
            "signal_id", "requirement_codes", "scope_obligation_id",
            "source_row_id", "source_ref", "field_or_block",
            "restriction_type", "requiredness_source", "requiredness_class", "required_when",
            "marker_oracle_found", "empty_value_oracle_found", "oracle_source",
            "oracle_status", "decision", "planned_tc_or_gap", "gap_id",
            "analyst_question", "handoff_rule", "calibration_notes",
            "linked_atom_id", "linked_obligation_id",
        )
        title = "Requiredness Oracle Inventory"
    body = [
        [
            _tokens(item.get(column, []))
            if column == "requirement_codes"
            else item.get(column, "none_required")
            for column in columns
        ]
        for item in rows
    ]
    counts: dict[str, int] = {}
    for item in rows:
        decision = str(item.get("decision", ""))
        counts[decision] = counts.get(decision, 0) + 1
    return (
        f"# {title}\n\n## Контекст\n\n- `scope_slug`: `{scope_slug}`\n\n"
        f"## {title}\n\n" + _table(columns, body) + "\n\n## Summary\n\n"
        f"- total_obligations: `{len(rows)}`\n"
        + "".join(f"- {key}: `{value}`\n" for key, value in sorted(counts.items()))
        + "\n## Writer Handoff Rules\n\n"
        "- Сохранить exact `scope_obligation_id` и ATOM/OBL linkage.\n"
        "- Не домысливать неизвестный UI oracle.\n"
    )


def _render_clarification_requests(
    *,
    scope_slug: str,
    records: Sequence[ApprovedClarification],
    boundary_gaps: Sequence[Mapping[str, Any]] = (),
    requirement_codes_by_row: Mapping[str, Sequence[str]] | None = None,
    gap_links: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
) -> str:
    columns = (
        "clarification_id", "gap_id", "scope_slug", "requirement_codes",
        "related_ft_reference", "question", "needed_for", "blocking",
        "requested_from", "authority", "user_response", "response_status",
        "response_type", "updated_at",
    )
    rows = []
    codes_by_row = requirement_codes_by_row or {}
    links_by_gap = gap_links or {}
    for index, gap in enumerate(boundary_gaps, start=1):
        gap_id = _text(gap.get("gap_id"), label="boundary_gap.gap_id")
        source_row_ids = [
            str(item)
            for item in _array(
                gap.get("source_row_ids"),
                label=f"boundary_gap.{gap_id}.source_row_ids",
            )
        ]
        requirement_codes = list(
            dict.fromkeys(
                code
                for source_row_id in source_row_ids
                for code in codes_by_row.get(source_row_id, ())
            )
        )
        related_references = list(
            dict.fromkeys(
                [
                    *(
                        str(item)
                        for item in _array(
                            gap.get("source_refs"),
                            label=f"boundary_gap.{gap_id}.source_refs",
                        )
                    ),
                    *links_by_gap.get(gap_id, {}).get("atom_ids", ()),
                ]
            )
        )
        rows.append(
            [
                f"CLR-PENDING-{index:03d}",
                gap_id,
                scope_slug,
                _tokens(requirement_codes),
                _tokens(related_references),
                gap["clarification_question"],
                "Уточнить observable semantics без изменения candidate/executable route.",
                "no",
                "analyst",
                "analyst",
                "-",
                "unanswered",
                "not-provided",
                "-",
            ]
        )
    for record in records:
        references = (
            _tokens(record.requirement_codes)
            if record.requirement_codes
            else _tokens(record.source_row_ids)
        )
        rows.append(
            [
                record.clarification_id,
                record.gap_id,
                record.scope_slug,
                _tokens(record.requirement_codes),
                references,
                f"Resolved by registered evidence {record.evidence_source_path}.",
                "Точная semantic binding для source assertion.",
                "yes",
                record.authority,
                record.authority,
                record.exact_answer,
                record.response_status,
                record.response_type,
                record.answered_at,
            ]
        )
    return (
        "# Scope Clarification Requests\n\n"
        "## Контекст\n\n"
        f"- `scope_slug`: `{scope_slug}`\n"
        "- Coverage gaps: `scope-coverage-gaps.md`\n\n"
        "## Как Заполнять\n\n"
        "- Для pending строк заполнять только ответ, response status/type и дату.\n"
        "- Approved строки уже связаны с registered evidence; не редактировать.\n\n"
        "## Clarification Requests\n\n"
        + _table(columns, rows)
        + "\n\n## Gaps Without Requests\n\n"
        "| gap_id | related_ft_reference | reason |\n"
        "| --- | --- | --- |\n"
        "| none_required | none_required | Все boundary gaps имеют pending request или approved clarification. |\n\n"
        "## Правила Использования Ответов\n\n"
        "- Каждый ответ используется только через typed manifest binding и exact SHA-256.\n"
        "- При противоречии приоритет остаётся у основного ФТ.\n"
    )


def materialize_bounded_scope(
    *,
    repo_root: Path,
    context: Mapping[str, Any],
    decision: Mapping[str, Any],
    handoff_dir: Path,
    _semantic_design: Mapping[str, Any] | None = None,
    _scope_boundary_decision: Mapping[str, Any] | None = None,
    _approved_clarifications: Sequence[Mapping[str, Any]] = (),
    _bridge_receipt: Mapping[str, Any] | None = None,
    _logical_handoff_dir: Path | None = None,
    _canonical_test_cases_override: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if decision.get("version") == 2:
        raise BoundedScopeMaterializationError(
            "scope contract v2 is boundary-only and its semantic-design bridge is not "
            "implemented; use an explicit v1 analyzer decision for the current "
            "end-to-end materialization route"
        )
    if decision.get("version") != 1:
        raise BoundedScopeMaterializationError("decision.version must equal 1")
    ft_slug = _stable_ft_slug(context)
    scope_slug = _text(context.get("scope_slug"), label="context.scope_slug")
    section_id = _text(context.get("section_id"), label="context.section_id")
    package_id = _text(context.get("package_id", "WP-01"), label="context.package_id")
    semantic_mode = _semantic_design is not None
    if decision.get("status") != "ready":
        raise BoundedScopeMaterializationError(
            "blocked semantic decisions cannot be materialized as runnable workflow"
        )
    ft_root = (repo_root / "fts" / ft_slug).resolve()
    canonical_test_cases = str(context["canonical_test_cases"])
    if _canonical_test_cases_override is not None:
        override = _canonical_test_cases_override.resolve()
        test_cases_root = (ft_root / "test-cases").resolve()
        if (
            override.parent != test_cases_root
            or override.suffix.lower() != ".md"
            or override.name.casefold() == "readme.md"
        ):
            raise BoundedScopeMaterializationError(
                "canonical test-case override must be one Markdown file directly "
                "under the selected FT test-cases directory"
            )
        canonical_test_cases = override.relative_to(ft_root).as_posix()
    try:
        handoff_dir = handoff_dir.resolve()
        handoff_dir.relative_to(ft_root)
    except ValueError as exc:
        raise BoundedScopeMaterializationError("handoff_dir must stay inside selected FT") from exc
    if handoff_dir.exists() and any(handoff_dir.iterdir()):
        raise BoundedScopeMaterializationError(
            f"handoff_dir must be new or empty: {handoff_dir}"
        )
    handoff_dir.mkdir(parents=True, exist_ok=True)
    logical_handoff_dir = (
        _logical_handoff_dir.resolve()
        if _logical_handoff_dir is not None
        else handoff_dir
    )
    try:
        logical_handoff_dir.relative_to(ft_root)
    except ValueError as exc:
        raise BoundedScopeMaterializationError(
            "logical handoff_dir must stay inside selected FT"
        ) from exc

    source_rows, decisions_by_row, assertion_decisions = _decision_registry(context, decision)
    boundary_disposition_by_row = {
        str(item["source_row_id"]): str(item["disposition"])
        for item in (
            _scope_boundary_decision.get("source_decisions", [])
            if _scope_boundary_decision is not None
            else []
        )
        if isinstance(item, Mapping)
    }
    row_by_id = {str(item["source_row_id"]): item for item in source_rows}
    obligations = [
        _object(item, label="decision.obligations[]")
        for item in _array(decision.get("obligations"), label="decision.obligations")
    ]
    obligation_by_id = {str(item["obligation_id"]): item for item in obligations}

    semantic_negative_rows: list[Mapping[str, Any]] = []
    semantic_requiredness_rows: list[Mapping[str, Any]] = []
    boundary_gaps: list[Mapping[str, Any]] = []
    boundary_requirement_codes_by_row: dict[str, tuple[str, ...]] = {}
    candidate_obligation_ids: set[str] = set()
    constraint_gap_ids_by_atom: dict[str, list[str]] = {}
    primary_gap_id_by_atom: dict[str, str] = {}
    gap_links: dict[str, dict[str, tuple[str, ...]]] = {}
    if semantic_mode:
        assert _semantic_design is not None
        assert _scope_boundary_decision is not None
        semantic_negative_rows = [
            _object(item, label="semantic_design.negative_oracles[]")
            for item in _array(
                _semantic_design.get("negative_oracles"),
                label="semantic_design.negative_oracles",
            )
        ]
        semantic_requiredness_rows = [
            _object(item, label="semantic_design.requiredness_oracles[]")
            for item in _array(
                _semantic_design.get("requiredness_oracles"),
                label="semantic_design.requiredness_oracles",
            )
        ]
        boundary_gaps = [
            _object(item, label="scope_boundary_decision.gaps[]")
            for item in _array(
                _scope_boundary_decision.get("gaps"),
                label="scope_boundary_decision.gaps",
            )
        ]
        boundary_gap_by_id = {
            str(item["gap_id"]): item for item in boundary_gaps
        }
        boundary_source_decisions = [
            _object(item, label="scope_boundary_decision.source_decisions[]")
            for item in _array(
                _scope_boundary_decision.get("source_decisions"),
                label="scope_boundary_decision.source_decisions",
            )
        ]
        boundary_requirement_codes_by_row = {
            str(item["source_row_id"]): tuple(
                str(code)
                for code in _array(
                    item.get("requirement_codes"),
                    label=(
                        "scope_boundary_decision.source_decisions[]."
                        "requirement_codes"
                    ),
                )
            )
            for item in boundary_source_decisions
        }
        assertion_by_atom = {
            str(assertion["atom_id"]): assertion
            for assertion in assertion_decisions
        }
        testable_assertion_by_atom = {
            str(assertion["atom_id"]): assertion
            for assertion in assertion_decisions
            if assertion.get("semantic_disposition") == "testable"
        }
        atoms_by_row: dict[str, list[str]] = {}
        for row_id, row_decision in decisions_by_row.items():
            for assertion in row_decision["assertions"]:
                atoms_by_row.setdefault(row_id, []).append(
                    str(assertion["atom_id"])
                )

        oracle_bound_atoms_by_gap: dict[str, list[str]] = {}
        for oracle in (*semantic_negative_rows, *semantic_requiredness_rows):
            obligation_id = _text(
                oracle.get("linked_obligation_id"),
                label="semantic oracle linked_obligation_id",
            )
            atom_id = _text(
                oracle.get("linked_atom_id"), label="semantic oracle linked_atom_id"
            )
            obligation = obligation_by_id.get(obligation_id)
            if obligation is None or str(obligation.get("linked_atom_id")) != atom_id:
                raise BoundedScopeMaterializationError(
                    f"semantic oracle must preserve one known ATOM/OBL chain: "
                    f"{atom_id}/{obligation_id}"
                )
            if oracle.get("decision") == "candidate_tc_required":
                candidate_obligation_ids.add(obligation_id)
            gap_id = str(oracle.get("gap_id", ""))
            if gap_id in boundary_gap_by_id:
                oracle_bound_atoms_by_gap.setdefault(gap_id, []).append(atom_id)

        # A single source restriction may require multiple independent boundary
        # candidates (for example N-1 and N+1) while the source-signal registry
        # owns only one generic negative-oracle slot. Preserve the explicit typed
        # candidate contract; a prose review note alone is not authoritative.
        candidate_obligation_ids.update(
            str(obligation["obligation_id"])
            for obligation in obligations
            if _is_explicit_direct_calibration_candidate(obligation)
        )

        for gap_id, gap in boundary_gap_by_id.items():
            if gap.get("blocking") is not False:
                raise BoundedScopeMaterializationError(
                    f"ready semantic boundary cannot materialize blocking gap {gap_id}"
                )
            atom_ids = list(
                dict.fromkeys(oracle_bound_atoms_by_gap.get(gap_id, ()))
            )
            if not atom_ids:
                row_atom_ids = list(
                    dict.fromkeys(
                        atom_id
                        for row_id in _array(
                            gap.get("source_row_ids"),
                            label=f"scope_boundary_decision.gaps.{gap_id}.source_row_ids",
                        )
                        for atom_id in atoms_by_row.get(str(row_id), ())
                    )
                )
                ambiguous_atom_ids = [
                    atom_id
                    for atom_id in row_atom_ids
                    if assertion_by_atom.get(atom_id, {}).get(
                        "semantic_disposition"
                    )
                    == "ambiguous"
                ]
                if ambiguous_atom_ids:
                    atom_ids = ambiguous_atom_ids
                elif gap.get("gap_type") in {
                    "missing-observation-interface",
                    "missing-source-definition",
                }:
                    na_atom_ids = [
                        atom_id
                        for atom_id in row_atom_ids
                        if assertion_by_atom.get(atom_id, {}).get(
                            "semantic_disposition"
                        )
                        == "not-applicable"
                    ]
                    atom_ids = na_atom_ids or row_atom_ids
                else:
                    atom_ids = row_atom_ids
            if not atom_ids:
                raise BoundedScopeMaterializationError(
                    f"non-blocking boundary gap {gap_id} cannot be routed to a "
                    "source assertion ATOM"
                )
            unknown_atoms = sorted(set(atom_ids) - set(assertion_by_atom))
            if unknown_atoms:
                raise BoundedScopeMaterializationError(
                    f"boundary gap {gap_id} references unknown ATOMs: "
                    + ", ".join(unknown_atoms)
                )
            assertion_ids = tuple(
                str(assertion_by_atom[atom_id]["assertion_id"])
                for atom_id in atom_ids
            )
            linked_requirement_codes = tuple(
                dict.fromkeys(
                    code
                    for atom_id in atom_ids
                    for code in map(
                        str,
                        assertion_by_atom[atom_id].get("requirement_codes", []),
                    )
                )
            )
            gap_links[gap_id] = {
                "assertion_ids": assertion_ids,
                "atom_ids": tuple(atom_ids),
                "requirement_codes": linked_requirement_codes,
            }
            for atom_id in atom_ids:
                assertion = assertion_by_atom[atom_id]
                if assertion.get("semantic_disposition") == "ambiguous":
                    if atom_id in primary_gap_id_by_atom:
                        raise BoundedScopeMaterializationError(
                            f"ambiguous ATOM {atom_id} cannot own multiple primary GAPs"
                        )
                    primary_gap_id_by_atom[atom_id] = gap_id
                elif atom_id in testable_assertion_by_atom:
                    constraint_gap_ids_by_atom.setdefault(atom_id, []).append(
                        gap_id
                    )

        # A requirement-code clarification may exclude only an internal sibling of
        # an otherwise testable row. Preserve that resolved exclusion as a hash-bound
        # N/A ASSERT/ATOM link in scope-coverage-gaps without creating an obligation.
        scope_excluded_dependencies = [
            _object(item, label="scope_boundary_decision.dependencies[]")
            for item in _array(
                _scope_boundary_decision.get("dependencies"),
                label="scope_boundary_decision.dependencies",
            )
            if isinstance(item, Mapping) and item.get("resolution") == "scope-excluded"
        ]
        gap_links.update(
            _resolved_scope_exclusion_gap_links(
                clarifications=_approved_clarifications,
                dependencies=scope_excluded_dependencies,
                requirement_codes_by_row=boundary_requirement_codes_by_row,
                decisions_by_row=decisions_by_row,
            )
        )

    spec_source = _repo_path(
        repo_root, context.get("source_row_extraction_spec"), label="source_row_extraction_spec"
    )
    baseline_source = _repo_path(
        repo_root, context.get("source_row_baseline"), label="source_row_baseline"
    )
    spec_target = handoff_dir / "source-row-extraction-spec.json"
    baseline_target = handoff_dir / "source-row-baseline.json"
    _copy_exact(spec_source, spec_target)
    _copy_exact(baseline_source, baseline_target)
    spec = load_extraction_spec(spec_target)
    baseline = load_source_row_baseline(baseline_target)
    if spec.scope_slug != scope_slug or baseline.scope_slug != scope_slug:
        raise BoundedScopeMaterializationError("source baseline scope_slug mismatch")
    if len(source_rows) != baseline.candidate_count:
        raise BoundedScopeMaterializationError("context source rows must equal baseline candidates")

    gap_path = handoff_dir / "scope-coverage-gaps.md"
    _write_atomic(
        gap_path,
        (
            _render_coverage_gaps(
                scope_slug=scope_slug,
                clarifications=_approved_clarifications,
                boundary_gaps=boundary_gaps,
                requirement_codes_by_row=boundary_requirement_codes_by_row,
                gap_links=gap_links,
            )
            if semantic_mode
            else
            "# Scope Coverage Gaps\n\n"
            "- blocking: `0`\n"
            "- non_blocking: `0`\n"
            "- status: `none`\n\n"
            "Неразрешённых неоднозначностей в подтверждённом bounded scope нет.\n"
        ),
    )

    typed_rows = []
    typed_assertions = []
    for row in source_rows:
        row_id = str(row["source_row_id"])
        scope_disposition = str(decisions_by_row[row_id]["scope_disposition"])
        typed_rows.append(
            SourceRow.from_dict(
                {
                    "source_row_id": row_id,
                    "source_path": row["source_path"],
                    "source_locator": row["source_locator"],
                    "bounded_source_text": row["bounded_source_text"],
                    "source_context_class": row["source_context_class"],
                    "candidate_id": row["candidate_id"],
                    "scope_disposition": scope_disposition,
                    "requirement_codes": decisions_by_row[row_id]["requirement_codes"],
                }
            )
        )
        for assertion in decisions_by_row[row_id]["assertions"]:
            typed_assertions.append(
                SourceAssertion.from_dict(
                    _assertion_payload(
                        row,
                        assertion,
                        primary_gap_id=primary_gap_id_by_atom.get(
                            str(assertion["atom_id"])
                        ),
                    )
                )
            )

    source_entries = [
        _object(item, label="context.sources[]")
        for item in _array(context.get("sources"), label="context.sources")
    ]
    portable_fixture_lines = _portable_fixture_contract_lines(
        repo_root=repo_root,
        source_entries=source_entries,
        obligations=obligations,
    )
    mockups = [
        _object(item, label="context.mockups[]")
        for item in _array(context.get("mockups", []), label="context.mockups")
    ]
    all_selection_rows: list[list[Any]] = []
    for entry in (*source_entries, *mockups):
        repo_path = _text(entry.get("path"), label="source.path")
        file_path = _repo_path(repo_root, repo_path, label="source.path")
        all_selection_rows.append(
            [
                f"`{_ft_relative(repo_root, ft_root, repo_path)}`",
                f"`{entry['role']}`",
                f"`{_sha256(file_path)}`",
                f"`{entry['manifest_binding']}`",
                entry.get("selection_reason", "bounded scope input"),
                entry.get("version_or_date", "current"),
                entry.get("notes", "none"),
            ]
        )

    source_selection = (
        "# Source Selection\n\n"
        f"- request_summary: {_text(context.get('request_summary'), label='request_summary')}\n"
        f"- selected_ft_slug: `{ft_slug}`\n"
        f"- planned_scope_slug: `{scope_slug}`\n"
        "- selection_status: `selected`\n\n"
        "## Source Registry\n\n"
        + _table(
            (
                "path", "role", "sha256", "manifest_binding", "selection_reason",
                "version_or_date", "source_quality_notes",
            ),
            all_selection_rows,
        )
        + "\n\n## Machine-readable source\n\n"
        "- xhtml_available: `yes`\n"
        "- xhtml_matches_main_ft: `yes`\n"
        "- xhtml_required_for_downstream: `yes`\n"
    )
    _write_atomic(handoff_dir / "source-selection.md", source_selection)

    included = [str(item) for item in decision.get("included", [])]
    excluded = [str(item) for item in decision.get("excluded", [])]
    scope_gap_gate = (
        f"Все baseline rows учтены; {len(boundary_gaps)} open non-blocking GAP "
        "сохранены в scope-coverage-gaps.md и не блокируют независимые obligations."
        if boundary_gaps
        else "Все baseline rows учтены; открытые coverage gaps отсутствуют."
    )
    scope_contract = (
        "# Scope Contract\n\n"
        f"- scope_slug: `{scope_slug}`\n"
        f"- section_id: `{section_id}`\n"
        f"- package_id: `{package_id}`\n"
        f"- summary: {decision.get('scope_summary')}\n\n"
        "## Включено\n\n"
        + "\n".join(f"- {item}" for item in included)
        + "\n\n## Исключено\n\n"
        + "\n".join(f"- {item}" for item in excluded)
        + "\n\n## Gate\n\n"
        "Scope ограничен одним разделом. "
        + scope_gap_gate
        + "\n"
    )
    _write_atomic(handoff_dir / "scope-contract.md", scope_contract)

    parity_rows = []
    for item in context.get("parity", []):
        row = _object(item, label="context.parity[]")
        parity_rows.append(
            [
                row.get("requirement_code", "none_required"),
                row.get("docx_locator", "none_required"),
                row.get("xhtml_locator", "none_required"),
                row.get("pdf_locator", "none_required"),
                row.get("status", "matched"),
            ]
        )
    _write_atomic(
        handoff_dir / "source-parity-check.md",
        "# Source Parity Check\n\n"
        + _table(
            ("requirement_code", "docx_locator", "xhtml_locator", "pdf_locator", "status"),
            parity_rows,
        )
        + "\n\nDOCX остаётся source of truth; XHTML используется для exact rows; PDF — только parity.\n",
    )

    mockup_rows = [
        [
            f"`{entry['path']}`",
            entry.get("screen_name", "screen"),
            "; ".join(str(item) for item in decision.get("mockup_locators", [])),
            "UI locator only; no business-rule inference",
        ]
        for entry in mockups
    ]
    _write_atomic(
        handoff_dir / "mockup-visual-inventory.md",
        "# Mockup Visual Inventory\n\n"
        + _table(("path", "screen_name", "visible_locators", "limitation"), mockup_rows)
        + "\n",
    )

    assertion_by_atom = {str(item["atom_id"]): item for item in assertion_decisions}
    inventory_rows = []
    for row in source_rows:
        row_id = str(row["source_row_id"])
        row_assertions = decisions_by_row[row_id]["assertions"]
        inventory_rows.append(
            [
                f"`{row_id}`", f"`{package_id}`", row.get("field_or_action", "context"),
                row.get("source_ref", row["source_locator"]),
                f"`{_tokens(decisions_by_row[row_id]['requirement_codes'])}`",
                f"`{decisions_by_row[row_id]['scope_disposition']}`",
                f"`{_tokens([str(item['atom_id']) for item in row_assertions])}`",
                f"`{row['source_path']}`", f"`{row['source_locator']}`",
                row["bounded_source_text"], f"`{row['source_context_class']}`",
                f"`{row['candidate_id']}`",
                *(
                    [f"`{boundary_disposition_by_row[row_id]}`"]
                    if semantic_mode
                    else []
                ),
            ]
        )
    _write_atomic(
        handoff_dir / "source-row-inventory.md",
        "# Handoff Source Row Registry\n\n## Source Row Inventory\n\n"
        + _table(
            (
                "source_row_id", "package_id", "field_or_action", "source_ref",
                "requirement_codes", "in_scope", "mapped_atom_or_gap", "source_path",
                "source_locator", "bounded_source_text", "source_context_class", "candidate_id",
                *(["boundary_disposition"] if semantic_mode else []),
            ),
            inventory_rows,
        )
        + f"\n\n- Baseline candidates: `{baseline.candidate_count}`.\n"
        f"- Inventory rows: `{len(inventory_rows)}`.\n",
    )

    ledger_rows = []
    obligation_rows = []
    plan_rows = []
    context_counter = 0
    target_counter = 0
    plan_counter = 0
    for row in source_rows:
        row_id = str(row["source_row_id"])
        for assertion in decisions_by_row[row_id]["assertions"]:
            atom_id = str(assertion["atom_id"])
            codes = [str(item) for item in assertion["requirement_codes"]]
            testable = assertion["semantic_disposition"] == "testable"
            source_ref = str(assertion.get("source_reference") or row.get("source_ref") or row["source_locator"])
            assertion_package_id = str(
                obligation_by_id[str(assertion["obligation_ids"][0])].get(
                    "package_id", package_id
                )
                if assertion.get("obligation_ids")
                else row.get("package_id", package_id)
            )
            if testable:
                target_counter += 1
                planned_targets = [
                    str(obligation_by_id[obligation_id]["planned_tc_id"])
                    for obligation_id in assertion["obligation_ids"]
                ]
                coverage_status = (
                    "covered_with_ui_calibration"
                    if any(
                        str(obligation_id) in candidate_obligation_ids
                        for obligation_id in assertion["obligation_ids"]
                    )
                    else "covered"
                )
                covered_by = _tokens(planned_targets)
            else:
                context_counter += 1
                primary_gap_id = primary_gap_id_by_atom.get(atom_id)
                if assertion["semantic_disposition"] == "ambiguous":
                    if primary_gap_id is None:
                        raise BoundedScopeMaterializationError(
                            f"ambiguous ATOM {atom_id} requires one primary GAP"
                        )
                    coverage_status = "unclear"
                    covered_by = primary_gap_id
                else:
                    coverage_status = "not-applicable"
                    covered_by = "not-applicable"
            ledger_rows.append(
                [
                    f"`{atom_id}`", f"`{assertion_package_id}`", f"`{assertion['source_property_id']}`",
                    f"`{_tokens(codes)}`", source_ref, f"`{row_id}`", f"`{_tokens(codes)}`",
                    assertion["canonical_statement"], assertion["field_or_block"],
                    "; ".join(assertion["condition_clauses"]) or "none_required",
                    "; ".join(assertion["oracle_clauses"]) or assertion["disposition_rationale"],
                    f"`{coverage_status}`", f"`{covered_by}`",
                    f"`{_tokens(constraint_gap_ids_by_atom.get(atom_id, ()))}`",
                ]
            )
            if not testable:
                primary_gap_id = primary_gap_id_by_atom.get(atom_id)
                is_ambiguous = assertion["semantic_disposition"] == "ambiguous"
                context_obligation_class = (
                    "ambiguous-behavior"
                    if is_ambiguous
                    else "not-applicable-context"
                )
                context_planned_target = (
                    primary_gap_id if is_ambiguous else "not-applicable"
                )
                context_status = "unclear" if is_ambiguous else "not-applicable"
                context_notes = (
                    "Open primary source-definition GAP; no executable obligation."
                    if is_ambiguous
                    else "Explicit boundary/context accounting."
                )
                obligation_rows.append(
                    [
                        f"`OBL-CONTEXT-{context_counter:03d}`", f"`{package_id}`",
                        f"`{assertion['source_property_id']}`", f"`{atom_id}`", "`context`",
                        f"`{context_obligation_class}`", assertion["disposition_rationale"], source_ref,
                        f"`{row_id}`", f"`{_tokens(codes)}`", f"`{context_planned_target}`",
                        f"`{context_status}`", context_notes,
                        *(
                            ["`none_required`", "", "`none_required`", "`none`"]
                            if semantic_mode
                            else []
                        ),
                    ]
                )
                plan_rows.append(
                    [
                        f"`PD-CONTEXT-{context_counter:03d}`", f"`{package_id}`", "`traceability`",
                        source_ref, f"`{row_id}`", f"`{_tokens(codes)}`", f"`{atom_id}`",
                        assertion["disposition_rationale"], "`not-applicable`",
                        f"`{context_obligation_class}`", "`none_required:not-applicable`",
                        "`none_required:not-applicable`", source_ref,
                        f"`{context_planned_target}`", f"`{context_status}`",
                        *(
                            [
                                "none_required:not-applicable",
                                "none_required:not-applicable",
                                "none_required:not-applicable",
                                "none_required:not-applicable",
                                "none_required:not-applicable",
                            ]
                            if semantic_mode
                            else []
                        ),
                    ]
                )
                continue
            for obligation_id in assertion["obligation_ids"]:
                obligation = obligation_by_id[str(obligation_id)]
                obligation_package_id = str(obligation.get("package_id", package_id))
                obligation_rows.append(
                    [
                        f"`{obligation_id}`", f"`{obligation_package_id}`",
                        f"`{obligation['source_property_id']}`", f"`{atom_id}`",
                        f"`{obligation['property_type']}`", f"`{obligation['obligation_class']}`",
                        obligation["required_behavior"], obligation["source_ref"], f"`{row_id}`",
                        f"`{_tokens(codes)}`", f"`{obligation['planned_tc_id']}`", "`covered`",
                        obligation["review_notes"],
                        *(
                            [
                                f"`{_tokens([str(item) for item in obligation['dictionary_refs']])}`",
                                (
                                    f"`{obligation['dictionary_coverage']}`"
                                    if obligation["dictionary_refs"]
                                    else ""
                                ),
                                f"`{_tokens([str(item) for item in obligation['scope_obligation_ids']])}`",
                                (
                                    "`ui-calibration-required`"
                                    if str(obligation_id) in candidate_obligation_ids
                                    else "`none`"
                                ),
                            ]
                            if semantic_mode
                            else []
                        ),
                    ]
                )
                plan_counter += 1
                plan_rows.append(
                    [
                        f"`PD-{(plan_counter if semantic_mode else target_counter):03d}`",
                        f"`{obligation_package_id}`",
                        f"`{obligation['design_dimension']}`", obligation["source_ref"], f"`{row_id}`",
                        f"`{_tokens(codes)}`", f"`{atom_id}`", obligation["planned_check"],
                        f"`{obligation['check_type']}`", f"`{obligation['coverage_class']}`",
                        f"`{obligation['input_class']}`", obligation["single_expected_behavior"],
                        obligation["oracle_source"], f"`{obligation['planned_tc_id']}`", "`planned`",
                        *(
                            [
                                obligation["test_data"],
                                obligation["initial_state_capture"],
                                obligation["changed_state_setup"],
                                obligation["pre_action_state_oracle"],
                                obligation["state_relation"],
                            ]
                            if semantic_mode
                            else []
                        ),
                    ]
                )

    _write_atomic(
        handoff_dir / "atomic-requirements-ledger.md",
        "# Handoff Atomic Model\n\n## Atomic Requirements Ledger\n\n"
        + _table(
            (
                "atom_id", "package_id", "source_property_id", "req_id", "source_reference",
                "source_row_id", "requirement_codes", "atomic_statement", "field_or_block",
                "condition", "expected_behavior", "coverage_status", "covered_by_tc",
                "constraint_gap_ids",
            ),
            ledger_rows,
        )
        + "\n",
    )
    _write_atomic(
        handoff_dir / "coverage-obligation-table.md",
        "# Handoff Coverage Model\n\n## Coverage Obligation Table\n\n"
        + _table(
            (
                "obligation_id", "package_id", "source_property_id", "linked_atom_id",
                "property_type", "obligation_class", "required_behavior", "source_ref",
                "source_row_id", "requirement_codes", "planned_tc_or_gap", "status", "review_notes",
                *(
                    [
                        "dictionary_refs", "dictionary_coverage",
                        "scope_obligation_ids", "calibration_status",
                    ]
                    if semantic_mode
                    else []
                ),
            ),
            obligation_rows,
        )
        + "\n",
    )
    _write_atomic(
        handoff_dir / "package-test-design-plan.md",
        "# Handoff Package Design Input\n\n"
        + (
            "## Portable Fixture Contracts\n\n"
            + "\n".join(portable_fixture_lines)
            + "\n\n"
            if portable_fixture_lines
            else ""
        )
        + "## Package Test Design Plan\n\n"
        + _table(
            (
                "design_item_id", "package_id", "design_dimension", "source_ref", "source_row_id",
                "requirement_codes", "linked_atoms", "planned_check", "check_type", "coverage_class",
                "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status",
                *(
                    [
                        "test_data", "initial_state_capture", "changed_state_setup",
                        "pre_action_state_oracle", "state_relation",
                    ]
                    if semantic_mode
                    else []
                ),
            ),
            plan_rows,
        )
        + "\n\n## Package Gate\n\n"
        f"- `{package_id}` source rows: `{len(source_rows)}`.\n"
        f"- testable obligations: `{len(obligations)}`.\n"
        "- one executable plan row per obligation; no hidden coverage gap.\n",
    )

    dictionary_name = None
    negative_oracle_name = None
    requiredness_oracle_name = None
    if semantic_mode:
        assert _semantic_design is not None
        dictionaries = [
            _object(item, label="semantic_design.dictionaries[]")
            for item in _array(
                _semantic_design.get("dictionaries"),
                label="semantic_design.dictionaries",
            )
        ]
        if dictionaries:
            dictionary_name = "dictionary-inventory.md"
            properties_by_row: dict[str, list[str]] = {}
            for row_id, row_decision in decisions_by_row.items():
                properties_by_row[row_id] = [
                    str(item["source_property_id"])
                    for item in row_decision["assertions"]
                ]
            dictionary_rows = []
            for item in dictionaries:
                used_properties = list(
                    dict.fromkeys(
                        property_id
                        for row_id in item["source_row_ids"]
                        for property_id in properties_by_row[str(row_id)]
                    )
                )
                dictionary_rows.append(
                    [
                        f"`{item['dictionary_id']}`",
                        f"`{item['dictionary_name']}`",
                        f"`{item['source_file']}`",
                        item["source_location"],
                        f"`{item['extraction_status']}`",
                        "; ".join(f"`{value}`" for value in item["active_values"]),
                        (
                            "; ".join(f"`{value}`" for value in item["archived_values"])
                            or "-"
                        ),
                        _tokens(used_properties),
                        item["gap_id"],
                        item["notes"],
                    ]
                )
            _write_atomic(
                handoff_dir / dictionary_name,
                "# Dictionary Inventory\n\n## Dictionary Inventory\n\n"
                + _table(
                    (
                        "dictionary_id", "dictionary_name", "source_file",
                        "source_location", "extraction_status", "active_values",
                        "archived_values", "used_by_source_properties", "gap_id", "notes",
                    ),
                    dictionary_rows,
                )
                + "\n",
            )
        if semantic_negative_rows:
            negative_oracle_name = "negative-oracle-inventory.md"
            _write_atomic(
                handoff_dir / negative_oracle_name,
                _render_oracle_inventory(
                    scope_slug=scope_slug,
                    kind="negative",
                    rows=semantic_negative_rows,
                ),
            )
        if semantic_requiredness_rows:
            requiredness_oracle_name = "requiredness-oracle-inventory.md"
            _write_atomic(
                handoff_dir / requiredness_oracle_name,
                _render_oracle_inventory(
                    scope_slug=scope_slug,
                    kind="requiredness",
                    rows=semantic_requiredness_rows,
                ),
            )

    applicability_rows = []
    for item in decision["applicability"]:
        applicability_rows.append(
            [
                f"`{item['dimension']}`", f"`{item['applicable']}`", item["source_ref"],
                item["reason"], f"`{_tokens(item['linked_atoms'])}`",
                f"`{_tokens(item['linked_test_cases'])}`", "`-`",
            ]
        )
    _write_atomic(
        handoff_dir / "test-design-applicability-matrix.md",
        "# Handoff Applicability Input\n\n## Test-design Applicability Matrix\n\n"
        + _table(
            ("dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"),
            applicability_rows,
        )
        + "\n",
    )

    assertion_source_paths = [
        str(item["path"])
        for item in source_entries
        if item.get("manifest_binding") == "assertion-source"
    ]
    evidence_sources = [
        (str(item["path"]), str(item["manifest_binding"]))
        for item in source_entries
        if item.get("manifest_binding") in {
            "semantic-source-of-truth", "structural-visual-parity", "supporting-material",
            "approved-clarification",
        }
    ]
    typed_clarifications = tuple(
        ApprovedClarification.from_dict(item) for item in _approved_clarifications
    )
    staging_manifest = build_source_assertion_manifest(
        repo_root,
        scope_slug=scope_slug,
        coverage_gaps_path=gap_path.relative_to(repo_root).as_posix(),
        source_paths=assertion_source_paths,
        assertions=typed_assertions,
        source_row_extraction_spec_digest=spec.digest,
        source_row_baseline_digest=baseline.digest,
        source_row_candidate_count=baseline.candidate_count,
        source_rows=typed_rows,
        evidence_sources=evidence_sources,
        clarifications=typed_clarifications,
        mockups=[
            (
                str(item["path"]),
                str(item.get("screen_name", "screen")),
                tuple(str(locator) for locator in decision.get("mockup_locators", [])),
            )
            for item in mockups
        ],
        expected_source_rows=typed_rows,
    )
    logical_gap_path = logical_handoff_dir / gap_path.name
    manifest = replace(
        staging_manifest,
        coverage_gaps_artifact=replace(
            staging_manifest.coverage_gaps_artifact,
            path=logical_gap_path.relative_to(repo_root).as_posix(),
        ),
    )
    _write_json(handoff_dir / "source-assertions.json", manifest.to_dict())
    bridge_receipt_payload: dict[str, Any] | None = None
    if semantic_mode:
        assert _scope_boundary_decision is not None
        assert _semantic_design is not None
        assert _bridge_receipt is not None
        boundary_artifact = handoff_dir / "scope-boundary-decision.json"
        semantic_artifact = handoff_dir / "semantic-design.json"
        _write_json(boundary_artifact, _scope_boundary_decision)
        _write_json(semantic_artifact, _semantic_design)
        bridge_receipt_payload = {
            **dict(_bridge_receipt),
            "materialization_status": "materialized",
            "source_assertion_manifest_digest": manifest.digest,
            "scope_boundary_artifact_sha256": _sha256(boundary_artifact),
            "semantic_design_artifact_sha256": _sha256(semantic_artifact),
        }
        _write_json(
            handoff_dir / "semantic-design-bridge-receipt.json",
            bridge_receipt_payload,
        )
        clarification_paths = list(
            dict.fromkeys(
                item.evidence_source_path
                for item in typed_clarifications
            )
        )
        if len(clarification_paths) == 1 and not boundary_gaps:
            _copy_exact(
                _repo_path(
                    repo_root,
                    clarification_paths[0],
                    label="approved clarification evidence",
                ),
                handoff_dir / "scope-clarification-requests.md",
            )
        elif clarification_paths or boundary_gaps:
            _write_atomic(
                handoff_dir / "scope-clarification-requests.md",
                _render_clarification_requests(
                    scope_slug=scope_slug,
                    records=typed_clarifications,
                    boundary_gaps=boundary_gaps,
                    requirement_codes_by_row=(
                        boundary_requirement_codes_by_row
                    ),
                    gap_links=gap_links,
                ),
            )

    source_review_prompt = (
        "## Цель этапа\n\n"
        f"Независимо проверить source-first manifest `{manifest.digest}` для scope `{scope_slug}`.\n\n"
        "## Входные артефакты\n\n"
        "- source-assertions.json, source-gate-validation.json, source-row inventory/spec/baseline.\n"
        "- bounded DOCX/PDF extracts из workflow-state.\n\n"
        "## Обязательные действия\n\n"
        "- Проверить каждую assertion, boundary accounting и все 13 semantic dimensions.\n"
        "- Вернуть receipt v6; accepted допустим только при полном verified set.\n\n"
        "## Не делать\n\n"
        "- Не читать repository, не вызывать tools, не писать test cases.\n\n"
        "## Ожидаемые выходы\n\n- Один source-assertion-review.json.\n\n"
        "## Gate завершения\n\n- Exact manifest digest и accepted/changes-required decision.\n"
    )
    _write_atomic(handoff_dir / "prompt.scope-assertions-to-reviewer.md", source_review_prompt)
    iteration_prompt = (
        "## Цель этапа\n\n"
        f"Написать и независимо проверить тест-кейсы для bounded scope `{scope_slug}`.\n\n"
        "## Входные артефакты\n\n"
        "- workflow-state.yaml и все latest_artifacts source/design цепочки.\n\n"
        "## Обязательные действия\n\n"
        "- Сохранить ASSERT → ATOM → OBL → TC traceability.\n"
        "- Один TC покрывает одну основную проверку и один основной observable result.\n"
        "- Использовать mockup только для видимых action-oriented шагов.\n"
        "- Создать или обновить canonical session log и agent-decision-log "
        "по standard audit policy.\n\n"
        "## Не делать\n\n"
        "- Не расширять scope и не придумывать правила, которых нет в source evidence.\n"
        "- Не сохранять runtime/debug outputs и dispatcher/config snapshots как "
        "production artifacts; canonical audit logs обязательны.\n\n"
        "## Ожидаемые выходы\n\n"
        f"- `{canonical_test_cases}` после independent reviewer sign-off.\n\n"
        "## Gate завершения\n\n"
        "- Deterministic compiler gates pass; reviewer принимает все obligations без unresolved findings.\n"
    )
    _write_atomic(handoff_dir / "prompt.scope-to-iteration.md", iteration_prompt)
    if semantic_mode:
        _write_atomic(
            handoff_dir / "scope-analyzer-session-log.md",
            "# Scope Analyzer Session Log\n\n"
            "## Session Metadata\n\n"
            "| field | value |\n| --- | --- |\n"
            "| skill | `ft-scope-analyzer` |\n"
            "| mode | `standard-semantic-design-bridge` |\n"
            f"| ft_slug | `{ft_slug}` |\n"
            f"| scope_slug | `{scope_slug}` |\n"
            "| started_from | `prepared bounded context + scope boundary v2` |\n"
            "| status_after | `ready-for-next-stage` |\n\n"
            "## Inputs Read\n\n"
            "- `scope-boundary-decision.json` - authoritative scope boundary.\n"
            "- `semantic-design.json` - typed ASSERT/ATOM/OBL design.\n"
            "- Registered bounded sources - exact source and evidence bindings.\n\n"
            "## Inputs Not Used\n\n"
            "- Previous test-case outputs - excluded from semantic materialization.\n\n"
            "## Key Decisions\n\n"
            "- Preserve the exact v2 boundary and publish only a verified v3 semantic design.\n"
            "- Route the immutable source manifest to an independent source reviewer.\n\n"
            "## Risks And Fallbacks\n\n"
            "- No fallback or partial publication is allowed; failures leave no final handoff.\n\n"
            "## Validation\n\n"
            "- Exact boundary/design binding, typed clarification provenance and source manifest validation passed.\n"
            "- Transactional sibling staging completed before atomic publication.\n\n"
            "## Contamination Check\n\n"
            "- Prior generated test cases and previous semantic decisions were not used.\n",
        )
        _write_atomic(
            handoff_dir / "agent-decision-log.md",
            "# Agent Decision Log\n\n"
            "## Decision Log Metadata\n\n"
            "| field | value |\n| --- | --- |\n"
            f"| ft_slug | `{ft_slug}` |\n"
            f"| scope_slug | `{scope_slug}` |\n"
            "| stage | `ft-scope-analyzer` |\n"
            "| started_from | `scope-boundary-decision.json` |\n\n"
            "## Decision Log\n\n"
            "| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| `DEC-001` | 1 | `scope-boundary` | `scope-boundary-decision.json` | Preserve exact ordered v2 dispositions and codes | Boundary is authoritative for standard production | `source-row-inventory.md` | high | applied |\n"
            "| `DEC-002` | 2 | `test-design` | `semantic-design.json` | Preserve typed evidence, dictionaries, oracle inventories and state-change fields | Dropping them would degrade downstream test design | `source-assertions.json`; design artifacts | high | applied |\n"
            "| `DEC-003` | 3 | `routing` | verified bridge receipt | Route to independent source reviewer | Writer cannot start before accepted source review | `workflow-state.yaml`; `prompt.scope-assertions-to-reviewer.md` | high | applied |\n",
        )

    artifact_names = {
        "source_selection": "source-selection.md",
        "scope_contract": "scope-contract.md",
        "coverage_gaps": "scope-coverage-gaps.md",
        "source_parity_check": "source-parity-check.md",
        "source_row_inventory": "source-row-inventory.md",
        "source_row_extraction_spec": "source-row-extraction-spec.json",
        "source_row_baseline": "source-row-baseline.json",
        "mockup_visual_inventory": "mockup-visual-inventory.md",
        "source_assertions": "source-assertions.json",
        "source_gate_validation": "source-gate-validation.json",
        "source_assertion_review": "source-assertion-review.json",
        "source_assertion_review_prompt": "prompt.scope-assertions-to-reviewer.md",
        "atomic_requirements_ledger": "atomic-requirements-ledger.md",
        "coverage_obligation_table": "coverage-obligation-table.md",
        "package_test_design_plan": "package-test-design-plan.md",
        "test_design_applicability_matrix": "test-design-applicability-matrix.md",
        "prompt_scope_to_iteration": "prompt.scope-to-iteration.md",
        "active_transition_prompt": "prompt.scope-to-iteration.md",
    }
    if semantic_mode:
        artifact_names.update(
            {
                "scope_boundary_decision": "scope-boundary-decision.json",
                "semantic_design": "semantic-design.json",
                "semantic_design_bridge_receipt": "semantic-design-bridge-receipt.json",
                "active_transition_prompt": "prompt.scope-assertions-to-reviewer.md",
                "session_log": "scope-analyzer-session-log.md",
                "decision_log": "agent-decision-log.md",
            }
        )
        if (handoff_dir / "scope-clarification-requests.md").is_file():
            artifact_names["scope_clarification_requests"] = (
                "scope-clarification-requests.md"
            )
        if dictionary_name is not None:
            artifact_names["dictionary_inventory"] = dictionary_name
        if negative_oracle_name is not None:
            artifact_names["negative_oracle_inventory"] = negative_oracle_name
        if requiredness_oracle_name is not None:
            artifact_names["requiredness_oracle_inventory"] = requiredness_oracle_name
    bounded_evidence_names: list[str] = []
    bounded_evidence_targets: list[Path] = []
    for key, value in context.get("bounded_evidence", {}).items():
        bounded_source = _repo_path(
            repo_root, value, label=f"bounded_evidence.{key}"
        )
        bounded_name = f"bounded-evidence-{key.replace('_', '-')}.json"
        bounded_target = handoff_dir / bounded_name
        _copy_exact(bounded_source, bounded_target)
        artifact_names[f"bounded_evidence_{key}"] = bounded_name
        bounded_evidence_names.append(bounded_name)
        bounded_evidence_targets.append(bounded_target)

    downstream_evidence_readiness: dict[str, Any] | None = None
    if semantic_mode:
        # Import lazily to keep legacy v1 materialization independent while
        # reusing the exact canonical source-review evidence contract.  The
        # staging manifest differs from the published manifest only in the
        # transaction-local coverage-gaps path; after rename the published
        # logical path resolves to the same bytes.
        from scripts.codex_exec_source_assertion_reviewer import (  # noqa: PLC0415
            prepare_evidence_set,
        )

        prepared_evidence = prepare_evidence_set(
            root=repo_root,
            manifest=staging_manifest,
            inventory_path=handoff_dir / "source-row-inventory.md",
            extraction_spec_path=spec_target,
            baseline_path=baseline_target,
            bounded_extract_paths=tuple(bounded_evidence_targets),
            max_direct_file_bytes=65_536,
        )
        downstream_evidence_readiness = {
            "status": "passed",
            "canonical_preflight": "source-reviewer.prepare_evidence_set",
            "published_manifest_digest": manifest.digest,
            "binding_count": len(prepared_evidence.bindings),
            "bounded_extract_count": len(bounded_evidence_targets),
            "direct_image_attachment_count": len(prepared_evidence.image_paths),
        }
        assert bridge_receipt_payload is not None
        bridge_receipt_payload["downstream_evidence_readiness"] = (
            downstream_evidence_readiness
        )
        bridge_receipt_payload["publication"] = {
            "status": "atomic-renamed",
            "final_handoff": logical_handoff_dir.relative_to(repo_root).as_posix(),
        }
        _write_json(
            handoff_dir / "semantic-design-bridge-receipt.json",
            bridge_receipt_payload,
        )
    latest_lines = []
    for key, value in artifact_names.items():
        latest_value = _relative_handoff_path(ft_root, logical_handoff_dir, value)
        latest_lines.append(f"  {key}: {latest_value}")
    latest_lines.extend(
        [
            f"  main_ft_docx: {_ft_relative(repo_root, ft_root, context['main_ft_docx'])}",
            f"  main_ft_xhtml: {_ft_relative(repo_root, ft_root, context['main_ft_xhtml'])}",
            f"  main_ft_pdf: {_ft_relative(repo_root, ft_root, context['main_ft_pdf'])}",
            f"  package_notes: {_ft_relative(repo_root, ft_root, context['package_notes'])}",
            f"  canonical_test_cases: {canonical_test_cases}",
        ]
    )
    required_input_names = [
        "source-selection.md",
        "scope-contract.md",
        "scope-coverage-gaps.md",
        "source-parity-check.md",
        "mockup-visual-inventory.md",
        "source-row-inventory.md",
        "source-row-extraction-spec.json",
        "source-row-baseline.json",
        "source-assertions.json",
        "atomic-requirements-ledger.md",
        "coverage-obligation-table.md",
        "package-test-design-plan.md",
        "test-design-applicability-matrix.md",
        "prompt.scope-assertions-to-reviewer.md",
        *bounded_evidence_names,
    ]
    if semantic_mode:
        required_input_names.extend(
            [
                "scope-boundary-decision.json",
                "semantic-design.json",
                "semantic-design-bridge-receipt.json",
                "scope-analyzer-session-log.md",
                "agent-decision-log.md",
            ]
        )
        if (handoff_dir / "scope-clarification-requests.md").is_file():
            required_input_names.append("scope-clarification-requests.md")
        for optional_name in (
            dictionary_name,
            negative_oracle_name,
            requiredness_oracle_name,
        ):
            if optional_name is not None:
                required_input_names.append(optional_name)
    required_input_lines = "\n".join(
        "  - " + _relative_handoff_path(ft_root, logical_handoff_dir, name)
        for name in required_input_names
    )
    non_blocking_gap_count = len(
        {str(item["gap_id"]) for item in boundary_gaps}
    )
    open_questions = [
        f"{item['gap_id']} | {item['clarification_question']}"
        for item in boundary_gaps
    ]
    open_questions_yaml = (
        "open_questions: []\n"
        if not open_questions
        else "open_questions:\n"
        + "".join(
            f"  - {json.dumps(question, ensure_ascii=False)}\n"
            for question in open_questions
        )
    )
    workflow = (
        f"ft_slug: {ft_slug}\n"
        f"scope_slug: {scope_slug}\n"
        f"section_id: \"{section_id}\"\n"
        "prepared_compiler_contract_version: 3\n"
        + (
            "current_stage: ft-scope-analyzer\n"
            "stage_status: ready-for-next-stage\n"
            "current_round: 0\n"
            "next_skill: ft-test-case-reviewer\n"
            if semantic_mode
            else
            "current_stage: ft-test-case-iteration\n"
            "stage_status: runnable\n"
            "current_round: 1\n"
            "next_skill: ft-test-case-iteration\n"
        )
        + (
            "required_inputs:\n" + required_input_lines + "\n"
            if semantic_mode
            else ""
        )
        + "latest_artifacts:\n"
        + "\n".join(latest_lines)
        + "\ncoverage_gaps:\n  blocking: 0\n"
        + f"  non_blocking: {non_blocking_gap_count}\n"
        + open_questions_yaml
        + "blocking_reasons: []\naccepted_risks: []\n"
        f"canonical_test_cases: {canonical_test_cases}\n"
    )
    _write_atomic(handoff_dir / "workflow-state.yaml", workflow)
    return {
        "status": "materialized",
        "handoff": logical_handoff_dir.relative_to(repo_root).as_posix(),
        "manifest_digest": manifest.digest,
        "source_row_count": len(source_rows),
        "assertion_count": len(typed_assertions),
        "testable_obligation_count": len(obligations),
        "non_blocking_gap_count": non_blocking_gap_count,
        "persistent_artifact_count": len(tuple(handoff_dir.iterdir())),
        **(
            {"semantic_design_bridge": bridge_receipt_payload}
            if bridge_receipt_payload is not None
            else {}
        ),
        **(
            {"downstream_evidence_readiness": downstream_evidence_readiness}
            if downstream_evidence_readiness is not None
            else {}
        ),
    }


def materialize_semantic_design_bridge(
    *,
    repo_root: Path,
    context: Mapping[str, Any],
    scope_boundary_decision: Mapping[str, Any],
    semantic_design: Mapping[str, Any],
    approved_clarifications: Sequence[Mapping[str, Any]],
    publication_owner_token: str,
    handoff_dir: Path,
    success_summary_path: Path | None = None,
    canonical_test_cases_override: Path | None = None,
) -> dict[str, Any]:
    """Validate and transactionally publish one standard semantic handoff.

    All rendering happens in a new sibling staging directory.  The final path
    must not exist and becomes visible only after every source-first contract
    validation and file write has completed.
    """

    repo_root = repo_root.resolve()
    owner_token = _publication_owner_token(publication_owner_token)
    validate_bridge_boundary(context, scope_boundary_decision)
    normalized_semantic_design, normalization_receipt = (
        normalize_semantic_design_source_property_transport(
            semantic_design,
            context=context,
        )
    )
    semantic_design = normalized_semantic_design
    receipt = {
        **validate_semantic_design_binding(
            context,
            scope_boundary_decision,
            semantic_design,
            clarifications=approved_clarifications,
            require_ready=True,
        ),
        "transport_normalization": normalization_receipt,
        "publication_ownership_contract_version": 1,
        "publication_owner_token": owner_token,
        "canonical_test_cases_override": (
            canonical_test_cases_override.resolve().relative_to(repo_root).as_posix()
            if canonical_test_cases_override is not None
            else None
        ),
    }
    if semantic_design.get("version") != SEMANTIC_DESIGN_VERSION:
        raise BoundedScopeMaterializationError(
            f"semantic_design.version must equal {SEMANTIC_DESIGN_VERSION}"
        )
    ft_slug = _stable_ft_slug(context)
    ft_root = (repo_root / "fts" / ft_slug).resolve()
    final_dir = handoff_dir.resolve()
    try:
        final_dir.relative_to(ft_root)
    except ValueError as exc:
        raise BoundedScopeMaterializationError(
            "handoff_dir must stay inside selected FT"
        ) from exc
    if final_dir.exists():
        raise BoundedScopeMaterializationError(
            f"transactional semantic handoff must not already exist: {final_dir}"
        )
    resolved_summary: Path | None = None
    if success_summary_path is not None:
        resolved_summary = success_summary_path.resolve()
        overlaps_final = False
        for candidate, root in (
            (resolved_summary, final_dir),
            (final_dir, resolved_summary),
        ):
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            overlaps_final = True
            break
        if overlaps_final:
            raise BoundedScopeMaterializationError(
                "success summary must not overlap the atomic handoff path"
            )
        if resolved_summary.exists():
            raise BoundedScopeMaterializationError(
                f"summary output must be fresh: {resolved_summary}"
            )
        resolved_summary.parent.mkdir(parents=True, exist_ok=True)
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{final_dir.name}.semantic-stage-",
            dir=final_dir.parent,
        )
    ).resolve()
    try:
        projected = legacy_v1_projection(semantic_design)
        result = materialize_bounded_scope(
            repo_root=repo_root,
            context=context,
            decision=projected,
            handoff_dir=staging_dir,
            _semantic_design=semantic_design,
            _scope_boundary_decision=scope_boundary_decision,
            _approved_clarifications=approved_clarifications,
            _bridge_receipt=receipt,
            _logical_handoff_dir=final_dir,
            _canonical_test_cases_override=canonical_test_cases_override,
        )
        if final_dir.exists():
            raise BoundedScopeMaterializationError(
                f"transactional semantic handoff appeared during publication: {final_dir}"
            )
        result["handoff"] = final_dir.relative_to(repo_root).as_posix()
        result["persistent_artifact_count"] = len(tuple(staging_dir.iterdir()))
        result["materialization_status"] = result["status"]
        result["status"] = "completed"
        result["publication"] = {
            "status": "atomic-renamed",
            "final_handoff": result["handoff"],
            "staging_cleaned": True,
        }
        # The directory rename is the only success commit.  A completed summary
        # must never become visible before that commit: an abrupt process exit in
        # that window would otherwise leave a false success result with no handoff.
        os.rename(staging_dir, final_dir)
        if resolved_summary is not None:
            try:
                write_json_fresh(resolved_summary, result)
            except Exception as exc:  # noqa: BLE001 - reporting is post-commit.
                # The immutable handoff is authoritative after the rename.  Keep
                # returning success and expose the reporting problem to callers
                # that can still observe the in-process result/stdout.
                result["reporting_error"] = {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "summary_output": str(resolved_summary),
                }
        return result
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


__all__ = [
    "BoundedScopeMaterializationError",
    "materialize_bounded_scope",
    "materialize_semantic_design_bridge",
    "write_json_fresh",
]
