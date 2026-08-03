from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.etree import ElementTree


SCHEMA_VERSION = 1
CHANGE_CLASSES = frozenset(
    {
        "unchanged",
        "editorial-only",
        "moved",
        "renumbered",
        "modified-behavior",
        "added",
        "removed",
        "dictionary-changed",
        "support-changed",
        "mockup-changed",
        "ambiguous-match",
    }
)
CASE_ACTIONS = frozenset(
    {
        "reuse-byte-identical",
        "modify",
        "split",
        "merge",
        "retire",
        "replace",
        "new",
    }
)
_REQUIREMENT_CODE = re.compile(r"\b(?:GSR|BSR|DIT|REQ)\s*[-:]?\s*\d+[A-Za-zА-Яа-я]?\b", re.IGNORECASE)
_TC_HEADING = re.compile(r"(?m)^##[ \t]+(TC-[A-Za-z0-9-]+)[ \t]*\r?$")
_TRACE_TOKEN = re.compile(r"\b(?:ATOM|OBL|SRC|DICT|GSR|BSR|DIT|REQ)[ -][A-Za-z0-9-]+\b", re.IGNORECASE)
_SECTION_NUMBER = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s+)+")


class IncrementalUpdateError(ValueError):
    pass


@dataclass(frozen=True)
class SourceEntity:
    entity_id: str
    explicit_id: str
    kind: str
    section_path: tuple[str, ...]
    requirement_codes: tuple[str, ...]
    field_identity: str
    atomic_statement: str
    structural_hash: str
    semantic_hash: str
    editorial_hash: str
    source_locator: str
    dictionary_values: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["section_path"] = list(self.section_path)
        payload["requirement_codes"] = list(self.requirement_codes)
        payload["dictionary_values"] = list(self.dictionary_values)
        return payload


@dataclass(frozen=True)
class IncrementalUpdateResult:
    status: str
    run_dir: Path
    shadow_suite: Path | None
    release_manifest: Path
    writer_invocation_count: int
    change_count: int
    reused_case_count: int
    modified_case_count: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_bytes_atomic(path: Path, value: bytes, *, deny_existing: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if deny_existing and path.exists():
        raise IncrementalUpdateError(f"immutable artifact already exists: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("wb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_json(path: Path, payload: Any) -> None:
    _write_bytes_atomic(path, _json_bytes(payload))


def _read_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IncrementalUpdateError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise IncrementalUpdateError(f"{label} must be a JSON object: {path}")
    return payload


def _resolve(repo_root: Path, raw: Any, *, label: str, required: bool = True) -> Path | None:
    if raw is None and not required:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise IncrementalUpdateError(f"{label} path must be non-empty text")
    candidate = Path(raw)
    path = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise IncrementalUpdateError(f"{label} path escapes repository root: {path}") from exc
    if required and not path.is_file():
        raise IncrementalUpdateError(f"{label} is missing: {path}")
    return path


def _normalize_space(value: str) -> str:
    return " ".join(html.unescape(value).replace("\xa0", " ").split())


def _canonical_code(value: str) -> str:
    compact = re.sub(r"\s*[-:]?\s*", " ", value.strip().upper())
    return _normalize_space(compact)


def _codes(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_canonical_code(item.group(0)) for item in _REQUIREMENT_CODE.finditer(value)))


def _semantic_text(value: str) -> str:
    without_codes = _REQUIREMENT_CODE.sub(" ", value)
    return _normalize_space(without_codes).casefold()


def _editorial_text(value: str) -> str:
    semantic = _semantic_text(value)
    return " ".join(re.findall(r"[0-9a-zа-яё]+", semantic, re.IGNORECASE))


def _hash_fields(*values: Any) -> str:
    serialized = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(serialized.encode("utf-8"))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def _element_text(element: ElementTree.Element) -> str:
    return _normalize_space(" ".join(element.itertext()))


def _ancestors(
    element: ElementTree.Element,
    parents: Mapping[ElementTree.Element, ElementTree.Element],
) -> Iterable[ElementTree.Element]:
    current = parents.get(element)
    while current is not None:
        yield current
        current = parents.get(current)


def extract_xhtml_entities(path: Path) -> list[SourceEntity]:
    if not path.is_file():
        raise IncrementalUpdateError(
            "blocked-input: XHTML of the new FT version is mandatory"
        )
    try:
        root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ElementTree.ParseError) as exc:
        raise IncrementalUpdateError(f"cannot parse XHTML {path}: {exc}") from exc
    parents = {child: parent for parent in root.iter() for child in parent}
    sections: list[str] = []
    entities: list[SourceEntity] = []
    counters: dict[str, int] = {}
    for element in root.iter():
        tag = _local_name(element.tag)
        if re.fullmatch(r"h[1-6]", tag):
            level = int(tag[1])
            heading = _element_text(element)
            if heading:
                sections = sections[: level - 1]
                sections.append(heading)
            continue
        explicit_kind = element.attrib.get("data-entity-kind", "").strip()
        if tag not in {"tr", "li", "p"} and not explicit_kind:
            continue
        ancestor_tags = {_local_name(item.tag) for item in _ancestors(element, parents)}
        if tag == "p" and ancestor_tags & {"tr", "li"}:
            continue
        text = _element_text(element)
        statement = _normalize_space(element.attrib.get("data-statement", "")) or text
        if not statement:
            continue
        cells = [_element_text(child) for child in element if _local_name(child.tag) in {"td", "th"}]
        field_identity = _normalize_space(element.attrib.get("data-field-id", ""))
        if not field_identity and tag == "tr" and cells:
            field_identity = _normalize_space(cells[0])
        explicit_id = _normalize_space(element.attrib.get("data-entity-id", ""))
        kind = explicit_kind or (
            "table-row" if tag == "tr" else "list-item" if tag == "li" else "requirement"
        )
        raw_dictionary = element.attrib.get("data-dictionary-values", "")
        dictionary_values = tuple(
            _normalize_space(item) for item in raw_dictionary.split("|") if _normalize_space(item)
        )
        if kind == "dictionary" and not dictionary_values and len(cells) > 1:
            dictionary_values = tuple(
                item for item in (_normalize_space(cell) for cell in cells[1:]) if item
            )
        requirement_codes = _codes(statement)
        stable_basis = explicit_id or (
            requirement_codes[0]
            if requirement_codes
            else field_identity
            if field_identity
            else _editorial_text(statement)[:120]
        )
        occurrence_key = f"{kind}:{stable_basis}"
        counters[occurrence_key] = counters.get(occurrence_key, 0) + 1
        entity_id = explicit_id or (
            re.sub(r"[^a-zA-Z0-9_-]+", "-", stable_basis).strip("-").lower()[:60]
            or f"entity-{len(entities) + 1:04d}"
        )
        if counters[occurrence_key] > 1:
            entity_id = f"{entity_id}-{counters[occurrence_key]}"
        semantic = _semantic_text(statement)
        editorial = _editorial_text(statement)
        locator = f"{path.as_posix()}::{tag}[{len(entities) + 1}]"
        entities.append(
            SourceEntity(
                entity_id=entity_id,
                explicit_id=explicit_id,
                kind=kind,
                section_path=tuple(sections),
                requirement_codes=requirement_codes,
                field_identity=field_identity,
                atomic_statement=statement,
                structural_hash=_hash_fields(
                    kind,
                    [_SECTION_NUMBER.sub("", item) for item in sections],
                    field_identity.casefold(),
                    requirement_codes,
                ),
                semantic_hash=_hash_fields(semantic, dictionary_values),
                editorial_hash=_hash_fields(editorial, dictionary_values),
                source_locator=locator,
                dictionary_values=dictionary_values,
            )
        )
    if not entities:
        raise IncrementalUpdateError(f"XHTML contains no normalizable entities: {path}")
    return entities


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            data = archive.read("word/document.xml")
        root = ElementTree.fromstring(data)
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise IncrementalUpdateError(f"cannot parse DOCX source of truth {path}: {exc}") from exc
    return _normalize_space(" ".join(root.itertext()))


def extract_pdf_codes(path: Path) -> tuple[str, ...]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IncrementalUpdateError(f"cannot read PDF parity source {path}: {exc}") from exc
    text = raw.decode("utf-8", errors="ignore") + " " + raw.decode("latin-1", errors="ignore")
    return _codes(text)


def _unique_index(
    entities: Sequence[SourceEntity], key: str
) -> dict[Any, list[int]]:
    result: dict[Any, list[int]] = {}
    for index, entity in enumerate(entities):
        if key == "explicit_id":
            value: Any = entity.explicit_id or None
        elif key == "semantic_hash":
            value = entity.semantic_hash
        elif key == "requirement_codes":
            value = entity.requirement_codes[0] if len(entity.requirement_codes) == 1 else None
        elif key == "field_identity":
            value = (entity.kind, entity.field_identity.casefold()) if entity.field_identity else None
        else:
            raise IncrementalUpdateError(f"unknown entity index key: {key}")
        if value is not None:
            result.setdefault(value, []).append(index)
    return result


def classify_changes(
    old_entities: Sequence[SourceEntity],
    new_entities: Sequence[SourceEntity],
) -> list[dict[str, Any]]:
    unmatched_old = set(range(len(old_entities)))
    unmatched_new = set(range(len(new_entities)))
    pairs: list[tuple[int, int, str]] = []
    ambiguous_old: set[int] = set()
    ambiguous_new: set[int] = set()
    for key in ("explicit_id", "semantic_hash", "requirement_codes", "field_identity"):
        old_index = _unique_index(old_entities, key)
        new_index = _unique_index(new_entities, key)
        for value in sorted(set(old_index) & set(new_index), key=str):
            old_candidates = [item for item in old_index[value] if item in unmatched_old]
            new_candidates = [item for item in new_index[value] if item in unmatched_new]
            if len(old_candidates) == 1 and len(new_candidates) == 1:
                old_id, new_id = old_candidates[0], new_candidates[0]
                pairs.append((old_id, new_id, key))
                unmatched_old.remove(old_id)
                unmatched_new.remove(new_id)
            elif old_candidates and new_candidates:
                ambiguous_old.update(old_candidates)
                ambiguous_new.update(new_candidates)
    changes: list[dict[str, Any]] = []
    for old_id, new_id, matched_by in pairs:
        old = old_entities[old_id]
        new = new_entities[new_id]
        if old.kind == "dictionary" and old.dictionary_values != new.dictionary_values:
            classification = "dictionary-changed"
        elif old.semantic_hash == new.semantic_hash:
            if old.requirement_codes != new.requirement_codes:
                classification = "renumbered"
            elif (
                old.section_path != new.section_path
                or old.source_locator.rsplit("::", 1)[-1]
                != new.source_locator.rsplit("::", 1)[-1]
            ):
                classification = "moved"
            else:
                classification = "unchanged"
        elif old.editorial_hash == new.editorial_hash:
            classification = "editorial-only"
        else:
            classification = "modified-behavior"
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": classification,
                "matched_by": matched_by,
                "old_entity": old.to_dict(),
                "new_entity": new.to_dict(),
            }
        )
    for index in sorted(ambiguous_old & unmatched_old):
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "ambiguous-match",
                "matched_by": "non-unique-stable-identity",
                "old_entity": old_entities[index].to_dict(),
                "new_entity": None,
            }
        )
        unmatched_old.remove(index)
    for index in sorted(ambiguous_new & unmatched_new):
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "ambiguous-match",
                "matched_by": "non-unique-stable-identity",
                "old_entity": None,
                "new_entity": new_entities[index].to_dict(),
            }
        )
        unmatched_new.remove(index)
    for index in sorted(unmatched_old):
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "removed",
                "matched_by": "none",
                "old_entity": old_entities[index].to_dict(),
                "new_entity": None,
            }
        )
    for index in sorted(unmatched_new):
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "added",
                "matched_by": "none",
                "old_entity": None,
                "new_entity": new_entities[index].to_dict(),
            }
        )
    return sorted(changes, key=lambda item: item["change_id"])


def _append_file_changes(
    changes: list[dict[str, Any]],
    *,
    classification: str,
    old_paths: Sequence[Path],
    new_paths: Sequence[Path],
) -> None:
    old_registry = {path.name: sha256_file(path) for path in old_paths}
    new_registry = {path.name: sha256_file(path) for path in new_paths}
    if old_registry == new_registry:
        return
    changes.append(
        {
            "change_id": f"CHG-{len(changes) + 1:04d}",
            "classification": classification,
            "matched_by": "file-name-and-sha256",
            "old_entity": {"files": old_registry},
            "new_entity": {"files": new_registry},
        }
    )


def _append_pdf_code_change(
    changes: list[dict[str, Any]], old_pdf: Path, new_pdf: Path
) -> None:
    old_codes = extract_pdf_codes(old_pdf)
    new_codes = extract_pdf_codes(new_pdf)
    if old_codes == new_codes:
        return
    represented_old = {
        code
        for change in changes
        for entity in (change.get("old_entity"),)
        if isinstance(entity, Mapping)
        for code in entity.get("requirement_codes", [])
    }
    represented_new = {
        code
        for change in changes
        for entity in (change.get("new_entity"),)
        if isinstance(entity, Mapping)
        for code in entity.get("requirement_codes", [])
    }
    if set(old_codes) - represented_old or set(new_codes) - represented_new:
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "renumbered",
                "matched_by": "pdf-parity-only",
                "old_entity": {
                    "requirement_codes": list(old_codes),
                    "source_locator": str(old_pdf),
                },
                "new_entity": {
                    "requirement_codes": list(new_codes),
                    "source_locator": str(new_pdf),
                },
            }
        )


def split_test_cases(value: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    text = value.decode("utf-8")
    matches = list(_TC_HEADING.finditer(text))
    if not matches:
        raise IncrementalUpdateError("canonical test-case file contains no TC-* headings")
    preamble = text[: matches[0].start()].encode("utf-8")
    cases: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end].encode("utf-8")
        cases.append(
            {
                "tc_id": match.group(1),
                "bytes": block,
                "sha256": sha256_bytes(block),
                "trace_refs": sorted(
                    {
                        _canonical_code(item.group(0))
                        if item.group(0).upper().startswith(("GSR", "BSR", "DIT", "REQ"))
                        else item.group(0).upper()
                        for item in _TRACE_TOKEN.finditer(block.decode("utf-8"))
                    }
                ),
            }
        )
    if len({item["tc_id"] for item in cases}) != len(cases):
        raise IncrementalUpdateError("canonical test-case file has duplicate TC ids")
    return preamble, cases


def _traceability_refs(path: Path) -> dict[str, set[str]]:
    text = path.read_text(encoding="utf-8")
    result: dict[str, set[str]] = {}
    for line in text.splitlines():
        tc_ids = set(re.findall(r"\bTC-[A-Za-z0-9-]+\b", line))
        refs = {
            _canonical_code(item.group(0))
            if item.group(0).upper().startswith(("GSR", "BSR", "DIT", "REQ"))
            else item.group(0).upper()
            for item in _TRACE_TOKEN.finditer(line)
        }
        for tc_id in tc_ids:
            result.setdefault(tc_id, set()).update(refs - {tc_id})
    return result


def _source_assertion_links(path: Path) -> list[dict[str, Any]]:
    payload = _read_object(path, label="source assertions")
    raw = payload.get("assertions", payload.get("source_assertions", []))
    if not isinstance(raw, list):
        raise IncrementalUpdateError("source assertions must contain an assertions array")
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        serialized = json.dumps(item, ensure_ascii=False)
        result.append(
            {
                "assertion_id": str(item.get("assertion_id") or item.get("id") or ""),
                "refs": sorted(
                    {
                        _canonical_code(match.group(0))
                        if match.group(0).upper().startswith(("GSR", "BSR", "DIT", "REQ"))
                        else match.group(0).upper()
                        for match in _TRACE_TOKEN.finditer(serialized)
                    }
                ),
            }
        )
    return result


def build_impact_and_plan(
    *,
    changes: Sequence[Mapping[str, Any]],
    cases: Sequence[Mapping[str, Any]],
    traceability: Mapping[str, set[str]],
    assertion_links: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    impacts: list[dict[str, Any]] = []
    broad_change = any(
        item["classification"] in {"support-changed", "mockup-changed", "ambiguous-match"}
        for item in changes
    )
    changed_refs: set[str] = set()
    removed_refs: set[str] = set()
    behavior_change_refs: set[str] = set()
    for change in changes:
        classification = str(change["classification"])
        if classification == "unchanged":
            continue
        refs: set[str] = set()
        for side in ("old_entity", "new_entity"):
            entity = change.get(side)
            if not isinstance(entity, Mapping):
                continue
            refs.update(str(item).upper() for item in entity.get("requirement_codes", []))
            explicit = entity.get("explicit_id") or entity.get("entity_id")
            if isinstance(explicit, str) and explicit:
                refs.add(explicit.upper())
        changed_refs.update(refs)
        if classification == "removed":
            removed_refs.update(refs)
        if classification in {
            "modified-behavior",
            "dictionary-changed",
            "added",
            "removed",
        }:
            behavior_change_refs.update(refs)
        linked_assertions = sorted(
            item["assertion_id"]
            for item in assertion_links
            if refs & set(item["refs"])
        )
        linked_tcs = sorted(
            case["tc_id"]
            for case in cases
            if broad_change
            or refs
            & (
                set(case.get("trace_refs", []))
                | set(traceability.get(str(case["tc_id"]), set()))
            )
        )
        impacts.append(
            {
                "change_id": change["change_id"],
                "classification": classification,
                "requirement_refs": sorted(refs),
                "assertion_ids": linked_assertions,
                "test_case_ids": linked_tcs,
                "unknown_impact_expands_review": classification == "ambiguous-match",
            }
        )
    affected_by_tc = {
        tc_id: [impact for impact in impacts if tc_id in impact["test_case_ids"]]
        for tc_id in (str(case["tc_id"]) for case in cases)
    }
    plan: list[dict[str, Any]] = []
    for case in cases:
        tc_id = str(case["tc_id"])
        linked = affected_by_tc[tc_id]
        refs = set(case.get("trace_refs", [])) | set(traceability.get(tc_id, set()))
        if refs & removed_refs:
            action = "retire"
        elif linked and (
            broad_change
            or refs & behavior_change_refs
            or any(item["classification"] == "renumbered" for item in linked)
        ):
            action = "modify"
        else:
            action = "reuse-byte-identical"
        plan.append(
            {
                "tc_id": tc_id,
                "action": action,
                "intent_preserved": action in {"reuse-byte-identical", "modify"},
                "change_ids": [item["change_id"] for item in linked],
                "old_sha256": case["sha256"],
            }
        )
    for change in changes:
        if change["classification"] == "added":
            plan.append(
                {
                    "tc_id": None,
                    "action": "new",
                    "intent_preserved": False,
                    "change_ids": [change["change_id"]],
                    "old_sha256": None,
                }
            )
    return impacts, plan


def _writer_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"cases": {}, "new_cases": []}
    payload = _read_object(path, label="incremental writer output")
    cases = payload.get("cases", {})
    new_cases = payload.get("new_cases", [])
    if not isinstance(cases, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in cases.items()
    ):
        raise IncrementalUpdateError("writer output cases must map TC ids to full blocks")
    if not isinstance(new_cases, list) or not all(isinstance(item, str) for item in new_cases):
        raise IncrementalUpdateError("writer output new_cases must be a string array")
    return {"cases": cases, "new_cases": new_cases}


def materialize_suite(
    *,
    preamble: bytes,
    cases: Sequence[Mapping[str, Any]],
    plan: Sequence[Mapping[str, Any]],
    writer: Mapping[str, Any],
) -> tuple[bytes, list[dict[str, Any]], list[str]]:
    plan_by_tc = {
        str(item["tc_id"]): item for item in plan if isinstance(item.get("tc_id"), str)
    }
    output = bytearray(preamble)
    unchanged: list[dict[str, Any]] = []
    missing: list[str] = []
    writer_cases = writer["cases"]
    for case in cases:
        tc_id = str(case["tc_id"])
        action = plan_by_tc[tc_id]["action"]
        if action == "retire":
            continue
        if action == "reuse-byte-identical":
            block = bytes(case["bytes"])
            unchanged.append(
                {
                    "tc_id": tc_id,
                    "old_sha256": case["sha256"],
                    "new_sha256": sha256_bytes(block),
                    "byte_identical": case["sha256"] == sha256_bytes(block),
                }
            )
        else:
            replacement = writer_cases.get(tc_id)
            if not isinstance(replacement, str) or not replacement.strip():
                missing.append(tc_id)
                continue
            if not re.search(rf"(?m)^##[ \t]+{re.escape(tc_id)}[ \t]*$", replacement):
                raise IncrementalUpdateError(
                    f"writer replacement for {tc_id} must preserve unchanged intent TC-ID"
                )
            block = replacement.encode("utf-8")
            if not block.endswith(b"\n"):
                block += b"\n"
        output.extend(block)
    new_plan_count = sum(item["action"] == "new" for item in plan)
    if len(writer["new_cases"]) < new_plan_count:
        missing.extend(f"new:{index + 1}" for index in range(new_plan_count - len(writer["new_cases"])))
    for block_text in writer["new_cases"]:
        match = _TC_HEADING.search(block_text)
        if match is None:
            raise IncrementalUpdateError("every writer new case must contain a TC-* heading")
        block = block_text.encode("utf-8")
        if not block.endswith(b"\n"):
            block += b"\n"
        output.extend(block)
    return bytes(output), unchanged, missing


def _markdown_changes(changes: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# Нормализованный diff версий ФТ",
        "",
        "| ID | Класс | Старый locator | Новый locator |",
        "| --- | --- | --- | --- |",
    ]
    for item in changes:
        old = item.get("old_entity") if isinstance(item.get("old_entity"), Mapping) else {}
        new = item.get("new_entity") if isinstance(item.get("new_entity"), Mapping) else {}
        lines.append(
            f"| `{item['change_id']}` | `{item['classification']}` | "
            f"`{old.get('source_locator', '—')}` | `{new.get('source_locator', '—')}` |"
        )
    return "\n".join(lines) + "\n"


def _markdown_impact(impacts: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# Матрица влияния изменений",
        "",
        "| Change | Класс | Assertions | Test cases | Unknown impact |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in impacts:
        lines.append(
            f"| `{item['change_id']}` | `{item['classification']}` | "
            f"{'; '.join(item['assertion_ids']) or '—'} | "
            f"{'; '.join(item['test_case_ids']) or '—'} | "
            f"{'yes' if item['unknown_impact_expands_review'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def _markdown_plan(plan: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# План актуализации тест-кейсов",
        "",
        "| TC-ID | Действие | Change IDs | Сохраняется intent |",
        "| --- | --- | --- | --- |",
    ]
    for item in plan:
        lines.append(
            f"| `{item.get('tc_id') or 'NEW'}` | `{item['action']}` | "
            f"{'; '.join(item['change_ids']) or '—'} | "
            f"{'yes' if item['intent_preserved'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def _markdown_changelog(plan: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# Changelog тест-кейсов",
        "",
        "| Старый TC-ID | Новый TC-ID | Действие |",
        "| --- | --- | --- |",
    ]
    for item in plan:
        tc_id = item.get("tc_id") or "—"
        new_id = tc_id if item["action"] not in {"retire", "new"} else "—"
        lines.append(f"| `{tc_id}` | `{new_id}` | `{item['action']}` |")
    return "\n".join(lines) + "\n"


def _run_gate(command: Sequence[str], *, repo_root: Path, shadow_suite: Path) -> dict[str, Any]:
    expanded = [item.replace("{shadow_suite}", str(shadow_suite)) for item in command]
    completed = subprocess.run(
        expanded,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
    )
    return {
        "command": expanded,
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_incremental_update(
    *,
    repo_root: Path,
    config_path: Path,
) -> IncrementalUpdateResult:
    repo_root = repo_root.resolve()
    config_path = config_path.resolve()
    config = _read_object(config_path, label="incremental update config")
    if config.get("schema_version") != SCHEMA_VERSION:
        raise IncrementalUpdateError("unsupported incremental update config schema")
    old = config.get("old_version")
    new = config.get("new_version")
    baseline = config.get("baseline")
    output = config.get("output")
    if not all(isinstance(item, Mapping) for item in (old, new, baseline, output)):
        raise IncrementalUpdateError(
            "config requires old_version, new_version, baseline and output objects"
        )
    run_dir = _resolve(repo_root, output.get("run_dir"), label="output.run_dir", required=False)
    assert run_dir is not None
    if run_dir.exists() and any(run_dir.iterdir()):
        raise IncrementalUpdateError(f"incremental update run directory is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    old_docx = _resolve(repo_root, old.get("docx"), label="old DOCX")
    new_docx = _resolve(repo_root, new.get("docx"), label="new DOCX")
    old_xhtml = _resolve(repo_root, old.get("xhtml"), label="old XHTML")
    new_xhtml = _resolve(repo_root, new.get("xhtml"), label="new XHTML")
    old_pdf = _resolve(repo_root, old.get("pdf"), label="old PDF")
    new_pdf = _resolve(repo_root, new.get("pdf"), label="new PDF")
    canonical = _resolve(repo_root, baseline.get("canonical_test_cases"), label="canonical test cases")
    traceability = _resolve(repo_root, baseline.get("traceability_matrix"), label="traceability matrix")
    assertions = _resolve(repo_root, baseline.get("source_assertions"), label="source assertions")
    assert all(path is not None for path in (old_docx, new_docx, old_xhtml, new_xhtml, old_pdf, new_pdf, canonical, traceability, assertions))

    old_docx_text = extract_docx_text(old_docx)
    new_docx_text = extract_docx_text(new_docx)
    old_entities = extract_xhtml_entities(old_xhtml)
    new_entities = extract_xhtml_entities(new_xhtml)
    changes = classify_changes(old_entities, new_entities)
    if old_docx_text != new_docx_text and all(
        item["classification"] in {"unchanged", "moved"} for item in changes
    ):
        changes.append(
            {
                "change_id": f"CHG-{len(changes) + 1:04d}",
                "classification": "ambiguous-match",
                "matched_by": "docx-source-change-not-projected-by-xhtml",
                "old_entity": {
                    "source_locator": str(old_docx),
                    "semantic_hash": sha256_bytes(old_docx_text.encode("utf-8")),
                },
                "new_entity": {
                    "source_locator": str(new_docx),
                    "semantic_hash": sha256_bytes(new_docx_text.encode("utf-8")),
                },
            }
        )

    def file_list(version: Mapping[str, Any], field: str) -> list[Path]:
        raw = version.get(field, [])
        if not isinstance(raw, list):
            raise IncrementalUpdateError(f"{field} must be an array")
        result: list[Path] = []
        for index, item in enumerate(raw):
            path = _resolve(repo_root, item, label=f"{field}[{index}]")
            assert path is not None
            result.append(path)
        return result

    _append_file_changes(
        changes,
        classification="support-changed",
        old_paths=file_list(old, "support"),
        new_paths=file_list(new, "support"),
    )
    _append_file_changes(
        changes,
        classification="mockup-changed",
        old_paths=file_list(old, "mockups"),
        new_paths=file_list(new, "mockups"),
    )
    _append_pdf_code_change(changes, old_pdf, new_pdf)
    if any(item["classification"] not in CHANGE_CLASSES for item in changes):
        raise IncrementalUpdateError("diff emitted an unknown change classification")

    canonical_bytes = canonical.read_bytes()
    preamble, cases = split_test_cases(canonical_bytes)
    impacts, plan = build_impact_and_plan(
        changes=changes,
        cases=cases,
        traceability=_traceability_refs(traceability),
        assertion_links=_source_assertion_links(assertions),
    )
    if any(item["action"] not in CASE_ACTIONS for item in plan):
        raise IncrementalUpdateError("update plan emitted an unknown case action")

    substantive_changes = [item for item in changes if item["classification"] != "unchanged"]
    writer_path = _resolve(
        repo_root,
        config.get("writer_output"),
        label="writer_output",
        required=False,
    )
    writer_invocation_count = 0 if not substantive_changes else 1 if writer_path else 0
    writer = _writer_payload(writer_path)
    suite_bytes, unchanged, missing_writer_items = materialize_suite(
        preamble=preamble,
        cases=cases,
        plan=plan,
        writer=writer,
    )
    if not substantive_changes:
        suite_bytes = canonical_bytes
        unchanged = [
            {
                "tc_id": case["tc_id"],
                "old_sha256": case["sha256"],
                "new_sha256": case["sha256"],
                "byte_identical": True,
            }
            for case in cases
        ]
        missing_writer_items = []
    shadow_dir = run_dir / "shadow-release"
    shadow_suite = shadow_dir / canonical.name
    _write_bytes_atomic(shadow_suite, suite_bytes)

    affected_case_ids = {
        str(item["tc_id"])
        for item in plan
        if isinstance(item.get("tc_id"), str)
        and item["action"] != "reuse-byte-identical"
    }
    _write_json(
        run_dir / "writer-input-package.json",
        {
            "schema_version": 1,
            "changed_entities": substantive_changes,
            "affected_cases": {
                str(case["tc_id"]): bytes(case["bytes"]).decode("utf-8")
                for case in cases
                if str(case["tc_id"]) in affected_case_ids
            },
            "impact": impacts,
            "update_plan": [
                item
                for item in plan
                if item.get("tc_id") is None or str(item.get("tc_id")) in affected_case_ids
            ],
            "dictionary_values": sorted(
                {
                    value
                    for change in substantive_changes
                    for entity in (change.get("new_entity"),)
                    if isinstance(entity, Mapping)
                    for value in entity.get("dictionary_values", [])
                }
            ),
            "full_old_suite_included": False,
        },
    )

    _write_json(
        run_dir / "ft-version-diff.json",
        {
            "schema_version": 1,
            "old_version_id": old.get("id"),
            "new_version_id": new.get("id"),
            "old_docx_sha256": sha256_file(old_docx),
            "new_docx_sha256": sha256_file(new_docx),
            "old_docx_text_sha256": sha256_bytes(old_docx_text.encode("utf-8")),
            "new_docx_text_sha256": sha256_bytes(new_docx_text.encode("utf-8")),
            "old_entities": [item.to_dict() for item in old_entities],
            "new_entities": [item.to_dict() for item in new_entities],
            "changes": changes,
        },
    )
    _write_bytes_atomic(run_dir / "ft-version-diff.md", _markdown_changes(changes).encode("utf-8"))
    _write_json(
        run_dir / "change-classification.json",
        {
            "schema_version": 1,
            "counts": {
                classification: sum(item["classification"] == classification for item in changes)
                for classification in sorted(CHANGE_CLASSES)
            },
            "changes": changes,
        },
    )
    _write_bytes_atomic(run_dir / "change-impact-matrix.md", _markdown_impact(impacts).encode("utf-8"))
    _write_bytes_atomic(run_dir / "update-plan.md", _markdown_plan(plan).encode("utf-8"))
    _write_json(
        run_dir / "tc-reuse-manifest.json",
        {
            "schema_version": 1,
            "canonical_before_sha256": sha256_bytes(canonical_bytes),
            "shadow_after_sha256": sha256_bytes(suite_bytes),
            "writer_invocation_count": writer_invocation_count,
            "cases": unchanged,
        },
    )
    _write_json(
        run_dir / "unchanged-region-manifest.json",
        {
            "schema_version": 1,
            "all_byte_identical": all(item["byte_identical"] for item in unchanged),
            "regions": unchanged,
        },
    )
    _write_bytes_atomic(run_dir / "test-case-changelog.md", _markdown_changelog(plan).encode("utf-8"))

    release_mode = str(config.get("release_mode") or "shadow")
    if release_mode not in {"shadow", "publish"}:
        raise IncrementalUpdateError("release_mode must be shadow or publish")

    stale_codes: list[str] = []
    shadow_text = suite_bytes.decode("utf-8")
    for change in changes:
        if change["classification"] not in {"renumbered", "removed"}:
            continue
        old_entity = change.get("old_entity")
        new_entity = change.get("new_entity")
        new_codes = set(new_entity.get("requirement_codes", [])) if isinstance(new_entity, Mapping) else set()
        if isinstance(old_entity, Mapping):
            stale_codes.extend(
                code
                for code in old_entity.get("requirement_codes", [])
                if code not in new_codes and code in shadow_text
            )
    review_findings: list[dict[str, Any]] = []
    if missing_writer_items:
        review_findings.append(
            {
                "id": "UPDATE-WRITER-OUTPUT-MISSING",
                "severity": "error",
                "details": missing_writer_items,
            }
        )
    if not all(item["byte_identical"] for item in unchanged):
        review_findings.append(
            {
                "id": "UPDATE-UNCHANGED-REGION-MUTATED",
                "severity": "error",
                "details": [item["tc_id"] for item in unchanged if not item["byte_identical"]],
            }
        )
    if stale_codes:
        review_findings.append(
            {
                "id": "UPDATE-STALE-REQUIREMENT-REFERENCE",
                "severity": "error",
                "details": sorted(set(stale_codes)),
            }
        )
    if any(item["classification"] == "ambiguous-match" for item in changes):
        review_findings.append(
            {
                "id": "UPDATE-AMBIGUOUS-MATCH",
                "severity": "error",
                "details": [
                    item["change_id"]
                    for item in changes
                    if item["classification"] == "ambiguous-match"
                ],
            }
        )
    gate_results: list[dict[str, Any]] = []
    raw_gates = config.get("production_gate_commands", [])
    if not isinstance(raw_gates, list):
        raise IncrementalUpdateError("production_gate_commands must be an array")
    for raw_command in raw_gates:
        if not isinstance(raw_command, list) or not all(isinstance(item, str) for item in raw_command):
            raise IncrementalUpdateError("each production gate command must be a string array")
        gate = _run_gate(raw_command, repo_root=repo_root, shadow_suite=shadow_suite)
        gate_results.append(gate)
        if not gate["passed"]:
            review_findings.append(
                {
                    "id": "UPDATE-PRODUCTION-GATE-FAILED",
                    "severity": "error",
                    "details": gate,
                }
            )
    independent_review_accepted = False
    independent_review_path = _resolve(
        repo_root,
        config.get("independent_review_output"),
        label="independent_review_output",
        required=False,
    )
    if independent_review_path is not None:
        independent_review = _read_object(
            independent_review_path, label="independent update review"
        )
        expected_review_binding = {
            "shadow_sha256": sha256_bytes(suite_bytes),
            "ft_version_diff_sha256": sha256_file(run_dir / "ft-version-diff.json"),
            "update_plan_sha256": sha256_file(run_dir / "update-plan.md"),
        }
        independent_review_accepted = (
            independent_review.get("decision") == "accepted"
            and isinstance(independent_review.get("reviewer_session_id"), str)
            and bool(independent_review.get("reviewer_session_id", "").strip())
            and all(
                independent_review.get(key) == value
                for key, value in expected_review_binding.items()
            )
        )
        if not independent_review_accepted:
            review_findings.append(
                {
                    "id": "UPDATE-INDEPENDENT-REVIEW-INVALID",
                    "severity": "error",
                    "details": expected_review_binding,
                }
            )
    elif release_mode == "publish":
        review_findings.append(
            {
                "id": "UPDATE-INDEPENDENT-REVIEW-MISSING",
                "severity": "error",
                "details": "publish requires a hash-bound independent review artifact",
            }
        )
    if release_mode == "publish" and not gate_results:
        review_findings.append(
            {
                "id": "UPDATE-PRODUCTION-GATES-NOT-CONFIGURED",
                "severity": "error",
                "details": "publish requires at least one full-suite production gate command",
            }
        )
    accepted = not review_findings
    review_result = {
        "schema_version": 1,
        "decision": "accepted" if accepted else "changes-required",
        "checks": {
            "classification_reviewed": True,
            "impact_analysis_reviewed": True,
            "changed_cases_reviewed": not missing_writer_items,
            "changed_unchanged_boundary_reviewed": True,
            "stale_old_version_refs_absent": not stale_codes,
            "unchanged_hashes_preserved": all(item["byte_identical"] for item in unchanged),
            "full_suite_gates_passed": all(item["passed"] for item in gate_results),
            "independent_review_accepted": (
                independent_review_accepted
                if independent_review_path is not None
                else "not-required-shadow"
                if release_mode == "shadow"
                else False
            ),
        },
        "findings": review_findings,
        "gate_results": gate_results,
    }
    _write_json(run_dir / "update-review-result.json", review_result)

    published = False
    snapshots = run_dir / "snapshots"
    (snapshots / "before").mkdir(parents=True, exist_ok=True)
    _write_bytes_atomic(snapshots / "before" / canonical.name, canonical_bytes)
    (snapshots / "after-writer").mkdir(parents=True, exist_ok=True)
    _write_bytes_atomic(snapshots / "after-writer" / canonical.name, suite_bytes)
    if release_mode == "publish" and accepted:
        expected_target = _resolve(
            repo_root,
            output.get("canonical_path"),
            label="output.canonical_path",
            required=False,
        )
        if expected_target is None or expected_target != canonical:
            raise IncrementalUpdateError(
                "publish requires output.canonical_path equal to baseline canonical_test_cases"
            )
        if sha256_file(canonical) != sha256_bytes(canonical_bytes):
            raise IncrementalUpdateError("canonical test cases changed before incremental publication")
        _write_bytes_atomic(canonical, suite_bytes)
        (snapshots / "signed-off").mkdir(parents=True, exist_ok=True)
        _write_bytes_atomic(snapshots / "signed-off" / canonical.name, suite_bytes)
        published = True
    if published:
        status = "signed-off"
    elif accepted:
        status = "shadow-accepted"
    elif any(item["id"] == "UPDATE-AMBIGUOUS-MATCH" for item in review_findings):
        status = "review-failed"
    elif missing_writer_items:
        status = "writer-required"
    else:
        status = "review-failed"
    release_manifest = run_dir / "release-manifest.json"
    _write_json(
        release_manifest,
        {
            "schema_version": 1,
            "status": status,
            "created_at": utc_now(),
            "old_version_id": old.get("id"),
            "new_version_id": new.get("id"),
            "old_ft_hashes": {
                "docx": sha256_file(old_docx),
                "xhtml": sha256_file(old_xhtml),
                "pdf": sha256_file(old_pdf),
            },
            "new_ft_hashes": {
                "docx": sha256_file(new_docx),
                "xhtml": sha256_file(new_xhtml),
                "pdf": sha256_file(new_pdf),
            },
            "canonical_before_sha256": sha256_bytes(canonical_bytes),
            "shadow_sha256": sha256_bytes(suite_bytes),
            "canonical_after_sha256": sha256_file(canonical),
            "published": published,
            "writer_invocation_count": writer_invocation_count,
            "change_count": len(substantive_changes),
            "test_case_actions": plan,
            "artifacts": [
                "ft-version-diff.json",
                "ft-version-diff.md",
                "change-classification.json",
                "change-impact-matrix.md",
                "update-plan.md",
                "tc-reuse-manifest.json",
                "unchanged-region-manifest.json",
                "test-case-changelog.md",
                "release-manifest.json",
                "update-review-result.json",
                "writer-input-package.json",
            ],
        },
    )
    return IncrementalUpdateResult(
        status=status,
        run_dir=run_dir,
        shadow_suite=shadow_suite,
        release_manifest=release_manifest,
        writer_invocation_count=writer_invocation_count,
        change_count=len(substantive_changes),
        reused_case_count=len(unchanged),
        modified_case_count=sum(item["action"] != "reuse-byte-identical" for item in plan),
    )
