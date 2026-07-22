from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

from test_case_agent.review_cycle import source_assertions as source_assertions_module
from test_case_agent.review_cycle.source_assertions import (
    ApprovedClarification,
    ClarificationClauseBinding,
    MANIFEST_VERSION,
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    RegisteredEvidenceSource,
    RegisteredArtifact,
    RegisteredSource,
    SOURCE_REVIEW_DIMENSIONS,
    SUPPORTING_SOURCE_EVIDENCE_ROLES,
    ClauseEvidenceBinding,
    RequirementCodeBinding,
    ScopeBoundaryManifestContext,
    ScopeBoundaryExclusion,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionContractError,
    SourceAssertionManifest,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    SourceRow,
    SupportingSourceBinding,
    build_source_assertion_manifest as build_source_assertion_manifest_contract,
    load_source_assertion_manifest,
    load_source_assertion_review_receipt,
    load_legacy_source_assertion_manifest_diagnostic,
    migrate_source_assertion_manifest_v3_payload,
    parse_embedded_source_assertion_contract,
    render_embedded_source_assertion_contract,
    scope_boundary_source_locator,
    sha256_file,
    validate_source_assertion_manifest,
)


TEST_EXTRACTION_SPEC_DIGEST = "1" * 64
TEST_BASELINE_DIGEST = "2" * 64


def _test_candidate_id(source_row_id: str) -> str:
    suffix = hashlib.sha256(source_row_id.encode("utf-8")).hexdigest()[:24]
    return f"SRC-CAND-{suffix}"


def _write_text_pdf(path: Path, page_texts: tuple[str, ...]) -> None:
    from pypdf import PdfWriter
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    for value in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_ref}
                )
            }
        )
        stream = DecodedStreamObject()
        escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream.set_data(
            f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
        )
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as output:
        writer.write(output)


def build_source_assertion_manifest(repo_root: Path, **kwargs):
    """Test adapter: production callers must pass real baseline-bound values."""

    assertions = tuple(kwargs["assertions"])
    kwargs["assertions"] = assertions
    explicit_rows = kwargs.get("source_rows")
    if explicit_rows is None:
        row_ids = tuple(dict.fromkeys(item.source_row_id for item in assertions))
        kwargs["source_row_candidate_ids"] = {
            row_id: _test_candidate_id(row_id) for row_id in row_ids
        }
        candidate_count = len(row_ids)
    else:
        rows = tuple(
            row
            if row.candidate_id is not None
            else replace(row, candidate_id=_test_candidate_id(row.source_row_id))
            for row in explicit_rows
        )
        kwargs["source_rows"] = rows
        candidate_count = sum(row.candidate_id is not None for row in rows)
    kwargs.setdefault(
        "source_row_extraction_spec_digest", TEST_EXTRACTION_SPEC_DIGEST
    )
    kwargs.setdefault("source_row_baseline_digest", TEST_BASELINE_DIGEST)
    kwargs.setdefault("source_row_candidate_count", candidate_count)
    coverage_gaps = repo_root / "coverage-gaps.md"
    execution_by_gap: dict[str, list[SourceAssertion]] = {}
    for assertion in assertions:
        for gap_id in assertion.execution_dependency_gap_ids:
            execution_by_gap.setdefault(gap_id, []).append(assertion)
    primary_by_gap: dict[str, list[SourceAssertion]] = {}
    for assertion in assertions:
        if assertion.primary_gap_id is not None:
            primary_by_gap.setdefault(assertion.primary_gap_id, []).append(assertion)
    sections = ["# Coverage Gaps", ""]
    clarifications = tuple(kwargs.get("clarifications", ()))
    clarification_gap_ids = {item.gap_id for item in clarifications}
    for clarification in clarifications:
        sections.extend(
            (
                f"## {clarification.gap_id}",
                "",
                "| field | value |",
                "| --- | --- |",
                f"| gap_id | {clarification.gap_id} |",
                "| status | resolved |",
                "| resolution | approved-clarification:"
                + clarification.clarification_id
                + " |",
                "",
            )
        )
    for gap_id, gap_assertions in sorted(primary_by_gap.items()):
        if gap_id in execution_by_gap or gap_id in clarification_gap_ids:
            continue
        sections.extend(
            (
                f"## {gap_id}",
                "",
                "| field | value |",
                "| --- | --- |",
                f"| gap_id | {gap_id} |",
                "| status | open |",
                "| affected_assertion_id | "
                + "; ".join(item.assertion_id for item in gap_assertions)
                + " |",
                "| affected_atom_id | "
                + "; ".join(item.atom_id for item in gap_assertions)
                + " |",
                "",
            )
        )
    for gap_id, gap_assertions in sorted(execution_by_gap.items()):
        affected_assertions = tuple(
            {
                item.assertion_id: item
                for item in (*primary_by_gap.get(gap_id, ()), *gap_assertions)
            }.values()
        )
        sections.extend(
            (
                f"## {gap_id}",
                "",
                "**Impact:** `blocking`",
                "",
                "| field | value |",
                "| --- | --- |",
                f"| gap_id | {gap_id} |",
                "| affected_assertion_id | "
                + "; ".join(item.assertion_id for item in affected_assertions)
                + " |",
                "| affected_atom_id | "
                + "; ".join(item.atom_id for item in affected_assertions)
                + " |",
                "| execution_assertion_ids | "
                + "; ".join(item.assertion_id for item in gap_assertions)
                + " |",
                "| execution_atom_ids | "
                + "; ".join(item.atom_id for item in gap_assertions)
                + " |",
                "| execution_obligation_ids | "
                + "; ".join(
                    obligation_id
                    for item in gap_assertions
                    for obligation_id in item.obligation_ids
                )
                + " |",
                "| blocks_ready_for_review | yes |",
                "| status | open |",
                "",
            )
        )
    if not execution_by_gap and not primary_by_gap and not clarifications:
        sections.extend(("No gaps.", ""))
    coverage_gaps.write_text("\n".join(sections), encoding="utf-8")
    kwargs.setdefault("coverage_gaps_path", "coverage-gaps.md")
    return build_source_assertion_manifest_contract(repo_root, **kwargs)


class SourceAssertionManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo_root = Path(self.temporary.name)
        self.source_path = self.repo_root / "source" / "main.xhtml"
        self.source_path.parent.mkdir(parents=True)
        (self.repo_root / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\nNo gaps.\n",
            encoding="utf-8",
        )
        self.base_source_candidates = (
            "BSR 3. Поиск выполняется, если заполнено только поле Фамилия клиента.",
            "BSR 6. Поиск выполняется, если заполнено только поле Имя клиента.",
            "BSR 9. Поиск выполняется, если заполнено только поле Отчество клиента.",
            "Общие ограничения документа проверены вне выбранного manifest scope.",
            "Преамбула родительского раздела проверена вне выбранного manifest scope.",
            "Перекрёстные ссылки проверены вне выбранного manifest scope.",
        )
        self._write_source_candidates(*self.base_source_candidates)

    def _write_source_candidates(self, *texts: str) -> None:
        body = "".join(f"<p>{escape(text)}</p>" for text in texts)
        self._write_source_markup(
            body.replace("только поле", "только\u00a0поле")
        )

    def _write_source_markup(self, body: str) -> None:
        self.source_path.write_text(
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            + body
            + "</body></html>",
            encoding="utf-8",
            newline="",
        )

    @staticmethod
    def _assertion(
        number: int,
        field_name: str,
        *,
        source_path: str = "source/main.xhtml",
        assertion_id: str | None = None,
        source_row_id: str | None = None,
        atom_id: str | None = None,
        obligation_id: str | None = None,
        polarity: str = "positive",
        disposition: str = "testable",
    ) -> SourceAssertion:
        code = f"BSR {number}"
        row_position = {3: 1, 6: 2, 9: 3}[number]
        row_id = source_row_id or f"SRC-AMS-{number:03d}"
        exact = (
            f"{code}. Поиск выполняется, если заполнено только поле {field_name} клиента."
        )
        return SourceAssertion(
            assertion_id=assertion_id or f"ASSERT-BSR-{number:03d}",
            source_path=source_path,
            source_context_class="document-global-constraints",
            locator=f"/*/*[1]/*[{row_position}]",
            exact_source_text=exact,
            canonical_statement=(
                f"Поиск должен выполняться, когда заполнено только поле «{field_name} клиента»."
            ),
            polarity=polarity,
            semantic_disposition=disposition,
            execution_readiness="ready",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="high",
            condition_clauses=(
                f"Заполнено только поле «{field_name} клиента»; остальные фильтры пусты.",
            ),
            action_clauses=("Нажать «Найти».",),
            oracle_clauses=(
                f"Поиск выполняется по заполненному полю «{field_name} клиента».",
            ),
            requirement_codes=(code,),
            requirement_code_bindings=(
                RequirementCodeBinding(
                    requirement_code=code,
                    source_row_id=row_id,
                    provenance_role="xhtml-row",
                    exact_source_fragment=exact,
                ),
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=clause_kind,
                    clause_index=0,
                    source_row_id=row_id,
                    evidence_role=clause_kind,
                    exact_source_fragment=exact,
                )
                for clause_kind in ("condition", "action", "oracle")
            ),
            source_row_id=row_id,
            atom_id=atom_id or f"ATOM-AMS-{number:03d}",
            obligation_ids=(obligation_id or f"OBL-AMS-{number:03d}",),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
        )

    def _build(self, assertions: tuple[SourceAssertion, ...] | None = None):
        assertions = assertions or (
            self._assertion(3, "Фамилия"),
            self._assertion(6, "Имя"),
            self._assertion(9, "Отчество"),
        )
        return build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=assertions,
            expected_source_row_ids=tuple(item.source_row_id for item in assertions),
            approved_polarities={item.assertion_id: "positive" for item in assertions},
        )

    def _build_with_user_clarification(
        self,
        *,
        requirement_numbers: tuple[int, ...] = (3,),
        response_type: str = "user-confirmed",
        authority: str = "user",
        evidence_role: str = "approved-clarification",
        exact_answer: str = (
            "Поиск выполняется после заполнения только поля «Фамилия клиента»."
        ),
    ) -> tuple[SourceAssertionManifest, ApprovedClarification, Path]:
        clarification_path = self.repo_root / "scope-clarification-requests.md"
        clarification_id = "CLR-AMS-001"
        gap_id = "GAP-AMS-001"
        requirement_codes = tuple(
            f"BSR {number}" for number in requirement_numbers
        )
        clarification_path.write_text(
            "\n".join(
                (
                    "# Scope clarifications",
                    "",
                    "| clarification_id | gap_id | scope_slug | requirement_codes | authority | user_response | response_status | response_type | updated_at |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    f"| {clarification_id} | {gap_id} | applications-menu-search | {'; '.join(requirement_codes)} | {authority} | {exact_answer} | answered | {response_type} | 2026-07-15 |",
                    "",
                )
            ),
            encoding="utf-8",
        )
        answer_digest = hashlib.sha256(exact_answer.encode("utf-8")).hexdigest()
        clarification = ApprovedClarification(
            clarification_id=clarification_id,
            gap_id=gap_id,
            scope_slug="applications-menu-search",
            requirement_codes=requirement_codes,
            authority=authority,
            response_status="answered",
            response_type=response_type,
            answered_at="2026-07-15",
            exact_answer=exact_answer,
            exact_answer_sha256=answer_digest,
            evidence_source_path="scope-clarification-requests.md",
            evidence_source_sha256=sha256_file(clarification_path),
        )
        fields = {3: "Фамилия", 6: "Имя", 9: "Отчество"}
        assertions = tuple(
            replace(
                self._assertion(number, fields[number]),
                clarification_clause_bindings=(
                    ClarificationClauseBinding(
                        clarification_id=clarification_id,
                        clause_kind="oracle",
                        clause_index=0,
                        requirement_codes=(f"BSR {number}",),
                        exact_answer_sha256=answer_digest,
                    ),
                ),
            )
            for number in requirement_numbers
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=assertions,
            clarifications=(clarification,),
            evidence_sources=(("scope-clarification-requests.md", evidence_role),),
            expected_source_row_ids=tuple(
                assertion.source_row_id for assertion in assertions
            ),
            approved_polarities={
                assertion.assertion_id: assertion.polarity
                for assertion in assertions
            },
        )
        return manifest, clarification, clarification_path

    def _build_with_source_context_clarification(
        self,
    ) -> tuple[SourceAssertionManifest, ApprovedClarification, Path]:
        context_text = "Форма поиска заявок является основной формой раздела заявок."
        self._write_source_candidates(*self.base_source_candidates, context_text)
        clarification_path = self.repo_root / "scope-clarification-requests.md"
        clarification_id = "CLR-AMS-033"
        gap_id = "GAP-AMS-033"
        exact_answer = "Форма поиска заявок является основной формой раздела."
        clarification_path.write_text(
            "\n".join(
                (
                    "# Scope clarifications",
                    "",
                    "| clarification_id | gap_id | scope_slug | requirement_codes | authority | user_response | response_status | response_type | updated_at |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    f"| {clarification_id} | {gap_id} | applications-menu-search |  | user | {exact_answer} | answered | user-confirmed | 2026-07-15 |",
                    "",
                )
            ),
            encoding="utf-8",
        )
        answer_digest = hashlib.sha256(exact_answer.encode("utf-8")).hexdigest()
        clarification = ApprovedClarification(
            clarification_id=clarification_id,
            gap_id=gap_id,
            scope_slug="applications-menu-search",
            requirement_codes=(),
            authority="user",
            response_status="answered",
            response_type="user-confirmed",
            answered_at="2026-07-15",
            exact_answer=exact_answer,
            exact_answer_sha256=answer_digest,
            evidence_source_path="scope-clarification-requests.md",
            evidence_source_sha256=sha256_file(clarification_path),
            binding_scope="source-context",
            source_row_ids=("SRC-AMS-001",),
        )
        assertion = SourceAssertion(
            assertion_id="ASSERT-AMS-CONTEXT-001",
            source_path="source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]/*[7]",
            exact_source_text=context_text,
            canonical_statement="Форма поиска заявок является основной формой раздела.",
            polarity="positive",
            semantic_disposition="testable",
            execution_readiness="ready",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="medium",
            condition_clauses=("Открыт раздел заявок.",),
            action_clauses=("Открыть форму поиска заявок.",),
            oracle_clauses=("Отображается основная форма поиска заявок.",),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=clause_kind,
                    clause_index=0,
                    source_row_id="SRC-AMS-001",
                    evidence_role=clause_kind,
                    exact_source_fragment=context_text,
                )
                for clause_kind in ("condition", "action", "oracle")
            ),
            source_row_id="SRC-AMS-001",
            atom_id="ATOM-AMS-CONTEXT-001",
            obligation_ids=("OBL-AMS-CONTEXT-001",),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
            clarification_clause_bindings=(
                ClarificationClauseBinding(
                    clarification_id=clarification_id,
                    clause_kind="oracle",
                    clause_index=0,
                    requirement_codes=(),
                    exact_answer_sha256=answer_digest,
                    binding_scope="source-context",
                    source_row_ids=("SRC-AMS-001",),
                ),
            ),
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
            clarifications=(clarification,),
            evidence_sources=(("scope-clarification-requests.md", "approved-clarification"),),
            expected_source_row_ids=(assertion.source_row_id,),
            approved_polarities={assertion.assertion_id: assertion.polarity},
        )
        return manifest, clarification, clarification_path

    def _build_with_not_applicable_canonical_clarification(
        self,
    ) -> tuple[SourceAssertionManifest, ApprovedClarification, Path]:
        context_text = "Форма поиска заявок является основной формой раздела заявок."
        self._write_source_candidates(*self.base_source_candidates, context_text)
        clarification_path = self.repo_root / "scope-clarification-requests.md"
        clarification_id = "CLR-AMS-033"
        gap_id = "GAP-AMS-033"
        exact_answer = "Форма поиска заявок является основной формой раздела."
        clarification_path.write_text(
            "\n".join(
                (
                    "# Scope clarifications",
                    "",
                    "| clarification_id | gap_id | scope_slug | requirement_codes | authority | user_response | response_status | response_type | updated_at |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    f"| {clarification_id} | {gap_id} | applications-menu-search |  | user | {exact_answer} | answered | user-confirmed | 2026-07-15 |",
                    "",
                )
            ),
            encoding="utf-8",
        )
        answer_digest = hashlib.sha256(exact_answer.encode("utf-8")).hexdigest()
        clarification = ApprovedClarification(
            clarification_id=clarification_id,
            gap_id=gap_id,
            scope_slug="applications-menu-search",
            requirement_codes=(),
            authority="user",
            response_status="answered",
            response_type="user-confirmed",
            answered_at="2026-07-15",
            exact_answer=exact_answer,
            exact_answer_sha256=answer_digest,
            evidence_source_path="scope-clarification-requests.md",
            evidence_source_sha256=sha256_file(clarification_path),
            binding_scope="source-context",
            source_row_ids=("SRC-AMS-001",),
        )
        assertion = SourceAssertion(
            assertion_id="ASSERT-AMS-CONTEXT-001",
            source_path="source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]/*[7]",
            exact_source_text=context_text,
            canonical_statement="Форма поиска заявок является основной формой раздела.",
            polarity="neutral",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="medium",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            source_row_id="SRC-AMS-001",
            atom_id="ATOM-AMS-CONTEXT-001",
            obligation_ids=(),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
            disposition_rationale=(
                "Уточнение фиксирует только контекст основной формы и не задаёт "
                "самостоятельного исполнимого поведения системы."
            ),
            clarification_clause_bindings=(
                ClarificationClauseBinding(
                    clarification_id=clarification_id,
                    clause_kind="canonical",
                    clause_index=0,
                    requirement_codes=(),
                    exact_answer_sha256=answer_digest,
                    binding_scope="source-context",
                    source_row_ids=("SRC-AMS-001",),
                ),
            ),
        )
        source_row = SourceRow(
            source_row_id=assertion.source_row_id,
            source_path=assertion.source_path,
            source_locator=assertion.locator,
            bounded_source_text=assertion.exact_source_text,
            source_context_class=assertion.source_context_class,
            candidate_id=None,
            scope_disposition="yes",
            requirement_codes=(),
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
            source_rows=(source_row,),
            clarifications=(clarification,),
            evidence_sources=(("scope-clarification-requests.md", "approved-clarification"),),
            expected_source_row_ids=(assertion.source_row_id,),
            approved_polarities={assertion.assertion_id: assertion.polarity},
        )
        return manifest, clarification, clarification_path

    @staticmethod
    def _source_row(assertion: SourceAssertion) -> SourceRow:
        return SourceRow(
            source_row_id=assertion.source_row_id,
            source_path=assertion.source_path,
            source_locator=assertion.locator,
            bounded_source_text=assertion.exact_source_text,
            source_context_class=assertion.source_context_class,
            candidate_id=_test_candidate_id(assertion.source_row_id),
            scope_disposition=(
                "no"
                if assertion.semantic_disposition == "not-applicable"
                else (
                    "unclear"
                    if assertion.semantic_disposition == "ambiguous"
                    else "yes"
                )
            ),
            requirement_codes=assertion.requirement_codes,
        )

    @staticmethod
    def _retarget_source_contract(
        assertion: SourceAssertion,
        *,
        exact_source_text: str,
        source_row_id: str,
        requirement_codes: tuple[str, ...],
        provenance_role: str = "xhtml-row",
    ) -> SourceAssertion:
        return replace(
            assertion,
            exact_source_text=exact_source_text,
            source_row_id=source_row_id,
            requirement_codes=requirement_codes,
            requirement_code_bindings=tuple(
                RequirementCodeBinding(
                    requirement_code=code,
                    source_row_id=source_row_id,
                    provenance_role=provenance_role,
                    exact_source_fragment=(
                        exact_source_text if provenance_role == "xhtml-row" else None
                    ),
                )
                for code in requirement_codes
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=kind,
                    clause_index=index,
                    source_row_id=source_row_id,
                    evidence_role=kind,
                    exact_source_fragment=exact_source_text,
                )
                for kind, clauses in (
                    ("condition", assertion.condition_clauses),
                    ("action", assertion.action_clauses),
                    ("oracle", assertion.oracle_clauses),
                )
                for index in range(len(clauses))
            ),
        )

    @staticmethod
    def _as_not_applicable(
        assertion: SourceAssertion,
        *,
        context_class: str | None = None,
    ) -> SourceAssertion:
        return replace(
            assertion,
            source_context_class=context_class or assertion.source_context_class,
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=(),
            disposition_rationale=(
                "Эта source row проверенно исключена из выбранного scope."
            ),
        )

    def _not_applicable_code_assertion(
        self,
        *,
        requirement_code: str,
        source_row_id: str,
        source_text: str,
        assertion_suffix: str,
    ) -> SourceAssertion:
        assertion = self._retarget_source_contract(
            self._assertion(3, "Фамилия"),
            exact_source_text=source_text,
            source_row_id=source_row_id,
            requirement_codes=(requirement_code,),
        )
        return replace(
            self._as_not_applicable(assertion),
            assertion_id=f"ASSERT-AMS-NO-{assertion_suffix}",
            atom_id=f"ATOM-AMS-NO-{assertion_suffix}",
            canonical_statement=(
                f"{requirement_code} сохранён как проверенное исключение из scope."
            ),
            polarity="neutral",
        )

    @staticmethod
    def _scope_boundary(
        manifest: SourceAssertionManifest,
        *,
        verdict: str = "verified",
        reviewed_manifest_contexts: tuple[ScopeBoundaryManifestContext, ...] | None = None,
        excluded_contexts: tuple[ScopeBoundaryExclusion, ...] | None = None,
        required_change: str | None = None,
    ) -> ScopeBoundaryReview:
        if reviewed_manifest_contexts is None:
            reviewed_manifest_contexts = tuple(
                ScopeBoundaryManifestContext(
                    context_class=item.source_context_class,
                    source_row_id=item.source_row_id,
                )
                for item in manifest.source_rows
                if item.source_context_class
                in {
                        "document-global-constraints",
                        "ancestor-and-section-preamble",
                        "cross-referenced-constraints",
                }
            )
        if excluded_contexts is None:
            sources_by_path = {item.path: item for item in manifest.sources}
            reviewed_classes = {
                item.context_class for item in reviewed_manifest_contexts
            }
            external_context_text = {
                "document-global-constraints": (
                    "Общие ограничения документа проверены вне выбранного manifest scope."
                ),
                "ancestor-and-section-preamble": (
                    "Преамбула родительского раздела проверена вне выбранного manifest scope."
                ),
                "cross-referenced-constraints": (
                    "Перекрёстные ссылки проверены вне выбранного manifest scope."
                ),
            }
            excluded_contexts = tuple(
                ScopeBoundaryExclusion(
                    context_class=context_class,
                    source_path="source/main.xhtml",
                    source_sha256=sources_by_path["source/main.xhtml"].sha256,
                    source_locator=scope_boundary_source_locator(
                        "source/main.xhtml",
                        exact_text,
                    ),
                    exact_source_text=exact_text,
                    reason=(
                        "Проверенный контекст находится вне manifest source-row registry."
                    ),
                )
                for context_class, exact_text in external_context_text.items()
                if context_class
                in {
                    "document-global-constraints",
                    "ancestor-and-section-preamble",
                    "cross-referenced-constraints",
                }
                and context_class not in reviewed_classes
            )
        return ScopeBoundaryReview(
            verdict=verdict,
            checked_context_classes=(
                "document-global-constraints",
                "ancestor-and-section-preamble",
                "cross-referenced-constraints",
            ),
            reviewed_manifest_contexts=reviewed_manifest_contexts,
            excluded_contexts=excluded_contexts,
            required_change=(
                required_change
                if required_change is not None
                else (
                    NO_REQUIRED_CHANGE
                    if verdict == "verified"
                    else "Исправить классификацию границ выбранного scope."
                )
            ),
            note="Границы scope сверены с контекстом всего документа.",
        )

    @staticmethod
    def _inventory_review(
        manifest: SourceAssertionManifest,
        *,
        verdict: str = "verified",
        required_change: str | None = None,
    ) -> SourceInventoryReview:
        return SourceInventoryReview(
            extraction_spec_digest=manifest.source_row_extraction_spec_digest,
            baseline_digest=manifest.source_row_baseline_digest,
            candidate_count=manifest.source_row_candidate_count,
            mapped_source_row_count=sum(
                item.candidate_id is not None for item in manifest.source_rows
            ),
            verdict=verdict,
            required_change=(
                required_change
                if required_change is not None
                else (
                    NO_REQUIRED_CHANGE
                    if verdict == "verified"
                    else "Исправить неполную классификацию source-row inventory."
                )
            ),
            note="Candidate baseline и mapping строк независимо проверены полностью.",
        )

    @staticmethod
    def _dimension_verdicts(*incorrect: str) -> dict[str, str]:
        incorrect_set = set(incorrect)
        return {
            dimension: "incorrect" if dimension in incorrect_set else "verified"
            for dimension in SOURCE_REVIEW_DIMENSIONS
        }

    @classmethod
    def _review(
        cls,
        assertion: SourceAssertion,
        *,
        incorrect_dimensions: tuple[str, ...] = (),
        approved_polarity: str | None = None,
        approved_semantic_disposition: str | None = None,
        approved_execution_readiness: str | None = None,
        approved_risk: str | None = None,
        required_change: str | None = None,
    ) -> SourceAssertionReview:
        verdict = "incorrect" if incorrect_dimensions else "verified"
        return SourceAssertionReview(
            assertion_id=assertion.assertion_id,
            approved_polarity=approved_polarity or assertion.polarity,
            approved_semantic_disposition=(
                approved_semantic_disposition or assertion.semantic_disposition
            ),
            approved_execution_readiness=(
                approved_execution_readiness or assertion.execution_readiness
            ),
            approved_risk=approved_risk or assertion.risk,
            dimension_verdicts=cls._dimension_verdicts(*incorrect_dimensions),
            verdict=verdict,
            required_change=(
                required_change
                if required_change is not None
                else (
                    "Исправить ошибочную классификацию assertion."
                    if incorrect_dimensions
                    else NO_REQUIRED_CHANGE
                )
            ),
            note="Сверено с точным фрагментом XHTML.",
        )

    def assert_contract_error(self, code: str, callback) -> SourceAssertionContractError:
        with self.assertRaises(SourceAssertionContractError) as context:
            callback()
        self.assertEqual(code, context.exception.code)
        return context.exception

    def test_build_load_digest_and_compact_reviewer_basis(self) -> None:
        manifest = self._build()
        manifest_path = self.repo_root / "source-assertions.json"
        manifest_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        restored = load_source_assertion_manifest(
            manifest_path,
            self.repo_root,
            expected_source_row_ids=("SRC-AMS-003", "SRC-AMS-006", "SRC-AMS-009"),
            approved_polarities={
                "ASSERT-BSR-003": "positive",
                "ASSERT-BSR-006": "positive",
                "ASSERT-BSR-009": "positive",
            },
        )

        self.assertEqual(manifest.digest, restored.digest)
        self.assertRegex(restored.digest, r"^[0-9a-f]{64}$")
        basis = restored.to_compact_reviewer_basis()
        self.assertEqual("bounded-source-first-assertions-v4", basis["contract"])
        self.assertEqual(restored.digest, basis["manifest_digest"])
        self.assertEqual(3, len(basis["assertions"]))
        self.assertIn("BSR 3", restored.compact_reviewer_basis_json())

    def test_user_confirmed_clarification_is_hash_and_clause_bound(self) -> None:
        manifest, clarification, _ = self._build_with_user_clarification(
            requirement_numbers=(3, 6, 9),
        )

        manifest.validate(self.repo_root)
        basis = manifest.to_compact_reviewer_basis()
        self.assertEqual(
            clarification.to_dict(),
            basis["clarifications"][0],
        )
        self.assertEqual(
            {"BSR 3", "BSR 6", "BSR 9"},
            {
                code
                for assertion in manifest.assertions
                for binding in assertion.clarification_clause_bindings
                for code in binding.requirement_codes
            },
        )
        self.assertEqual("user", clarification.authority)
        self.assertEqual("user-confirmed", clarification.response_type)

    def test_source_context_clarification_binds_exact_in_scope_source_row(self) -> None:
        manifest, clarification, _ = self._build_with_source_context_clarification()

        manifest.validate(self.repo_root)
        binding = manifest.assertions[0].clarification_clause_bindings[0]
        self.assertEqual("source-context", clarification.binding_scope)
        self.assertEqual((), clarification.requirement_codes)
        self.assertEqual(("SRC-AMS-001",), clarification.source_row_ids)
        self.assertEqual("source-context", binding.binding_scope)
        self.assertEqual((), binding.requirement_codes)
        self.assertEqual(("SRC-AMS-001",), binding.source_row_ids)
        serialized = manifest.to_dict()
        self.assertEqual(
            "source-context",
            serialized["clarifications"][0]["binding_scope"],
        )
        self.assertEqual(
            ["SRC-AMS-001"],
            serialized["clarifications"][0]["source_row_ids"],
        )

    def test_not_applicable_canonical_clarification_binds_context_without_obligation(self) -> None:
        manifest, clarification, _ = (
            self._build_with_not_applicable_canonical_clarification()
        )

        manifest.validate(self.repo_root)
        assertion = manifest.assertions[0]
        binding = assertion.clarification_clause_bindings[0]
        self.assertEqual("not-applicable", assertion.semantic_disposition)
        self.assertEqual("not-applicable", assertion.execution_readiness)
        self.assertEqual((), assertion.condition_clauses)
        self.assertEqual((), assertion.action_clauses)
        self.assertEqual((), assertion.oracle_clauses)
        self.assertEqual((), assertion.obligation_ids)
        self.assertEqual("canonical", binding.clause_kind)
        self.assertEqual(0, binding.clause_index)
        self.assertEqual("source-context", binding.binding_scope)
        self.assertEqual(clarification.exact_answer_sha256, binding.exact_answer_sha256)
        restored = SourceAssertionManifest.from_dict(manifest.to_dict())
        restored.validate(self.repo_root)
        self.assertEqual(
            "canonical",
            restored.assertions[0].clarification_clause_bindings[0].clause_kind,
        )

    def test_excluded_source_context_clarification_binds_canonical_na_row(self) -> None:
        manifest, _, _ = self._build_with_not_applicable_canonical_clarification()
        excluded_manifest = replace(
            manifest,
            source_rows=(
                replace(manifest.source_rows[0], scope_disposition="no"),
            ),
        )

        excluded_manifest.validate(self.repo_root)
        assertion = excluded_manifest.assertions[0]
        self.assertEqual("not-applicable", assertion.semantic_disposition)
        self.assertEqual((), assertion.obligation_ids)
        self.assertEqual(
            "canonical",
            assertion.clarification_clause_bindings[0].clause_kind,
        )

    def test_canonical_clarification_rejects_testable_and_ambiguous_assertions(self) -> None:
        manifest, _, _ = self._build_with_not_applicable_canonical_clarification()
        assertion = manifest.assertions[0]
        executable_clauses = {
            "condition_clauses": ("Открыта форма заявок.",),
            "action_clauses": ("Открыть форму поиска.",),
            "oracle_clauses": ("Отображается основная форма поиска.",),
        }
        executable_evidence = tuple(
            ClauseEvidenceBinding(
                clause_kind=clause_kind,
                clause_index=0,
                source_row_id=assertion.source_row_id,
                evidence_role=clause_kind,
                exact_source_fragment=assertion.exact_source_text,
            )
            for clause_kind in ("condition", "action", "oracle")
        )

        self.assert_contract_error(
            "clarification-canonical-disposition-invalid",
            lambda: replace(
                assertion,
                semantic_disposition="testable",
                execution_readiness="ready",
                condition_clauses=executable_clauses["condition_clauses"],
                action_clauses=executable_clauses["action_clauses"],
                oracle_clauses=executable_clauses["oracle_clauses"],
                clause_evidence_bindings=executable_evidence,
                obligation_ids=("OBL-AMS-CONTEXT-001",),
                disposition_rationale="",
            ).validate_shape(),
        )
        self.assert_contract_error(
            "clarification-canonical-disposition-invalid",
            lambda: replace(
                assertion,
                semantic_disposition="ambiguous",
                execution_readiness="dependency-blocked",
                execution_readiness_rationale=(
                    "Исполнение заблокировано до устранения неоднозначности контекста."
                ),
                primary_gap_id="GAP-AMS-099",
                disposition_rationale=(
                    "Источник не определяет однозначное исполнимое поведение для этого контекста."
                ),
            ).validate_shape(),
        )

    def test_canonical_clarification_rejects_requirement_code_scope_and_nonzero_index(self) -> None:
        manifest, _, _ = self._build_with_not_applicable_canonical_clarification()
        binding = manifest.assertions[0].clarification_clause_bindings[0]

        self.assert_contract_error(
            "clarification-canonical-binding-scope-invalid",
            lambda: replace(
                binding,
                binding_scope="requirement-code",
                requirement_codes=("BSR 31",),
                source_row_ids=(),
            ).validate_shape(),
        )
        self.assert_contract_error(
            "clarification-canonical-index-invalid",
            lambda: replace(binding, clause_index=1).validate_shape(),
        )

    def test_canonical_clarification_preserves_hash_and_orphan_guards(self) -> None:
        manifest, _, _ = self._build_with_not_applicable_canonical_clarification()
        assertion = manifest.assertions[0]
        binding = assertion.clarification_clause_bindings[0]

        self.assert_contract_error(
            "clarification-binding-answer-digest-mismatch",
            lambda: replace(
                manifest,
                assertions=(
                    replace(
                        assertion,
                        clarification_clause_bindings=(
                            replace(binding, exact_answer_sha256="0" * 64),
                        ),
                    ),
                ),
            ).validate(self.repo_root),
        )
        self.assert_contract_error(
            "orphan-approved-clarification",
            lambda: replace(
                manifest,
                assertions=(
                    replace(assertion, clarification_clause_bindings=()),
                ),
            ).validate(self.repo_root),
        )

    def test_empty_clarification_codes_require_explicit_source_context_row(self) -> None:
        manifest, clarification, _ = self._build_with_source_context_clarification()
        assertion = manifest.assertions[0]

        self.assert_contract_error(
            "clarification-requirement-codes-missing",
            lambda: replace(
                clarification,
                binding_scope="requirement-code",
                source_row_ids=(),
            ).validate_shape(),
        )
        self.assert_contract_error(
            "clarification-source-context-rows-missing",
            lambda: replace(clarification, source_row_ids=()).validate_shape(),
        )
        self.assert_contract_error(
            "clarification-binding-source-context-rows-missing",
            lambda: replace(
                assertion.clarification_clause_bindings[0],
                source_row_ids=(),
            ).validate_shape(),
        )

    def test_source_context_clarification_accepts_markdown_empty_code_marker(self) -> None:
        self.assertEqual(
            (),
            source_assertions_module._clarification_requirement_codes(
                "-",
                allow_empty=True,
            ),
        )

    def test_clarification_requirement_code_range_expands_to_exact_codes(self) -> None:
        self.assertEqual(
            ("BSR 105", "BSR 106", "BSR 107", "BSR 108"),
            source_assertions_module._clarification_requirement_codes(
                "BSR 105–108",
            ),
        )

    def test_clarification_requirement_code_range_rejects_reversed_bounds(self) -> None:
        self.assert_contract_error(
            "invalid-clarification-requirement-code-range",
            lambda: source_assertions_module._clarification_requirement_codes(
                "BSR 108-105",
            ),
        )

    def test_source_context_clarification_cannot_bind_foreign_assertion_row(self) -> None:
        manifest, clarification, _ = self._build_with_source_context_clarification()
        context_assertion = manifest.assertions[0]
        foreign_assertion = self._assertion(3, "Фамилия")
        foreign_row = self._source_row(foreign_assertion)
        foreign_binding = replace(
            context_assertion.clarification_clause_bindings[0],
            source_row_ids=(foreign_assertion.source_row_id,),
        )
        mutated = replace(
            manifest,
            assertions=(
                replace(
                    context_assertion,
                    clarification_clause_bindings=(foreign_binding,),
                ),
                foreign_assertion,
            ),
            source_rows=(*manifest.source_rows, foreign_row),
            source_row_candidate_count=2,
            clarifications=(
                replace(
                    clarification,
                    source_row_ids=(foreign_assertion.source_row_id,),
                ),
            ),
        )

        self.assert_contract_error(
            "clarification-assertion-source-context-row-mismatch",
            lambda: mutated.validate(self.repo_root),
        )

    def test_source_context_clarification_rejects_unbound_excluded_source_row(self) -> None:
        manifest, clarification, _ = self._build_with_source_context_clarification()
        context_assertion = manifest.assertions[0]
        ignored_assertion = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            obligation_ids=(),
            disposition_rationale="The row is explicitly outside the selected scope.",
        )
        ignored_row = replace(
            self._source_row(ignored_assertion),
            scope_disposition="no",
        )
        mutated = replace(
            manifest,
            assertions=(context_assertion, ignored_assertion),
            source_rows=(*manifest.source_rows, ignored_row),
            source_row_candidate_count=2,
            clarifications=(
                replace(
                    clarification,
                    source_row_ids=(
                        context_assertion.source_row_id,
                        ignored_assertion.source_row_id,
                    ),
                ),
            ),
        )

        self.assert_contract_error(
            "clarification-binding-source-context-row-set-mismatch",
            lambda: mutated.validate(self.repo_root),
        )

    def test_legacy_v4_requirement_code_clarification_infers_new_binding_fields(self) -> None:
        manifest, _, _ = self._build_with_user_clarification()
        payload = manifest.to_dict()
        for clarification_payload in payload["clarifications"]:
            clarification_payload.pop("binding_scope")
            clarification_payload.pop("source_row_ids")
        for assertion_payload in payload["assertions"]:
            for binding_payload in assertion_payload["clarification_clause_bindings"]:
                binding_payload.pop("binding_scope")
                binding_payload.pop("source_row_ids")

        restored = SourceAssertionManifest.from_dict(payload)
        restored.validate(self.repo_root)

        self.assertEqual("requirement-code", restored.clarifications[0].binding_scope)
        self.assertEqual((), restored.clarifications[0].source_row_ids)
        serialized = restored.to_dict()
        self.assertIn("binding_scope", serialized["clarifications"][0])
        self.assertIn("source_row_ids", serialized["clarifications"][0])

    def test_manifest_json_cannot_omit_clarification_registry(self) -> None:
        payload = self._build().to_dict()
        payload.pop("clarifications")

        self.assert_contract_error(
            "invalid-fields",
            lambda: SourceAssertionManifest.from_dict(payload),
        )

    def test_clarification_binding_requires_registered_typed_record(self) -> None:
        manifest, _, _ = self._build_with_user_clarification()

        self.assert_contract_error(
            "clarification-binding-unregistered",
            lambda: replace(manifest, clarifications=()).validate(self.repo_root),
        )

    def test_clarification_evidence_requires_registered_dedicated_role(self) -> None:
        manifest, _, _ = self._build_with_user_clarification()
        self.assert_contract_error(
            "clarification-evidence-unregistered",
            lambda: replace(manifest, evidence_sources=()).validate(self.repo_root),
        )
        self.assert_contract_error(
            "clarification-evidence-role-mismatch",
            lambda: replace(
                manifest,
                evidence_sources=(
                    replace(
                        manifest.evidence_sources[0],
                        role="supporting-material",
                    ),
                ),
            ).validate(self.repo_root),
        )

    def test_unapproved_clarification_response_cannot_bind_ready_semantics(self) -> None:
        for response_type in ("working-assumption", "rejected", "not-provided"):
            with self.subTest(response_type=response_type):
                self.assert_contract_error(
                    "unapproved-clarification-response-type",
                    lambda response_type=response_type: (
                        self._build_with_user_clarification(
                            response_type=response_type,
                        )
                    ),
                )
        manifest, clarification, _ = self._build_with_user_clarification()
        for response_status in ("superseded", "rejected", "unanswered"):
            with self.subTest(response_status=response_status):
                self.assert_contract_error(
                    "unapproved-clarification-response-status",
                    lambda response_status=response_status: replace(
                        manifest,
                        clarifications=(
                            replace(
                                clarification,
                                response_status=response_status,
                            ),
                        ),
                    ).validate(self.repo_root),
                )

    def test_clarification_authority_cannot_be_misrepresented(self) -> None:
        self.assert_contract_error(
            "clarification-authority-response-type-mismatch",
            lambda: self._build_with_user_clarification(
                authority="analyst",
                response_type="user-confirmed",
            ),
        )

    def test_changed_clarification_evidence_stales_manifest(self) -> None:
        manifest, _, clarification_path = self._build_with_user_clarification()
        clarification_path.write_text(
            clarification_path.read_text(encoding="utf-8").replace(
                "Поиск выполняется после заполнения только поля «Фамилия клиента».",
                "Поиск не выполняется после заполнения только поля «Фамилия клиента».",
            ),
            encoding="utf-8",
        )

        self.assert_contract_error(
            "stale-evidence-source-sha256",
            lambda: manifest.validate(self.repo_root),
        )

    def test_all_current_scope_answered_approved_rows_must_be_registered(self) -> None:
        manifest, clarification, clarification_path = (
            self._build_with_user_clarification()
        )
        clarification_path.write_text(
            clarification_path.read_text(encoding="utf-8").rstrip()
            + "\n"
            + "| CLR-AMS-UNREGISTERED | GAP-AMS-UNREGISTERED | "
            "applications-menu-search | BSR 99 | user | "
            "Second approved answer. | answered | user-confirmed | 2026-07-15 |\n",
            encoding="utf-8",
        )
        evidence_sha = sha256_file(clarification_path)
        updated_manifest = replace(
            manifest,
            clarifications=(
                replace(clarification, evidence_source_sha256=evidence_sha),
            ),
            evidence_sources=tuple(
                replace(item, sha256=evidence_sha)
                if item.path == clarification.evidence_source_path
                else item
                for item in manifest.evidence_sources
            ),
        )

        self.assert_contract_error(
            "clarification-record-set-mismatch",
            lambda: updated_manifest.validate(self.repo_root),
        )

    def test_nonapproved_or_other_scope_clarification_rows_are_not_promoted(self) -> None:
        manifest, clarification, clarification_path = (
            self._build_with_user_clarification()
        )
        clarification_path.write_text(
            clarification_path.read_text(encoding="utf-8").rstrip()
            + "\n"
            + "| CLR-AMS-WORKING | GAP-AMS-WORKING | applications-menu-search | "
            "BSR 99 | user | Working assumption. | answered | working-assumption | "
            "2026-07-15 |\n"
            + "| CLR-OTHER-APPROVED | GAP-OTHER-APPROVED | other-scope | "
            "BSR 100 | user | Other scope answer. | answered | user-confirmed | "
            "2026-07-15 |\n",
            encoding="utf-8",
        )
        evidence_sha = sha256_file(clarification_path)
        updated_manifest = replace(
            manifest,
            clarifications=(
                replace(clarification, evidence_source_sha256=evidence_sha),
            ),
            evidence_sources=tuple(
                replace(item, sha256=evidence_sha)
                if item.path == clarification.evidence_source_path
                else item
                for item in manifest.evidence_sources
            ),
        )

        updated_manifest.validate(self.repo_root)

    def test_clarification_binding_requires_exact_answer_digest(self) -> None:
        manifest, _, _ = self._build_with_user_clarification()
        assertion = manifest.assertions[0]
        bad_binding = replace(
            assertion.clarification_clause_bindings[0],
            exact_answer_sha256="0" * 64,
        )

        self.assert_contract_error(
            "clarification-binding-answer-digest-mismatch",
            lambda: replace(
                manifest,
                assertions=(
                    replace(
                        assertion,
                        clarification_clause_bindings=(bad_binding,),
                    ),
                ),
            ).validate(self.repo_root),
        )

    def test_shared_clarification_enforces_local_and_complete_code_binding(self) -> None:
        manifest, _, _ = self._build_with_user_clarification(
            requirement_numbers=(3, 6, 9),
        )
        first, second, third = manifest.assertions
        all_codes_on_first = replace(
            first.clarification_clause_bindings[0],
            requirement_codes=("BSR 3", "BSR 6", "BSR 9"),
        )
        self.assert_contract_error(
            "clarification-assertion-requirement-code-mismatch",
            lambda: replace(
                manifest,
                assertions=(
                    replace(
                        first,
                        clarification_clause_bindings=(all_codes_on_first,),
                    ),
                    second,
                    third,
                ),
            ).validate(self.repo_root),
        )

        self.assert_contract_error(
            "clarification-binding-requirement-code-set-mismatch",
            lambda: replace(
                manifest,
                assertions=(first, second, replace(third, clarification_clause_bindings=())),
            ).validate(self.repo_root),
        )

        unknown_code = replace(
            first.clarification_clause_bindings[0],
            requirement_codes=("BSR 99",),
        )
        self.assert_contract_error(
            "clarification-requirement-code-mismatch",
            lambda: replace(
                manifest,
                assertions=(
                    replace(
                        first,
                        clarification_clause_bindings=(unknown_code,),
                    ),
                    second,
                    third,
                ),
            ).validate(self.repo_root),
        )

    def test_definition_gap_does_not_reject_an_existing_clarification_binding(self) -> None:
        manifest, _, _ = self._build_with_user_clarification(
            requirement_numbers=(3, 6, 9),
        )
        gap_path = self.repo_root / manifest.coverage_gaps_artifact.path
        second = manifest.assertions[1]
        gap_path.write_text(
            gap_path.read_text(encoding="utf-8").rstrip()
            + "\n\n"
            + "\n".join(
                (
                    "## GAP-DEF-001",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| gap_id | GAP-DEF-001 |",
                    "| gap_type | missing-source-definition |",
                    "| requirement_codes | BSR 6 |",
                    f"| affected_assertion_id | {second.assertion_id} |",
                    f"| affected_atom_id | {second.atom_id} |",
                    "| status | open |",
                    "",
                )
            ),
            encoding="utf-8",
        )
        replace(
            manifest,
            coverage_gaps_artifact=replace(
                manifest.coverage_gaps_artifact,
                sha256=sha256_file(gap_path),
            ),
        ).validate(self.repo_root)

    def test_clarification_gap_must_be_resolved_by_exact_record(self) -> None:
        manifest, clarification, _ = self._build_with_user_clarification()
        gap_path = self.repo_root / manifest.coverage_gaps_artifact.path
        original = gap_path.read_text(encoding="utf-8")
        assertion = manifest.assertions[0]
        for expected_code, mutated in (
            (
                "clarification-gap-not-resolved",
                original.replace("| status | resolved |", "| status | open |"),
            ),
            (
                "clarification-gap-resolution-mismatch",
                original.replace(
                    f"approved-clarification:{clarification.clarification_id}",
                    "approved-clarification:CLR-OTHER",
                ),
            ),
            (
                "resolved-clarification-gap-has-execution-chain",
                original.replace(
                    "| status | resolved |",
                    "\n".join(
                        (
                            f"| execution_assertion_ids | {assertion.assertion_id} |",
                            f"| execution_atom_ids | {assertion.atom_id} |",
                            "| execution_obligation_ids | "
                            + "; ".join(assertion.obligation_ids)
                            + " |",
                            "| status | resolved |",
                        )
                    ),
                ),
            ),
        ):
            with self.subTest(expected_code=expected_code):
                gap_path.write_text(mutated, encoding="utf-8")
                updated_manifest = replace(
                    manifest,
                    coverage_gaps_artifact=replace(
                        manifest.coverage_gaps_artifact,
                        sha256=sha256_file(gap_path),
                    ),
                )
                self.assert_contract_error(
                    expected_code,
                    lambda updated_manifest=updated_manifest: (
                        updated_manifest.validate(self.repo_root)
                    ),
                )
        gap_path.write_text(original, encoding="utf-8")

    def test_v3_is_diagnostic_only_and_migration_requires_zero_clarification_confirmation(self) -> None:
        payload = self._build().to_dict()
        payload["version"] = 3
        payload.pop("clarifications")
        for assertion in payload["assertions"]:
            assertion.pop("clarification_clause_bindings")
        legacy_path = self.repo_root / "source-assertions.v3.json"
        legacy_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        diagnostic = load_legacy_source_assertion_manifest_diagnostic(legacy_path)
        self.assertFalse(diagnostic.production_eligible)
        self.assertFalse(diagnostic.migration_available)
        self.assert_contract_error(
            "legacy-manifest-requires-rematerialization",
            lambda: SourceAssertionManifest.from_dict(payload),
        )
        self.assert_contract_error(
            "source-manifest-migration-confirmation-required",
            lambda: migrate_source_assertion_manifest_v3_payload(
                payload,
                confirm_no_approved_clarifications=False,
            ),
        )
        migrated = migrate_source_assertion_manifest_v3_payload(
            payload,
            confirm_no_approved_clarifications=True,
        )
        self.assertEqual(MANIFEST_VERSION, migrated["version"])
        self.assertEqual([], migrated["clarifications"])
        SourceAssertionManifest.from_dict(migrated).validate(self.repo_root)
        confirmed_diagnostic = load_legacy_source_assertion_manifest_diagnostic(
            legacy_path,
            confirm_no_approved_clarifications=True,
        )
        self.assertFalse(confirmed_diagnostic.production_eligible)
        self.assertTrue(confirmed_diagnostic.migration_available)
        self.assertEqual(
            SourceAssertionManifest.from_dict(migrated).digest,
            confirmed_diagnostic.migrated_manifest_digest,
        )

    def test_manifest_requires_explicit_candidate_mapping_for_inferred_rows(self) -> None:
        assertion = self._assertion(3, "Фамилия")
        self.assert_contract_error(
            "source-candidate-mapping-required",
            lambda: build_source_assertion_manifest_contract(
                self.repo_root,
                scope_slug="applications-menu-search",
                coverage_gaps_path="coverage-gaps.md",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
                source_row_baseline_digest=TEST_BASELINE_DIGEST,
                source_row_candidate_count=1,
            ),
        )

    def test_manifest_rejects_invalid_duplicate_and_mismatched_candidate_mapping(self) -> None:
        assertion = self._assertion(3, "Фамилия")
        valid_row = self._source_row(assertion)
        for code, rows, candidate_count in (
            (
                "invalid-source-candidate-id",
                (replace(valid_row, candidate_id="SRC-CAND-invalid"),),
                1,
            ),
            (
                "duplicate-source-candidate-mapping",
                (
                    valid_row,
                    replace(
                        self._source_row(self._assertion(6, "Имя")),
                        candidate_id=valid_row.candidate_id,
                    ),
                ),
                2,
            ),
            (
                "source-row-candidate-count-mismatch",
                (valid_row,),
                2,
            ),
        ):
            assertions = (
                (assertion, self._assertion(6, "Имя"))
                if len(rows) == 2
                else (assertion,)
            )
            with self.subTest(code=code):
                self.assert_contract_error(
                    code,
                    lambda rows=rows, assertions=assertions, candidate_count=candidate_count: (
                        build_source_assertion_manifest_contract(
                            self.repo_root,
                            scope_slug="applications-menu-search",
                            coverage_gaps_path="coverage-gaps.md",
                            source_paths=("source/main.xhtml",),
                            assertions=assertions,
                            source_rows=rows,
                            source_row_extraction_spec_digest=(
                                TEST_EXTRACTION_SPEC_DIGEST
                            ),
                            source_row_baseline_digest=TEST_BASELINE_DIGEST,
                            source_row_candidate_count=candidate_count,
                        )
                    ),
                )

    def test_manifest_json_requires_baseline_fields_and_candidate_id(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        payload = manifest.to_dict()
        payload.pop("source_row_baseline_digest")
        self.assert_contract_error(
            "invalid-fields",
            lambda: SourceAssertionManifest.from_dict(payload),
        )

        payload = manifest.to_dict()
        payload["source_rows"][0].pop("candidate_id")
        self.assert_contract_error(
            "invalid-fields",
            lambda: SourceAssertionManifest.from_dict(payload),
        )

    def test_candidate_row_accepts_markup_spanning_visible_text_and_rejects_wrong_text(self) -> None:
        exact = self._assertion(3, "Фамилия").exact_source_text
        locator = "/*/*[1]/*[1]/*[1]"
        self._write_source_markup(
            "<table><tr><td><p>BSR 3. Поиск выполняется,</p></td>"
            "<td>если заполнено только поле Фамилия клиента.</td></tr></table>"
        )
        assertion = replace(
            self._assertion(3, "Фамилия"),
            locator=locator,
        )
        row = replace(
            self._source_row(assertion),
            bounded_source_text=exact,
        )

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
            source_rows=(row,),
        )
        self.assertEqual(exact, manifest.source_rows[0].bounded_source_text)

        self.assert_contract_error(
            "source-row-candidate-text-mismatch",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_rows=(
                    replace(
                        row,
                        bounded_source_text=exact.replace(
                            "выполняется", "не выполняется"
                        ),
                    ),
                ),
            ),
        )

    def test_candidate_row_rejects_non_candidate_or_owned_descendant_locator(self) -> None:
        exact = self._assertion(3, "Фамилия").exact_source_text
        self._write_source_markup(
            "<table><tr><td><p>BSR 3. Поиск выполняется, если заполнено только "
            "поле Фамилия клиента.</p></td></tr></table>"
        )
        descendant_locator = "/*/*[1]/*[1]/*[1]/*[1]/*[1]"
        assertion = replace(
            self._assertion(3, "Фамилия"),
            locator=descendant_locator,
        )
        row = replace(
            self._source_row(assertion),
            bounded_source_text=exact,
        )

        self.assert_contract_error(
            "source-row-candidate-locator-invalid",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_rows=(row,),
            ),
        )

    def test_candidate_visible_text_ownership_matches_nested_li_and_table_row(self) -> None:
        list_text = "BSR 3. Родительское правило."
        list_locator = "/*/*[1]/*[1]/*[1]"
        self._write_source_markup(
            "<ul><li>BSR 3. Родительское <span>правило.</span>"
            "<ul><li>BSR 6. Дочернее правило.</li></ul></li></ul>"
        )
        list_assertion = replace(
            self._retarget_source_contract(
                self._assertion(3, "Фамилия"),
                exact_source_text=list_text,
                source_row_id="SRC-AMS-003",
                requirement_codes=("BSR 3",),
            ),
            locator=list_locator,
        )
        list_row = replace(
            self._source_row(list_assertion),
            bounded_source_text=list_text,
        )
        build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(list_assertion,),
            source_rows=(list_row,),
        )
        self.assert_contract_error(
            "source-row-candidate-text-mismatch",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(list_assertion,),
                source_rows=(
                    replace(
                        list_row,
                        bounded_source_text=(
                            list_text + " BSR 6. Дочернее правило."
                        ),
                    ),
                ),
            ),
        )

        table_text = "BSR 3. Строка. Вложенный пункт."
        table_locator = "/*/*[1]/*[1]/*[1]"
        self._write_source_markup(
            "<table><tr><td><p>BSR 3. Строка.</p>"
            "<ul><li>Вложенный пункт.</li></ul></td></tr></table>"
        )
        table_assertion = replace(
            self._retarget_source_contract(
                self._assertion(3, "Фамилия"),
                exact_source_text=table_text,
                source_row_id="SRC-AMS-003",
                requirement_codes=("BSR 3",),
            ),
            locator=table_locator,
        )
        build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(table_assertion,),
            source_rows=(
                replace(
                    self._source_row(table_assertion),
                    bounded_source_text=table_text,
                ),
            ),
        )

    def test_normalizes_each_registered_source_only_once_per_validation(self) -> None:
        source_text = self.source_path.read_text(encoding="utf-8")
        original = source_assertions_module.normalize_exact_source_text
        source_normalizations = 0

        def counted(value: str) -> str:
            nonlocal source_normalizations
            if value == source_text:
                source_normalizations += 1
            return original(value)

        with patch.object(
            source_assertions_module,
            "normalize_exact_source_text",
            side_effect=counted,
        ):
            self._build()

        self.assertEqual(1, source_normalizations)

    def test_exact_source_text_cannot_end_inside_unicode_alnum_token(self) -> None:
        source_row_text = "BSR 77. Формат: 4 цифры."
        self._write_source_candidates(source_row_text)
        assertion = self._retarget_source_contract(
            self._assertion(3, "Фамилия"),
            exact_source_text="Формат: 4 цифр",
            source_row_id="SRC-AMS-077",
            requirement_codes=(),
        )
        assertion = replace(
            assertion,
            atom_id="ATOM-AMS-077",
            obligation_ids=("OBL-AMS-077",),
        )

        self.assert_contract_error(
            "assertion-source-fragment-outside-primary-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_rows=(
                    replace(
                        self._source_row(assertion),
                        bounded_source_text=source_row_text,
                    ),
                ),
                expected_source_row_ids=("SRC-AMS-077",),
            ),
        )

    def test_exact_source_text_cannot_start_inside_unicode_alnum_token(self) -> None:
        source_row_text = "BSR 77. XФормат: 4 цифры."
        self._write_source_candidates(source_row_text)
        assertion = self._retarget_source_contract(
            self._assertion(3, "Фамилия"),
            exact_source_text="Формат: 4 цифры",
            source_row_id="SRC-AMS-077",
            requirement_codes=(),
        )
        assertion = replace(
            assertion,
            atom_id="ATOM-AMS-077",
            obligation_ids=("OBL-AMS-077",),
        )

        self.assert_contract_error(
            "assertion-source-fragment-outside-primary-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_rows=(
                    replace(
                        self._source_row(assertion),
                        bounded_source_text=source_row_text,
                    ),
                ),
                expected_source_row_ids=("SRC-AMS-077",),
            ),
        )

    def test_exact_source_text_may_be_bounded_by_sentence_punctuation(self) -> None:
        source_row_text = "BSR 77. Формат: 4 цифры; значение обязательно."
        self._write_source_candidates(source_row_text)
        assertion = self._retarget_source_contract(
            self._assertion(3, "Фамилия"),
            exact_source_text="Формат: 4 цифры",
            source_row_id="SRC-AMS-077",
            requirement_codes=(),
        )
        assertion = replace(
            assertion,
            atom_id="ATOM-AMS-077",
            obligation_ids=("OBL-AMS-077",),
        )

        build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
            source_rows=(
                replace(
                    self._source_row(assertion),
                    bounded_source_text=source_row_text,
                ),
            ),
            expected_source_row_ids=("SRC-AMS-077",),
        )

    def test_bsr_3_6_9_are_positive_single_field_assertions(self) -> None:
        manifest = self._build()

        self.assertEqual(
            ("positive", "positive", "positive"),
            tuple(item.polarity for item in manifest.assertions),
        )
        for assertion, field_name in zip(
            manifest.assertions,
            ("Фамилия", "Имя", "Отчество"),
            strict=True,
        ):
            self.assertIn("только поле", assertion.canonical_statement)
            self.assertIn(field_name, assertion.condition_clauses[0])
            self.assertEqual(("Нажать «Найти».",), assertion.action_clauses)
            self.assertIn(field_name, assertion.oracle_clauses[0])

    def test_wrong_negative_polarity_fails_against_approved_positive_mapping(self) -> None:
        assertion = replace(self._assertion(3, "Фамилия"), polarity="negative")
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
        )

        error = self.assert_contract_error(
            "approved-polarity-mismatch",
            lambda: validate_source_assertion_manifest(
                manifest,
                self.repo_root,
                approved_polarities={"ASSERT-BSR-003": "positive"},
            ),
        )
        self.assertIn("declares negative", str(error))

    def test_stale_source_sha_is_rejected(self) -> None:
        manifest = self._build()
        self.source_path.write_text(
            self.source_path.read_text(encoding="utf-8") + "\nChanged.",
            encoding="utf-8",
        )

        self.assert_contract_error(
            "stale-source-sha256",
            lambda: manifest.validate(self.repo_root),
        )

    def test_stale_exact_source_text_is_rejected_without_fuzzy_matching(self) -> None:
        manifest = self._build()
        wrong = replace(
            manifest.assertions[0],
            exact_source_text=(
                "BSR 3. Поиск не выполняется, если заполнено только поле Фамилия клиента."
            ),
        )
        changed = replace(manifest, assertions=(wrong, *manifest.assertions[1:]))

        self.assert_contract_error(
            "assertion-source-fragment-outside-primary-row",
            lambda: changed.validate(self.repo_root),
        )

    def test_crlf_nbsp_and_whitespace_are_the_only_source_text_normalization(self) -> None:
        assertion = replace(
            self._assertion(3, "Фамилия"),
            exact_source_text=(
                "BSR 3.  Поиск выполняется,\nесли заполнено только поле Фамилия клиента."
            ),
        )

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
        )

        self.assertEqual("ASSERT-BSR-003", manifest.assertions[0].assertion_id)

    def test_additional_exact_fragments_bind_split_source_evidence(self) -> None:
        assertion = replace(
            self._assertion(3, "Фамилия"),
            exact_source_fragments=(
                "только поле Фамилия клиента.",
            ),
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(assertion,),
        )
        restored = SourceAssertionManifest.from_dict(manifest.to_dict())

        self.assertEqual(assertion.exact_source_fragments, restored.assertions[0].exact_source_fragments)
        self.assertEqual(manifest.digest, restored.digest)

        stale = replace(
            assertion,
            exact_source_fragments=("BSR 6. Утверждение отсутствует.",),
        )
        self.assert_contract_error(
            "assertion-source-fragment-outside-primary-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(stale,),
                source_rows=(self._source_row(assertion),),
            ),
        )

    def test_unstructured_fragment_cannot_borrow_text_from_another_source_row(self) -> None:
        primary = replace(
            self._assertion(3, "Фамилия"),
            exact_source_fragments=(
                "BSR 6. Поиск выполняется, если заполнено только поле Имя клиента.",
            ),
        )

        self.assert_contract_error(
            "assertion-source-fragment-outside-primary-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(primary,),
                source_rows=(self._source_row(self._assertion(3, "Фамилия")),),
                expected_source_row_ids=("SRC-AMS-003",),
            ),
        )

    def test_structured_supporting_binding_allows_declared_cross_row_evidence(self) -> None:
        primary = replace(
            self._assertion(3, "Фамилия"),
            supporting_source_bindings=(
                SupportingSourceBinding(
                    source_row_id="SRC-AMS-006",
                    evidence_role="applicability",
                    exact_source_fragment=(
                        "BSR 6. Поиск выполняется, если заполнено только поле Имя клиента."
                    ),
                ),
            ),
        )
        supporting = self._assertion(6, "Имя")
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(primary, supporting),
            expected_source_row_ids=("SRC-AMS-003", "SRC-AMS-006"),
        )

        restored = SourceAssertionManifest.from_dict(manifest.to_dict())
        self.assertEqual(
            primary.supporting_source_bindings,
            restored.assertions[0].supporting_source_bindings,
        )

        wrong_row = replace(
            primary,
            supporting_source_bindings=(
                SupportingSourceBinding(
                    source_row_id="SRC-AMS-009",
                    evidence_role="applicability",
                    exact_source_fragment=supporting.exact_source_text,
                ),
            ),
        )
        third = self._assertion(9, "Отчество")
        self.assert_contract_error(
            "supporting-source-fragment-outside-declared-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(wrong_row, supporting, third),
            ),
        )

    def test_supporting_source_binding_roles_cover_composite_chains(self) -> None:
        self.assertTrue(
            {
                "subject",
                "property",
                "applicability",
                "constraint",
                "cross-reference",
                "definition",
                "polarity",
            }
            <= SUPPORTING_SOURCE_EVIDENCE_ROLES
        )
        self.assertTrue(
            {"action", "condition", "oracle", "requirement-code"}.isdisjoint(
                SUPPORTING_SOURCE_EVIDENCE_ROLES
            )
        )
        with self.assertRaises(SourceAssertionContractError) as context:
            SupportingSourceBinding(
                source_row_id="SRC-AMS-006",
                evidence_role="message",
                exact_source_fragment="Некорректный формат.",
            ).validate_shape()
        self.assertEqual(
            "invalid-supporting-source-evidence-role",
            context.exception.code,
        )

    def test_clause_evidence_covers_each_clause_and_directly_binds_cross_row(self) -> None:
        primary = self._assertion(3, "Фамилия")
        self.assert_contract_error(
            "clause-evidence-binding-set-mismatch",
            lambda: replace(
                primary,
                clause_evidence_bindings=tuple(
                    item
                    for item in primary.clause_evidence_bindings
                    if item.clause_kind != "action"
                ),
            ).validate_shape(),
        )

        supporting = self._assertion(6, "Имя")
        cross_row_action = replace(
            primary,
            clause_evidence_bindings=tuple(
                replace(
                    item,
                    source_row_id=supporting.source_row_id,
                    exact_source_fragment=supporting.exact_source_text,
                )
                if item.clause_kind == "action"
                else item
                for item in primary.clause_evidence_bindings
            ),
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(cross_row_action, supporting),
        )
        action_binding = next(
            item
            for item in manifest.assertions[0].clause_evidence_bindings
            if item.clause_kind == "action"
        )
        self.assertEqual(supporting.source_row_id, action_binding.source_row_id)

    def test_composite_assertion_binds_property_action_and_message_to_distinct_rows(self) -> None:
        composite_rows = (
            (16, "BSR 16. VIN содержит 17 символов."),
            (30, "BSR 30. Система отклоняет VIN неверного формата."),
            (31, "BSR 31. Система отображает сообщение «Некорректный формат VIN»."),
        )
        self._write_source_candidates(
            *self.base_source_candidates,
            *(text for _, text in composite_rows),
        )
        source_positions = {16: 7, 30: 8, 31: 9}

        supporting_assertions = tuple(
            replace(
                self._retarget_source_contract(
                    self._assertion(3, "Фамилия"),
                    exact_source_text=text,
                    source_row_id=f"SRC-AMS-{number:03d}",
                    requirement_codes=(f"BSR {number}",),
                ),
                assertion_id=f"ASSERT-BSR-{number:03d}",
                source_context_class="scope-local",
                locator=f"/*/*[1]/*[{source_positions[number]}]",
                canonical_statement=text.removeprefix(f"BSR {number}. "),
                atom_id=f"ATOM-AMS-{number:03d}",
                obligation_ids=(f"OBL-AMS-{number:03d}",),
            )
            for number, text in composite_rows
        )
        primary_base = self._assertion(3, "Фамилия")
        primary = replace(
            primary_base,
            source_context_class="scope-local",
            requirement_codes=("BSR 3", "BSR 16", "BSR 30", "BSR 31"),
            requirement_code_bindings=(
                RequirementCodeBinding("BSR 3", "SRC-AMS-003", "xhtml-row", "BSR 3"),
                RequirementCodeBinding("BSR 16", "SRC-AMS-016", "xhtml-row", "BSR 16"),
                RequirementCodeBinding("BSR 30", "SRC-AMS-030", "xhtml-row", "BSR 30"),
                RequirementCodeBinding("BSR 31", "SRC-AMS-031", "xhtml-row", "BSR 31"),
            ),
            clause_evidence_bindings=(
                primary_base.clause_evidence_bindings[0],
                ClauseEvidenceBinding(
                    "action",
                    0,
                    "SRC-AMS-030",
                    "action",
                    composite_rows[1][1],
                ),
                ClauseEvidenceBinding(
                    "oracle",
                    0,
                    "SRC-AMS-031",
                    "oracle",
                    composite_rows[2][1],
                ),
            ),
            supporting_source_bindings=(
                SupportingSourceBinding(
                    source_row_id="SRC-AMS-016",
                    evidence_role="property",
                    exact_source_fragment=composite_rows[0][1],
                ),
            ),
        )

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(primary, *supporting_assertions),
            expected_source_row_ids=(
                "SRC-AMS-003",
                "SRC-AMS-016",
                "SRC-AMS-030",
                "SRC-AMS-031",
            ),
        )

        self.assertEqual(1, len(manifest.assertions[0].supporting_source_bindings))

    def test_typed_cross_row_code_binding_needs_no_legacy_support_binding(self) -> None:
        primary = replace(
            self._assertion(3, "Фамилия"),
            requirement_codes=("BSR 3", "BSR 6"),
            requirement_code_bindings=(
                RequirementCodeBinding("BSR 3", "SRC-AMS-003", "xhtml-row", "BSR 3"),
                RequirementCodeBinding("BSR 6", "SRC-AMS-006", "xhtml-row", "BSR 6"),
            ),
            supporting_source_bindings=(),
        )

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(primary, self._assertion(6, "Имя")),
        )
        self.assertEqual(
            ("BSR 3", "BSR 6"),
            manifest.assertions[0].requirement_codes,
        )

    def test_no_scope_row_is_retained_and_rejects_executable_assertion(self) -> None:
        base = self._assertion(3, "Фамилия")
        not_applicable = replace(
            base,
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=(),
            disposition_rationale=(
                "Эта строка сохранена как проверенное исключение из scope."
            ),
        )
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(not_applicable,),
            expected_source_row_ids=(not_applicable.source_row_id,),
        )

        self.assertEqual("no", manifest.source_rows[0].scope_disposition)
        self.assert_contract_error(
            "out-of-scope-row-executable-assertion",
            lambda: replace(manifest, assertions=(base,)).validate(self.repo_root),
        )

    def test_no_scope_not_applicable_row_accepts_union_of_all_bound_codes(self) -> None:
        source_text = (
            "BSR 2. Правило относится к другому блоку. "
            "BSR 3. Связанное правило также относится к другому блоку."
        )
        source_row_id = "SRC-AMS-NO-002-003"
        self._write_source_candidates(source_text)
        assertions = tuple(
            self._not_applicable_code_assertion(
                requirement_code=requirement_code,
                source_row_id=source_row_id,
                source_text=source_text,
                assertion_suffix=suffix,
            )
            for requirement_code, suffix in (("BSR 2", "002"), ("BSR 3", "003"))
        )
        source_row = SourceRow(
            source_row_id=source_row_id,
            source_path="source/main.xhtml",
            source_locator="/*/*[1]/*[1]",
            bounded_source_text=source_text,
            source_context_class="document-global-constraints",
            candidate_id=_test_candidate_id(source_row_id),
            scope_disposition="no",
            requirement_codes=("BSR 2", "BSR 3"),
        )

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=assertions,
            source_rows=(source_row,),
        )

        self.assertEqual(("BSR 2", "BSR 3"), manifest.source_rows[0].requirement_codes)
        self.assertTrue(
            all(
                assertion.semantic_disposition == "not-applicable"
                and not assertion.obligation_ids
                for assertion in manifest.assertions
            )
        )

    def test_no_scope_not_applicable_row_rejects_declared_code_without_binding(self) -> None:
        source_text = (
            "BSR 2. Правило относится к другому блоку. "
            "BSR 3. Связанное правило также относится к другому блоку."
        )
        source_row_id = "SRC-AMS-NO-002-003"
        self._write_source_candidates(source_text)
        assertion = self._not_applicable_code_assertion(
            requirement_code="BSR 2",
            source_row_id=source_row_id,
            source_text=source_text,
            assertion_suffix="002",
        )
        source_row = SourceRow(
            source_row_id=source_row_id,
            source_path="source/main.xhtml",
            source_locator="/*/*[1]/*[1]",
            bounded_source_text=source_text,
            source_context_class="document-global-constraints",
            candidate_id=_test_candidate_id(source_row_id),
            scope_disposition="no",
            requirement_codes=("BSR 2", "BSR 3"),
        )

        self.assertEqual((), assertion.obligation_ids)
        self.assert_contract_error(
            "source-row-requirement-code-unbound",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_rows=(source_row,),
            ),
        )

    def test_requirement_codes_must_come_from_exact_bound_rows(self) -> None:
        static_claim = replace(
            self._assertion(3, "Фамилия"),
            requirement_codes=("BSR 3", "BSR 36"),
            requirement_code_bindings=(
                RequirementCodeBinding("BSR 3", "SRC-AMS-003", "xhtml-row", "BSR 3"),
                RequirementCodeBinding("BSR 36", "SRC-AMS-003", "xhtml-row", "BSR 36"),
            ),
        )
        self.assert_contract_error(
            "requirement-code-absent-from-bound-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(static_claim,),
                source_rows=(self._source_row(self._assertion(3, "Фамилия")),),
            ),
        )

        source_text = "GSR 10. Поиск использует точное правило десять."
        self._write_source_candidates(source_text)
        prefix_claim = self._retarget_source_contract(
            self._assertion(3, "Фамилия"),
            exact_source_text=source_text,
            source_row_id="SRC-GSR-010",
            requirement_codes=("GSR 1",),
        )
        prefix_claim = replace(prefix_claim, locator="/*/*[1]/*[1]")
        row = SourceRow(
            source_row_id="SRC-GSR-010",
            source_path="source/main.xhtml",
            source_locator="/*/*[1]/*[1]",
            bounded_source_text=source_text,
            source_context_class="document-global-constraints",
            scope_disposition="yes",
            requirement_codes=("GSR 10",),
        )
        self.assert_contract_error(
            "requirement-code-absent-from-bound-row",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(prefix_claim,),
                source_rows=(row,),
            ),
        )

    def test_pdf_only_requirement_code_requires_registered_parity_evidence(self) -> None:
        base = self._assertion(3, "Фамилия")
        pdf_only = replace(
            base,
            requirement_codes=("BSR 99",),
            requirement_code_bindings=(
                RequirementCodeBinding("BSR 99", base.source_row_id, "pdf-parity"),
            ),
        )
        row = replace(
            self._source_row(base),
            requirement_codes=("BSR 99",),
        )
        self.assert_contract_error(
            "pdf-requirement-code-evidence-binding-missing",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(pdf_only,),
                source_rows=(row,),
            ),
        )

        pdf_path = self.repo_root / "source" / "main.pdf"
        _write_text_pdf(
            pdf_path,
            (
                "Page 1",
                "Page 2",
                "Page 3",
                "Page 4",
                "Page 5",
                "Page 6",
                "BSR 99. PDF parity code.",
            ),
        )
        unrelated_binding = replace(
            pdf_only,
            requirement_code_bindings=(
                RequirementCodeBinding(
                    "BSR 99",
                    base.source_row_id,
                    "pdf-parity",
                    evidence_source_path="source/unrelated.pdf",
                    evidence_locator="page:7",
                ),
            ),
        )
        self.assert_contract_error(
            "pdf-requirement-code-evidence-source-mismatch",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(unrelated_binding,),
                source_rows=(row,),
                evidence_sources=(("source/main.pdf", "structural-visual-parity"),),
            ),
        )

        exactly_bound = replace(
            pdf_only,
            requirement_code_bindings=(
                RequirementCodeBinding(
                    "BSR 99",
                    base.source_row_id,
                    "pdf-parity",
                    evidence_source_path="source/main.pdf",
                    evidence_locator="page:7",
                ),
            ),
        )
        build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(exactly_bound,),
            source_rows=(row,),
            evidence_sources=(("source/main.pdf", "structural-visual-parity"),),
        )

        invalid_locator = replace(
            pdf_only,
            requirement_code_bindings=(
                RequirementCodeBinding(
                    "BSR 99",
                    base.source_row_id,
                    "pdf-parity",
                    evidence_source_path="source/main.pdf",
                    evidence_locator="page 7 / BSR 99",
                ),
            ),
        )
        self.assert_contract_error(
            "invalid-pdf-evidence-locator",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(invalid_locator,),
                source_rows=(row,),
                evidence_sources=(("source/main.pdf", "structural-visual-parity"),),
            ),
        )

        wrong_page = replace(
            exactly_bound,
            requirement_code_bindings=(
                replace(
                    exactly_bound.requirement_code_bindings[0],
                    evidence_locator="page:6",
                ),
            ),
        )
        self.assert_contract_error(
            "pdf-requirement-code-not-on-declared-page",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(wrong_page,),
                source_rows=(row,),
                evidence_sources=(("source/main.pdf", "structural-visual-parity"),),
            ),
        )

    def test_source_rows_reject_duplicate_path_and_locator(self) -> None:
        first = replace(self._assertion(3, "Фамилия"), locator="shared/locator")
        second = replace(self._assertion(6, "Имя"), locator="shared/locator")

        self.assert_contract_error(
            "duplicate-source-row-locator",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(first, second),
                source_rows=(self._source_row(first), self._source_row(second)),
            ),
        )

    def test_unclear_source_row_cannot_claim_ready_execution(self) -> None:
        ready = self._assertion(3, "Фамилия")
        unclear_row = replace(
            self._source_row(ready),
            scope_disposition="unclear",
        )
        self.assert_contract_error(
            "unclear-row-ready-assertion",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(ready,),
                source_rows=(unclear_row,),
            ),
        )

        blocked = replace(
            ready,
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Исполнение заблокировано до разрешения неопределённой границы scope."
            ),
            execution_dependency_gap_ids=("GAP-EXECUTION-001",),
        )
        build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(blocked,),
            source_rows=(unclear_row,),
        )

    def test_typed_inventory_binding_rejects_swapped_source_row_ids(self) -> None:
        manifest = self._build()
        first_row, second_row, third_row = manifest.source_rows
        first_assertion, second_assertion, third_assertion = manifest.assertions
        swapped = replace(
            manifest,
            source_rows=(
                replace(second_row, source_row_id=first_row.source_row_id),
                replace(first_row, source_row_id=second_row.source_row_id),
                third_row,
            ),
            assertions=(
                replace(
                    first_assertion,
                    source_row_id=second_row.source_row_id,
                    requirement_code_bindings=tuple(
                        replace(item, source_row_id=second_row.source_row_id)
                        for item in first_assertion.requirement_code_bindings
                    ),
                    clause_evidence_bindings=tuple(
                        replace(item, source_row_id=second_row.source_row_id)
                        for item in first_assertion.clause_evidence_bindings
                    ),
                ),
                replace(
                    second_assertion,
                    source_row_id=first_row.source_row_id,
                    requirement_code_bindings=tuple(
                        replace(item, source_row_id=first_row.source_row_id)
                        for item in second_assertion.requirement_code_bindings
                    ),
                    clause_evidence_bindings=tuple(
                        replace(item, source_row_id=first_row.source_row_id)
                        for item in second_assertion.clause_evidence_bindings
                    ),
                ),
                third_assertion,
            ),
        )

        swapped.validate(
            self.repo_root,
            expected_source_row_ids=tuple(item.source_row_id for item in manifest.source_rows),
        )
        self.assert_contract_error(
            "source-row-registry-mismatch",
            lambda: swapped.validate(
                self.repo_root,
                expected_source_rows=manifest.source_rows,
            ),
        )

    def test_unregistered_source_and_orphan_registered_source_are_rejected(self) -> None:
        manifest = self._build()
        unregistered = replace(
            manifest.assertions[0], source_path="source/not-registered.xhtml"
        )
        changed = replace(manifest, assertions=(unregistered, *manifest.assertions[1:]))
        self.assert_contract_error(
            "unregistered-assertion-source",
            lambda: changed.validate(self.repo_root),
        )

        context_path = self.repo_root / "source" / "context.xhtml"
        context_path.write_text("Context only.", encoding="utf-8")
        orphan = RegisteredSource(
            path="source/context.xhtml",
            sha256=sha256_file(context_path),
        )
        changed = replace(manifest, sources=(*manifest.sources, orphan))
        self.assert_contract_error(
            "orphan-registered-source",
            lambda: changed.validate(self.repo_root),
        )

    def test_source_row_cannot_point_to_two_sources(self) -> None:
        second_path = self.repo_root / "source" / "second.xhtml"
        second_path.write_text(
            "BSR 6. Поиск выполняется, если заполнено только поле Имя клиента.",
            encoding="utf-8",
        )
        first = self._assertion(3, "Фамилия", source_row_id="SRC-SHARED")
        second = self._assertion(
            6,
            "Имя",
            source_path="source/second.xhtml",
            source_row_id="SRC-SHARED",
        )
        self.assert_contract_error(
            "source-row-source-mismatch",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml", "source/second.xhtml"),
                assertions=(first, second),
            ),
        )

    def test_duplicate_assertion_atom_and_obligation_mappings_are_rejected(self) -> None:
        first = self._assertion(3, "Фамилия")
        duplicate_assertion = self._assertion(
            6,
            "Имя",
            assertion_id=first.assertion_id,
        )
        duplicate_atom = self._assertion(
            6,
            "Имя",
            atom_id=first.atom_id,
        )
        duplicate_obligation = self._assertion(
            6,
            "Имя",
            obligation_id=first.obligation_ids[0],
        )

        for code, second in (
            ("duplicate-assertion-id", duplicate_assertion),
            ("duplicate-atom-mapping", duplicate_atom),
            ("duplicate-obligation-mapping", duplicate_obligation),
        ):
            with self.subTest(code=code):
                manifest = build_source_assertion_manifest(
                    self.repo_root,
                    scope_slug="applications-menu-search",
                    source_paths=("source/main.xhtml",),
                    assertions=(first,),
                )
                changed = replace(manifest, assertions=(first, second))
                self.assert_contract_error(
                    code,
                    lambda changed=changed: changed.validate(self.repo_root),
                )

    def test_missing_expected_source_row_is_rejected(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))

        error = self.assert_contract_error(
            "source-row-completeness-mismatch",
            lambda: manifest.validate(
                self.repo_root,
                expected_source_row_ids=("SRC-AMS-003", "SRC-AMS-006"),
            ),
        )
        self.assertIn("SRC-AMS-006", str(error))

    def test_mockup_hash_change_is_rejected(self) -> None:
        mockup_path = self.repo_root / "mockups" / "search.png"
        mockup_path.parent.mkdir(parents=True)
        mockup_path.write_bytes(b"mockup-v1")
        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(self._assertion(3, "Фамилия"),),
            mockups=(("mockups/search.png", "Основная форма поиска", ("Найти",)),),
        )
        mockup_path.write_bytes(b"mockup-v2")

        self.assert_contract_error(
            "stale-mockup-sha256",
            lambda: manifest.validate(self.repo_root),
        )

    def test_binary_and_support_evidence_are_hash_bound_without_text_decoding(self) -> None:
        docx_path = self.repo_root / "source" / "main.docx"
        pdf_path = self.repo_root / "source" / "main.pdf"
        support_path = self.repo_root / "support" / "dictionary.md"
        support_path.parent.mkdir(parents=True)
        docx_path.write_bytes(b"PK\x03\x04\xffbinary-docx")
        pdf_path.write_bytes(b"%PDF-1.7\x00\xffbinary-pdf")
        support_path.write_text("Справочник статусов", encoding="utf-8")

        manifest = build_source_assertion_manifest(
            self.repo_root,
            scope_slug="applications-menu-search",
            source_paths=("source/main.xhtml",),
            assertions=(self._assertion(3, "Фамилия"),),
            evidence_sources=(
                ("source/main.docx", "semantic-source-of-truth"),
                ("source/main.pdf", "structural-visual-parity"),
                ("support/dictionary.md", "supporting-material"),
            ),
        )

        self.assertEqual(3, len(manifest.evidence_sources))
        embedded = SourceAssertionManifest.from_compact_reviewer_basis(
            manifest.to_compact_reviewer_basis()
        )
        embedded.validate(self.repo_root)
        self.assertEqual(manifest.digest, embedded.digest)

        docx_path.write_bytes(b"PK\x03\x04changed")
        self.assert_contract_error(
            "stale-evidence-source-sha256",
            lambda: manifest.validate(self.repo_root),
        )

    def test_evidence_source_role_and_path_overlap_are_rejected(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        source_sha = sha256_file(self.source_path)

        invalid_role = replace(
            manifest,
            evidence_sources=(
                RegisteredEvidenceSource(
                    path="source/main.xhtml",
                    sha256=source_sha,
                    role="primary",
                ),
            ),
        )
        self.assert_contract_error(
            "invalid-evidence-source-role",
            lambda: invalid_role.validate(self.repo_root),
        )

        overlapping = replace(
            manifest,
            evidence_sources=(
                RegisteredEvidenceSource(
                    path="source/main.xhtml",
                    sha256=source_sha,
                    role="semantic-source-of-truth",
                ),
            ),
        )
        self.assert_contract_error(
            "evidence-source-overlaps-assertion-source",
            lambda: overlapping.validate(self.repo_root),
        )

    def test_ambiguous_assertion_cannot_claim_obligation(self) -> None:
        assertion = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Требуется уточнить неоднозначное поведение до исполнения."
            ),
        )
        manifest = SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="applications-menu-search",
            source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
            source_row_baseline_digest=TEST_BASELINE_DIGEST,
            source_row_candidate_count=1,
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(self.repo_root / "coverage-gaps.md")
            ),
            sources=(
                RegisteredSource(
                    "source/main.xhtml",
                    sha256_file(self.source_path),
                ),
            ),
            assertions=(assertion,),
            source_rows=(self._source_row(assertion),),
        )

        self.assert_contract_error(
            "ambiguous-obligation-claim",
            lambda: manifest.validate(self.repo_root),
        )

    def test_ambiguous_assertion_requires_primary_gap_and_substantive_rationale(self) -> None:
        base = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Требуется уточнить неоднозначное поведение до исполнения."
            ),
            obligation_ids=(),
        )
        manifest = SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="applications-menu-search",
            source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
            source_row_baseline_digest=TEST_BASELINE_DIGEST,
            source_row_candidate_count=1,
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(self.repo_root / "coverage-gaps.md")
            ),
            sources=(
                RegisteredSource(
                    "source/main.xhtml",
                    sha256_file(self.source_path),
                ),
            ),
            assertions=(base,),
            source_rows=(self._source_row(base),),
        )
        self.assert_contract_error(
            "ambiguous-primary-gap-missing",
            lambda: manifest.validate(self.repo_root),
        )

        with_gap = replace(base, primary_gap_id="GAP-ROLE-MODEL")
        self.assert_contract_error(
            "ambiguous-rationale-missing",
            lambda: replace(manifest, assertions=(with_gap,)).validate(self.repo_root),
        )
        self.assert_contract_error(
            "placeholder-review-explanation",
            lambda: replace(
                manifest,
                assertions=(
                    replace(with_gap, disposition_rationale="<explanation>"),
                ),
            ).validate(self.repo_root),
        )

        accepted = replace(
            with_gap,
            disposition_rationale=(
                "Источник не определяет ролевую модель для этого поиска."
            ),
        )
        gap_path = self.repo_root / "coverage-gaps.md"
        gap_path.write_text(
            "# Coverage Gaps\n\n"
            "## GAP-ROLE-MODEL\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-ROLE-MODEL |\n"
            "| affected_assertion_id | ASSERT-BSR-003 |\n"
            "| affected_atom_id | ATOM-AMS-003 |\n"
            "| status | open |\n",
            encoding="utf-8",
        )
        replace(
            manifest,
            assertions=(accepted,),
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(gap_path)
            ),
        ).validate(self.repo_root)

    def test_primary_gap_is_rejected_for_testable_and_not_applicable_assertions(self) -> None:
        testable = replace(
            self._assertion(3, "Фамилия"),
            primary_gap_id="GAP-001",
        )
        not_applicable = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            obligation_ids=(),
            primary_gap_id="GAP-001",
            disposition_rationale=(
                "Эта строка не задаёт обязанность системы в выбранном scope."
            ),
        )
        for code, assertion in (
            ("testable-primary-gap-claim", testable),
            ("not-applicable-primary-gap-claim", not_applicable),
        ):
            with self.subTest(code=code):
                manifest = SourceAssertionManifest(
                    version=MANIFEST_VERSION,
                    scope_slug="applications-menu-search",
                    source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
                    source_row_baseline_digest=TEST_BASELINE_DIGEST,
                    source_row_candidate_count=1,
                    coverage_gaps_artifact=RegisteredArtifact(
                        "coverage-gaps.md",
                        sha256_file(self.repo_root / "coverage-gaps.md"),
                    ),
                    sources=(
                        RegisteredSource(
                            "source/main.xhtml",
                            sha256_file(self.source_path),
                        ),
                    ),
                    assertions=(assertion,),
                    source_rows=(self._source_row(assertion),),
                )
                self.assert_contract_error(
                    code,
                    lambda manifest=manifest: manifest.validate(self.repo_root),
                )

    def test_primary_gap_requires_open_hash_bound_affected_chain(self) -> None:
        primary = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="ambiguous",
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "The source behavior requires clarification before execution."
            ),
            obligation_ids=(),
            primary_gap_id="GAP-PRIMARY-001",
            disposition_rationale=(
                "The registered source row does not determine the required behavior."
            ),
        )
        companion = self._assertion(6, "Имя")
        gap_path = self.repo_root / "coverage-gaps.md"

        def write_gap(
            *,
            status: str = "open",
            affected_assertions: str = "ASSERT-BSR-003",
            affected_atoms: str = "ATOM-AMS-003",
        ) -> None:
            gap_path.write_text(
                "# Coverage Gaps\n\n"
                "## GAP-PRIMARY-001\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| gap_id | GAP-PRIMARY-001 |\n"
                f"| affected_assertion_id | {affected_assertions} |\n"
                f"| affected_atom_id | {affected_atoms} |\n"
                f"| status | {status} |\n",
                encoding="utf-8",
            )

        def build() -> SourceAssertionManifest:
            return build_source_assertion_manifest_contract(
                self.repo_root,
                scope_slug="applications-menu-search",
                coverage_gaps_path="coverage-gaps.md",
                source_paths=("source/main.xhtml",),
                assertions=(primary, companion),
                source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
                source_row_baseline_digest=TEST_BASELINE_DIGEST,
                source_row_candidate_count=2,
                source_row_candidate_ids={
                    primary.source_row_id: _test_candidate_id(primary.source_row_id),
                    companion.source_row_id: _test_candidate_id(companion.source_row_id),
                },
                expected_source_row_ids=(
                    primary.source_row_id,
                    companion.source_row_id,
                ),
            )

        gap_path.write_text("# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8")
        self.assert_contract_error("primary-gap-unknown", build)

        write_gap(status="resolved")
        self.assert_contract_error("primary-gap-not-open", build)

        write_gap(
            affected_assertions="ASSERT-BSR-006",
            affected_atoms="ATOM-AMS-006",
        )
        self.assert_contract_error("primary-gap-affected-chain-mismatch", build)

        write_gap(affected_atoms="ATOM-AMS-006")
        self.assert_contract_error("coverage-gap-affected-chain-mismatch", build)

        write_gap(
            affected_assertions="ASSERT-BSR-003; ASSERT-UNKNOWN",
            affected_atoms="ATOM-AMS-003",
        )
        self.assert_contract_error("coverage-gap-affected-assertion-unknown", build)

        # A semantic gap may legitimately affect more rows than the ambiguous
        # primary assertion. The ASSERT->ATOM mapping is exact, while the primary
        # membership check is intentionally a subset check.
        write_gap(
            affected_assertions="ASSERT-BSR-003; ASSERT-BSR-006",
            affected_atoms="ATOM-AMS-003; ATOM-AMS-006",
        )
        build()

    def test_hash_bound_coverage_gap_heading_cannot_be_orphaned(self) -> None:
        assertion = self._assertion(3, "Фамилия")
        manifest = self._build((assertion,))
        gap_path = self.repo_root / "coverage-gaps.md"
        gap_path.write_text(
            "# Coverage Gaps\n\n"
            "## GAP-ORPHAN-001\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-ORPHAN-001 |\n"
            "| status | open |\n",
            encoding="utf-8",
        )
        updated = replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(gap_path)
            ),
        )

        self.assert_contract_error(
            "orphan-coverage-gap",
            lambda: updated.validate(self.repo_root),
        )

    def test_semantic_constraint_gap_with_exact_affected_chain_is_not_orphaned(self) -> None:
        assertion = self._assertion(3, "Фамилия")
        manifest = self._build((assertion,))
        gap_path = self.repo_root / "coverage-gaps.md"
        gap_path.write_text(
            "# Coverage Gaps\n\n"
            "## GAP-CONSTRAINT-001\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-CONSTRAINT-001 |\n"
            "| affected_assertion_id | ASSERT-BSR-003 |\n"
            "| affected_atom_id | ATOM-AMS-003 |\n"
            "| status | open |\n",
            encoding="utf-8",
        )
        replace(
            manifest,
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(gap_path)
            ),
        ).validate(self.repo_root)

    def test_testable_assertion_requires_action_oracle_and_obligation(self) -> None:
        base = self._assertion(3, "Фамилия")
        for code, assertion in (
            ("testable-action-missing", replace(base, action_clauses=())),
            ("testable-oracle-missing", replace(base, oracle_clauses=())),
            ("testable-obligation-missing", replace(base, obligation_ids=())),
        ):
            with self.subTest(code=code):
                manifest = SourceAssertionManifest(
                    version=MANIFEST_VERSION,
                    scope_slug="applications-menu-search",
                    source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
                    source_row_baseline_digest=TEST_BASELINE_DIGEST,
                    source_row_candidate_count=1,
                    coverage_gaps_artifact=RegisteredArtifact(
                        "coverage-gaps.md",
                        sha256_file(self.repo_root / "coverage-gaps.md"),
                    ),
                    sources=(
                        RegisteredSource(
                            "source/main.xhtml",
                            sha256_file(self.source_path),
                        ),
                    ),
                    assertions=(assertion,),
                    source_rows=(self._source_row(assertion),),
                )
                self.assert_contract_error(
                    code,
                    lambda manifest=manifest: manifest.validate(self.repo_root),
                )

    def test_not_applicable_assertion_requires_source_backed_rationale(self) -> None:
        base = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            obligation_ids=(),
        )
        manifest = SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="applications-menu-search",
            source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
            source_row_baseline_digest=TEST_BASELINE_DIGEST,
            source_row_candidate_count=1,
            coverage_gaps_artifact=RegisteredArtifact(
                "coverage-gaps.md", sha256_file(self.repo_root / "coverage-gaps.md")
            ),
            sources=(
                RegisteredSource(
                    "source/main.xhtml",
                    sha256_file(self.source_path),
                ),
            ),
            assertions=(base,),
            source_rows=(self._source_row(base),),
        )
        self.assert_contract_error(
            "not-applicable-rationale-missing",
            lambda: manifest.validate(self.repo_root),
        )

        accepted = replace(
            base,
            disposition_rationale=(
                "Строка SRC-AMS-003 описывает внешний контекст, "
                "а не обязанность системы в выбранном scope."
            ),
        )
        replace(manifest, assertions=(accepted,)).validate(
            self.repo_root,
            expected_source_row_ids=("SRC-AMS-003",),
        )

    def test_json_contract_rejects_unknown_or_missing_fields(self) -> None:
        payload = self._build((self._assertion(3, "Фамилия"),)).to_dict()
        payload["digest"] = "0" * 64
        manifest_path = self.repo_root / "unknown-field.json"
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.assert_contract_error(
            "invalid-fields",
            lambda: load_source_assertion_manifest(manifest_path, self.repo_root),
        )

        payload.pop("digest")
        payload["assertions"][0].pop("oracle_clauses")
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.assert_contract_error(
            "invalid-fields",
            lambda: load_source_assertion_manifest(manifest_path, self.repo_root),
        )

    def test_manifest_v1_requires_explicit_rematerialization(self) -> None:
        payload = self._build((self._assertion(3, "Фамилия"),)).to_dict()
        payload["version"] = 1
        payload["assertions"][0].pop("primary_gap_id")
        manifest_path = self.repo_root / "legacy-source-assertions-v1.json"
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

        self.assert_contract_error(
            "legacy-manifest-requires-rematerialization",
            lambda: load_source_assertion_manifest(manifest_path, self.repo_root),
        )

    def test_not_applicable_assertion_cannot_claim_obligations(self) -> None:
        assertion = replace(
            self._assertion(3, "Фамилия"),
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=("OBL-FAKE",),
            disposition_rationale=(
                "Источник исключает эту строку из выбранного функционального scope."
            ),
        )

        self.assert_contract_error(
            "not-applicable-obligation-claim",
            assertion.validate_shape,
        )

    def test_execution_readiness_is_independent_from_semantic_disposition(self) -> None:
        base = self._assertion(3, "Фамилия")
        dependency_blocked = replace(
            base,
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Исполнение заблокировано отсутствующим runtime-справочником."
            ),
            execution_dependency_gap_ids=("GAP-EXECUTION-001",),
        )
        dependency_blocked.validate_shape()

        self.assert_contract_error(
            "dependency-blocked-rationale-missing",
            lambda: replace(
                dependency_blocked,
                execution_readiness_rationale=NO_REQUIRED_CHANGE,
            ).validate_shape(),
        )
        self.assert_contract_error(
            "execution-readiness-disposition-mismatch",
            lambda: replace(
                base,
                semantic_disposition="ambiguous",
                obligation_ids=(),
                disposition_rationale=(
                    "Источник не определяет требуемое поведение однозначно."
                ),
            ).validate_shape(),
        )

    def test_execution_dependency_gap_ids_are_required_and_duplicate_free_only_for_blocked_testable(self) -> None:
        base = self._assertion(3, "Фамилия")
        blocked = replace(
            base,
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Исполнение зависит от отсутствующего воспроизводимого fixture."
            ),
        )
        self.assert_contract_error(
            "execution-dependency-gap-missing",
            blocked.validate_shape,
        )
        self.assert_contract_error(
            "duplicate-execution-dependency-gap-id",
            lambda: replace(
                blocked,
                execution_dependency_gap_ids=(
                    "GAP-EXECUTION-001",
                    "GAP-EXECUTION-001",
                ),
            ).validate_shape(),
        )
        self.assert_contract_error(
            "execution-dependency-gap-forbidden",
            lambda: replace(
                base,
                execution_dependency_gap_ids=("GAP-EXECUTION-001",),
            ).validate_shape(),
        )
        replace(
            blocked,
            execution_dependency_gap_ids=("GAP-EXECUTION-001",),
        ).validate_shape()

    def test_execution_dependency_gap_requires_hash_bound_blocking_exact_chain(self) -> None:
        assertion = replace(
            self._assertion(3, "Фамилия"),
            execution_readiness="dependency-blocked",
            execution_readiness_rationale=(
                "Исполнение зависит от отсутствующего воспроизводимого fixture."
            ),
            execution_dependency_gap_ids=("GAP-EXECUTION-001",),
        )
        gap_path = self.repo_root / "coverage-gaps.md"

        def write_gap(
            *, impact: str, blocks: str, obligation: str, status: str = "open"
        ) -> None:
            gap_path.write_text(
                "# Coverage Gaps\n\n"
                "## GAP-EXECUTION-001\n\n"
                f"**Impact:** `{impact}`\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| gap_id | GAP-EXECUTION-001 |\n"
                "| execution_assertion_ids | ASSERT-BSR-003 |\n"
                "| execution_atom_ids | ATOM-AMS-003 |\n"
                f"| execution_obligation_ids | {obligation} |\n"
                f"| blocks_ready_for_review | {blocks} |\n"
                f"| status | {status} |\n",
                encoding="utf-8",
            )

        def build() -> SourceAssertionManifest:
            return build_source_assertion_manifest_contract(
                self.repo_root,
                scope_slug="applications-menu-search",
                coverage_gaps_path="coverage-gaps.md",
                source_paths=("source/main.xhtml",),
                assertions=(assertion,),
                source_row_extraction_spec_digest=TEST_EXTRACTION_SPEC_DIGEST,
                source_row_baseline_digest=TEST_BASELINE_DIGEST,
                source_row_candidate_count=1,
                source_row_candidate_ids={
                    assertion.source_row_id: _test_candidate_id(
                        assertion.source_row_id
                    )
                },
                expected_source_row_ids=(assertion.source_row_id,),
            )

        gap_path.write_text("# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8")
        self.assert_contract_error("execution-dependency-gap-unknown", build)
        write_gap(
            impact="blocking",
            blocks="yes",
            obligation="OBL-AMS-003",
            status="",
        )
        self.assert_contract_error("execution-dependency-gap-not-open", build)
        write_gap(impact="non-blocking", blocks="yes", obligation="OBL-AMS-003")
        self.assert_contract_error("execution-dependency-gap-not-blocking", build)
        write_gap(impact="blocking", blocks="no", obligation="OBL-AMS-003")
        self.assert_contract_error(
            "execution-dependency-gap-does-not-block-review", build
        )
        for noncanonical_blocks_value in ("true", "blocking", "blocked"):
            write_gap(
                impact="blocking",
                blocks=noncanonical_blocks_value,
                obligation="OBL-AMS-003",
            )
            self.assert_contract_error(
                "execution-dependency-gap-does-not-block-review", build
            )
        write_gap(
            impact="blocking",
            blocks="yes",
            obligation="OBL-AMS-003; OBL-AMS-003",
        )
        self.assert_contract_error(
            "duplicate-coverage-gap-execution-id", build
        )
        write_gap(
            impact="blocking",
            blocks="yes",
            obligation="OBL-AMS-003 garbage",
        )
        self.assert_contract_error(
            "malformed-coverage-gap-execution-id-set", build
        )
        write_gap(impact="blocking", blocks="yes", obligation="OBL-AMS-003")
        gap_path.write_text(
            gap_path.read_text(encoding="utf-8")
            + "| execution_obligation_ids | OBL-AMS-003 |\n",
            encoding="utf-8",
        )
        self.assert_contract_error("duplicate-coverage-gap-field", build)
        write_gap(impact="blocking", blocks="yes", obligation="OBL-OTHER")
        self.assert_contract_error("execution-dependency-gap-chain-mismatch", build)
        write_gap(impact="blocking", blocks="yes", obligation="OBL-AMS-003")
        manifest = build()
        gap_path.write_text(
            gap_path.read_text(encoding="utf-8") + "\n<!-- stale -->\n",
            encoding="utf-8",
        )
        self.assert_contract_error(
            "stale-coverage-gaps-artifact-sha256",
            lambda: manifest.validate(self.repo_root),
        )

    def test_independent_review_receipt_binds_digest_set_and_polarity(self) -> None:
        manifest = self._build()
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=tuple(self._review(item) for item in manifest.assertions),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        receipt_path = self.repo_root / "source-assertion-review.json"
        receipt_path.write_text(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        restored = load_source_assertion_review_receipt(receipt_path, manifest)

        self.assertEqual("accepted", restored.decision)
        self.assertEqual(
            {item.assertion_id: "positive" for item in manifest.assertions},
            restored.approved_polarities,
        )

    def test_source_inventory_review_is_digest_bound_and_required_for_acceptance(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        reviews = (self._review(manifest.assertions[0]),)
        base_receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=reviews,
            source_inventory_review=self._inventory_review(manifest),
            scope_boundary_review=self._scope_boundary(manifest),
        )

        self.assert_contract_error(
            "source-inventory-review-manifest-mismatch",
            lambda: replace(
                base_receipt,
                source_inventory_review=replace(
                    base_receipt.source_inventory_review,
                    baseline_digest="0" * 64,
                ),
            ).validate(manifest),
        )

        incorrect_inventory = self._inventory_review(
            manifest,
            verdict="incorrect",
        )
        self.assert_contract_error(
            "accepted-source-review-has-unverified-inventory",
            lambda: replace(
                base_receipt,
                source_inventory_review=incorrect_inventory,
            ).validate(manifest),
        )

        changes_required = replace(
            base_receipt,
            decision="changes-required",
            source_inventory_review=incorrect_inventory,
        )
        changes_required.validate(manifest)

    def test_source_inventory_review_rejects_non_bijective_count_and_placeholder_note(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        review = self._inventory_review(manifest)
        self.assert_contract_error(
            "invalid-source-inventory-count",
            lambda: replace(review, mapped_source_row_count=0).validate_shape(),
        )
        self.assert_contract_error(
            "placeholder-review-explanation",
            lambda: replace(review, note="ok").validate_shape(),
        )

    def test_review_receipt_rejects_stale_digest_wrong_polarity_and_incomplete_set(self) -> None:
        manifest = self._build()
        reviews = tuple(self._review(item) for item in manifest.assertions)
        for code, receipt in (
            (
                "source-review-manifest-digest-mismatch",
                SourceAssertionReviewReceipt(
                    REVIEW_RECEIPT_VERSION,
                    "0" * 64,
                    "accepted",
                    reviews,
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
            (
                "approved-polarity-mismatch",
                SourceAssertionReviewReceipt(
                    REVIEW_RECEIPT_VERSION,
                    manifest.digest,
                    "accepted",
                    (
                        replace(reviews[0], approved_polarity="negative"),
                        *reviews[1:],
                    ),
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
            (
                "approved-semantic-disposition-mismatch",
                SourceAssertionReviewReceipt(
                    REVIEW_RECEIPT_VERSION,
                    manifest.digest,
                    "accepted",
                    (
                        replace(
                            reviews[0],
                            approved_semantic_disposition="ambiguous",
                            approved_execution_readiness="dependency-blocked",
                        ),
                        *reviews[1:],
                    ),
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
            (
                "approved-risk-mismatch",
                SourceAssertionReviewReceipt(
                    REVIEW_RECEIPT_VERSION,
                    manifest.digest,
                    "accepted",
                    (
                        replace(reviews[0], approved_risk="low"),
                        *reviews[1:],
                    ),
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
            (
                "source-review-set-mismatch",
                SourceAssertionReviewReceipt(
                    REVIEW_RECEIPT_VERSION,
                    manifest.digest,
                    "accepted",
                    reviews[:-1],
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
            (
                "unsupported-review-receipt-version",
                SourceAssertionReviewReceipt(
                    99,
                    manifest.digest,
                    "accepted",
                    reviews,
                    self._inventory_review(manifest),
                    self._scope_boundary(manifest),
                ),
            ),
        ):
            with self.subTest(code=code):
                self.assert_contract_error(
                    code,
                    lambda receipt=receipt: receipt.validate(manifest),
                )

    def test_receipt_post_validator_retains_transport_omitted_invariants(self) -> None:
        manifest = self._build()
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=tuple(
                self._review(item) for item in manifest.assertions
            ),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        payload = receipt.to_dict()

        duplicate = deepcopy(payload)
        duplicate["assertion_reviews"].append(
            deepcopy(duplicate["assertion_reviews"][0])
        )
        wrong_cardinality = deepcopy(payload)
        wrong_cardinality["assertion_reviews"] = wrong_cardinality[
            "assertion_reviews"
        ][:-1]
        empty_string = deepcopy(payload)
        empty_string["assertion_reviews"][0]["assertion_id"] = "   "
        invalid_sha256 = deepcopy(payload)
        invalid_sha256["source_inventory_review"]["baseline_digest"] = "not-a-sha"

        for code, candidate in (
            ("duplicate-source-review", duplicate),
            ("source-review-set-mismatch", wrong_cardinality),
            ("invalid-text", empty_string),
            ("invalid-sha256", invalid_sha256),
        ):
            with self.subTest(code=code):
                self.assert_contract_error(
                    code,
                    lambda candidate=candidate: (
                        SourceAssertionReviewReceipt.from_dict(candidate).validate(
                            manifest
                        )
                    ),
                )

    def test_changes_required_receipt_can_propose_corrected_classification(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        corrected = self._review(
            manifest.assertions[0],
            incorrect_dimensions=(
                "semantic-disposition",
                "execution-readiness",
            ),
            approved_semantic_disposition="ambiguous",
            approved_execution_readiness="dependency-blocked",
            required_change=(
                "Изменить semantic disposition на ambiguous и связать "
                "assertion с primary GAP."
            ),
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="changes-required",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(corrected,),
            scope_boundary_review=self._scope_boundary(manifest),
        )

        receipt.validate(manifest)

        unchanged_proposal = replace(
            corrected,
            approved_semantic_disposition="testable",
        )
        self.assert_contract_error(
            "incorrect-semantic-disposition-without-proposed-change",
            lambda: replace(
                receipt,
                assertion_reviews=(unchanged_proposal,),
            ).validate(manifest),
        )

    def test_review_dimensions_drive_verdict_and_required_change(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        verified = self._review(manifest.assertions[0])
        for dimension in ("oracle", "clarification-provenance"):
            with self.subTest(missing_dimension=dimension):
                missing_dimension = dict(verified.dimension_verdicts)
                missing_dimension.pop(dimension)
                self.assert_contract_error(
                    "source-review-dimension-set-mismatch",
                    lambda missing_dimension=missing_dimension: replace(
                        verified,
                        dimension_verdicts=missing_dimension,
                    ).validate_shape(),
                )

        incorrect_dimensions = self._dimension_verdicts("source-binding")
        self.assert_contract_error(
            "source-review-verdict-aggregate-mismatch",
            lambda: replace(
                verified,
                dimension_verdicts=incorrect_dimensions,
            ).validate_shape(),
        )
        self.assert_contract_error(
            "verified-source-review-required-change-invalid",
            lambda: replace(
                verified,
                required_change="Изменить source binding assertion.",
            ).validate_shape(),
        )

        incorrect = replace(
            verified,
            dimension_verdicts=incorrect_dimensions,
            verdict="incorrect",
            required_change=NO_REQUIRED_CHANGE,
        )
        self.assert_contract_error(
            "incorrect-source-review-required-change-missing",
            incorrect.validate_shape,
        )

    def test_source_assertion_review_requires_substantive_note(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        verified = self._review(manifest.assertions[0])
        for note in ("ok", "<explanation>"):
            with self.subTest(note=note):
                self.assert_contract_error(
                    "placeholder-review-explanation",
                    lambda note=note: replace(verified, note=note).validate_shape(),
                )

    def test_accepted_receipt_rejects_any_incorrect_dimension(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        incorrect = self._review(
            manifest.assertions[0],
            incorrect_dimensions=("risk",),
            approved_risk="medium",
            required_change="Изменить risk на medium после source review.",
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(incorrect,),
            scope_boundary_review=self._scope_boundary(manifest),
        )

        self.assert_contract_error(
            "accepted-source-review-has-errors",
            lambda: receipt.validate(manifest),
        )

    def test_review_receipt_v1_file_is_not_silently_upgraded(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt_path = self.repo_root / "source-assertion-review-v1.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "manifest_digest": manifest.digest,
                    "decision": "accepted",
                    "assertion_reviews": [
                        {
                            "assertion_id": "ASSERT-BSR-003",
                            "approved_polarity": "positive",
                            "verdict": "verified",
                            "note": "Legacy receipt without disposition and risk.",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        self.assert_contract_error(
            "legacy-review-receipt-requires-rereview",
            lambda: load_source_assertion_review_receipt(receipt_path, manifest),
        )

    def test_review_receipt_v2_requires_fresh_scope_boundary_review(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt_path = self.repo_root / "source-assertion-review-v2.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "manifest_digest": manifest.digest,
                    "decision": "accepted",
                    "assertion_reviews": [
                        {
                            "assertion_id": "ASSERT-BSR-003",
                            "approved_polarity": "positive",
                            "approved_semantic_disposition": "testable",
                            "approved_risk": "high",
                            "verdict": "verified",
                            "note": "Legacy receipt without boundary review.",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        self.assert_contract_error(
            "legacy-review-receipt-requires-rereview",
            lambda: load_source_assertion_review_receipt(receipt_path, manifest),
        )

    def test_review_receipt_v3_requires_fresh_typed_boundary_review(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt_path = self.repo_root / "source-assertion-review-v3.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "version": 3,
                    "manifest_digest": manifest.digest,
                    "decision": "accepted",
                    "assertion_reviews": [],
                    "scope_boundary_review": {},
                }
            ),
            encoding="utf-8",
        )

        self.assert_contract_error(
            "legacy-review-receipt-requires-rereview",
            lambda: load_source_assertion_review_receipt(receipt_path, manifest),
        )

    def test_scope_boundary_review_requires_complete_context_and_manifest_rows(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        boundary = self._scope_boundary(manifest)
        for code, candidate in (
            (
                "scope-boundary-context-set-mismatch",
                replace(
                    boundary,
                    checked_context_classes=boundary.checked_context_classes[:-1],
                ),
            ),
            (
                "scope-boundary-source-row-missing",
                replace(
                    boundary,
                    reviewed_manifest_contexts=(
                        ScopeBoundaryManifestContext(
                            context_class="document-global-constraints",
                            source_row_id="SRC-OUTSIDE-SCOPE",
                        ),
                    ),
                ),
            ),
            (
                "scope-boundary-manifest-context-set-mismatch",
                replace(
                    boundary,
                    reviewed_manifest_contexts=(),
                    excluded_contexts=(),
                ),
            ),
        ):
            with self.subTest(code=code):
                self.assert_contract_error(
                    code,
                    lambda candidate=candidate: candidate.validate(manifest),
                )

    def test_scope_boundary_empty_class_requires_source_bound_external_evidence(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        boundary = self._scope_boundary(manifest)
        without_cross_reference = replace(
            boundary,
            excluded_contexts=tuple(
                item
                for item in boundary.excluded_contexts
                if item.context_class != "cross-referenced-constraints"
            ),
        )

        self.assert_contract_error(
            "scope-boundary-class-evidence-missing",
            lambda: without_cross_reference.validate(manifest),
        )

        reported_missing_evidence = replace(
            without_cross_reference,
            verdict="incorrect",
            required_change=(
                "Add one source-bound cross-reference exclusion before acceptance."
            ),
            note=(
                "The supplied evidence does not account for the cross-reference "
                "boundary class."
            ),
        )
        reported_missing_evidence.validate(manifest)

    def test_scope_boundary_review_retains_all_not_applicable_manifest_rows(self) -> None:
        assertions = (
            self._as_not_applicable(
                self._assertion(3, "Фамилия"),
                context_class="document-global-constraints",
            ),
            self._as_not_applicable(
                self._assertion(6, "Имя"),
                context_class="ancestor-and-section-preamble",
            ),
            self._as_not_applicable(
                self._assertion(9, "Отчество"),
                context_class="cross-referenced-constraints",
            ),
        )
        manifest = self._build(assertions)
        boundary = self._scope_boundary(manifest)

        self.assertEqual(3, len(boundary.reviewed_manifest_contexts))
        self.assertEqual(0, len(boundary.excluded_contexts))
        boundary.validate(manifest)

    def test_scope_boundary_requires_every_manifest_boundary_row(self) -> None:
        first = self._assertion(3, "Фамилия")
        second = replace(
            self._assertion(6, "Имя"),
            source_context_class="cross-referenced-constraints",
        )
        third = self._assertion(9, "Отчество")
        manifest = self._build((first, second, third))
        complete = self._scope_boundary(manifest)
        missing_third = replace(
            complete,
            reviewed_manifest_contexts=tuple(
                item
                for item in complete.reviewed_manifest_contexts
                if item.source_row_id != third.source_row_id
            ),
        )

        self.assert_contract_error(
            "scope-boundary-manifest-context-set-mismatch",
            lambda: missing_third.validate(manifest),
        )

    def test_scope_boundary_rejects_exclusion_locator_reused_across_context_classes(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        boundary = self._scope_boundary(manifest)
        first, second = boundary.excluded_contexts
        reused = replace(
            second,
            source_path=first.source_path,
            source_sha256=first.source_sha256,
            source_locator=first.source_locator,
            exact_source_text=first.exact_source_text,
        )

        self.assert_contract_error(
            "scope-boundary-exclusion-reused-across-context-classes",
            lambda: replace(
                boundary,
                excluded_contexts=(first, reused),
            ).validate(manifest),
        )

    def test_scope_boundary_rejects_one_row_reused_for_all_context_classes(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        source_row_id = manifest.assertions[0].source_row_id
        boundary = self._scope_boundary(
            manifest,
            reviewed_manifest_contexts=tuple(
                ScopeBoundaryManifestContext(
                    context_class=context_class,
                    source_row_id=source_row_id,
                )
                for context_class in (
                    "document-global-constraints",
                    "ancestor-and-section-preamble",
                    "cross-referenced-constraints",
                )
            ),
            excluded_contexts=(),
        )

        self.assert_contract_error(
            "scope-boundary-context-class-mismatch",
            lambda: boundary.validate(manifest),
        )

    def test_scope_boundary_exclusion_must_bind_registered_source_digest(self) -> None:
        excluded = self._as_not_applicable(self._assertion(3, "Фамилия"))
        manifest = self._build((excluded,))
        boundary = self._scope_boundary(manifest)
        forged = replace(
            boundary.excluded_contexts[0],
            source_sha256="0" * 64,
        )

        self.assert_contract_error(
            "scope-boundary-exclusion-source-digest-mismatch",
            lambda: replace(
                boundary,
                excluded_contexts=(forged, *boundary.excluded_contexts[1:]),
            ).validate(manifest),
        )

    def test_scope_boundary_exclusion_requires_exact_registered_text_and_locator(self) -> None:
        excluded = self._as_not_applicable(self._assertion(3, "Фамилия"))
        manifest = self._build((excluded,))
        boundary = self._scope_boundary(manifest)
        exclusion = boundary.excluded_contexts[0]
        fake_text = "Текст отсутствует в зарегистрированном XHTML источнике."

        self.assert_contract_error(
            "scope-boundary-exclusion-text-mismatch",
            lambda: replace(
                boundary,
                excluded_contexts=(
                    replace(
                        exclusion,
                        exact_source_text=fake_text,
                        source_locator=scope_boundary_source_locator(
                            exclusion.source_path,
                            fake_text,
                        ),
                    ),
                    *boundary.excluded_contexts[1:],
                ),
            ).validate(manifest),
        )
        self.assert_contract_error(
            "scope-boundary-exclusion-locator-mismatch",
            lambda: replace(
                boundary,
                excluded_contexts=(
                    replace(exclusion, source_locator="arbitrary/locator"),
                    *boundary.excluded_contexts[1:],
                ),
            ).validate(manifest),
        )

    def test_scope_boundary_exclusion_cannot_replace_manifest_row(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        boundary = self._scope_boundary(manifest)
        exclusion = boundary.excluded_contexts[0]
        row = manifest.source_rows[0]
        overlaps_row = replace(
            exclusion,
            exact_source_text=row.bounded_source_text,
            source_locator=scope_boundary_source_locator(
                row.source_path,
                row.bounded_source_text,
            ),
        )

        self.assert_contract_error(
            "scope-boundary-exclusion-overlaps-manifest-row",
            lambda: replace(
                boundary,
                excluded_contexts=(overlaps_row, *boundary.excluded_contexts[1:]),
            ).validate(manifest),
        )

    def test_scope_boundary_manifest_row_handles_mixed_dispositions_in_any_order(self) -> None:
        testable = self._assertion(3, "Фамилия")
        not_applicable = replace(
            testable,
            assertion_id="ASSERT-BSR-003-NA",
            atom_id="ATOM-AMS-003-NA",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            clause_evidence_bindings=(),
            obligation_ids=(),
            disposition_rationale=(
                "Одна атомарная интерпретация строки исключена из выбранного scope."
            ),
        )
        for assertions in (
            (testable, not_applicable),
            (not_applicable, testable),
        ):
            with self.subTest(order=tuple(item.assertion_id for item in assertions)):
                manifest = build_source_assertion_manifest(
                    self.repo_root,
                    scope_slug="applications-menu-search",
                    source_paths=("source/main.xhtml",),
                    assertions=assertions,
                    expected_source_row_ids=(testable.source_row_id,),
                )
                self._scope_boundary(manifest).validate(manifest)

    def test_manifest_rejects_mixed_context_classes_for_one_source_row(self) -> None:
        first = self._assertion(3, "Фамилия")
        second = replace(
            first,
            assertion_id="ASSERT-BSR-003-SECOND",
            atom_id="ATOM-AMS-003-SECOND",
            obligation_ids=("OBL-AMS-003-SECOND",),
            source_context_class="scope-local",
        )

        self.assert_contract_error(
            "source-row-context-class-mismatch",
            lambda: build_source_assertion_manifest(
                self.repo_root,
                scope_slug="applications-menu-search",
                source_paths=("source/main.xhtml",),
                assertions=(first, second),
                expected_source_row_ids=(first.source_row_id,),
            ),
        )

    def test_scope_boundary_exclusion_rejects_placeholder_reason(self) -> None:
        excluded = self._as_not_applicable(self._assertion(3, "Фамилия"))
        manifest = self._build((excluded,))
        boundary = self._scope_boundary(manifest)

        self.assert_contract_error(
            "placeholder-review-explanation",
            lambda: replace(
                boundary,
                excluded_contexts=(
                    replace(boundary.excluded_contexts[0], reason="<explanation>"),
                ),
            ).validate(manifest),
        )

    def test_accepted_receipt_rejects_incorrect_scope_boundary_verdict(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(
                self._review(manifest.assertions[0]),
            ),
            scope_boundary_review=self._scope_boundary(
                manifest,
                verdict="incorrect",
            ),
        )

        self.assert_contract_error(
            "accepted-source-review-has-unverified-scope-boundary",
            lambda: receipt.validate(manifest),
        )

    def test_changes_required_receipt_accepts_incorrect_scope_boundary_only(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="changes-required",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(
                self._review(manifest.assertions[0]),
            ),
            scope_boundary_review=self._scope_boundary(
                manifest,
                verdict="incorrect",
            ),
        )

        receipt.validate(manifest)

        self.assert_contract_error(
            "incorrect-scope-boundary-required-change-missing",
            lambda: replace(
                receipt,
                scope_boundary_review=replace(
                    receipt.scope_boundary_review,
                    required_change=NO_REQUIRED_CHANGE,
                ),
            ).validate(manifest),
        )

    def test_verified_scope_boundary_rejects_spurious_required_change(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        boundary = replace(
            self._scope_boundary(manifest),
            required_change="Изменить корректную границу без причины.",
        )

        self.assert_contract_error(
            "verified-scope-boundary-required-change-invalid",
            lambda: boundary.validate(manifest),
        )

    def test_embedded_contract_round_trip_authenticates_full_receipt_and_obligations(self) -> None:
        manifest = self._build()
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=tuple(self._review(item) for item in manifest.assertions),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        evidence = render_embedded_source_assertion_contract(manifest, receipt)

        restored = parse_embedded_source_assertion_contract(
            evidence,
            self.repo_root,
            expected_scope_slug="applications-menu-search",
            expected_obligation_ids=tuple(
                item.obligation_ids[0] for item in manifest.assertions
            ),
        )

        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertEqual(manifest.digest, restored.manifest.digest)
        self.assertEqual("accepted", restored.review_receipt.decision)
        self.assertIn('"assertion_reviews"', evidence)
        self.assertIn('"scope_boundary_review"', evidence)

    def test_empty_source_first_marker_is_not_an_authenticated_contract(self) -> None:
        self.assert_contract_error(
            "incomplete-embedded-source-contract",
            lambda: parse_embedded_source_assertion_contract(
                "<!-- SOURCE-ASSERTIONS-V4 -->\n",
                self.repo_root,
                expected_scope_slug="applications-menu-search",
                expected_obligation_ids=(),
            ),
        )

    def test_legacy_embedded_contract_is_not_treated_as_plain_evidence(self) -> None:
        self.assert_contract_error(
            "legacy-embedded-source-contract-requires-rematerialization",
            lambda: parse_embedded_source_assertion_contract(
                "<!-- SOURCE-ASSERTIONS-V1 -->\n"
                "bounded-source-first-assertions-v1\n",
                self.repo_root,
                expected_scope_slug="applications-menu-search",
                expected_obligation_ids=(),
            ),
        )

    def test_forged_embedded_manifest_digest_is_rejected(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(
                self._review(manifest.assertions[0]),
            ),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        evidence = render_embedded_source_assertion_contract(manifest, receipt).replace(
            manifest.digest, "0" * 64, 1
        )

        self.assert_contract_error(
            "embedded-manifest-digest-mismatch",
            lambda: parse_embedded_source_assertion_contract(
                evidence,
                self.repo_root,
                expected_scope_slug="applications-menu-search",
                expected_obligation_ids=("OBL-AMS-003",),
            ),
        )

    def test_embedded_contract_rejects_incomplete_receipt_and_wrong_obligation_set(self) -> None:
        manifest = self._build((self._assertion(3, "Фамилия"),))
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=self._inventory_review(manifest),
            assertion_reviews=(
                self._review(manifest.assertions[0]),
            ),
            scope_boundary_review=self._scope_boundary(manifest),
        )
        evidence = render_embedded_source_assertion_contract(manifest, receipt)
        incomplete_receipt = json.dumps(
            {
                "version": REVIEW_RECEIPT_VERSION,
                "manifest_digest": manifest.digest,
                "decision": "accepted",
                "reviewed_assertion_count": 1,
            },
            separators=(",", ":"),
        )
        forged = evidence.replace(
            json.dumps(
                receipt.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            incomplete_receipt,
        )
        self.assert_contract_error(
            "invalid-fields",
            lambda: parse_embedded_source_assertion_contract(
                forged,
                self.repo_root,
                expected_scope_slug="applications-menu-search",
                expected_obligation_ids=("OBL-AMS-003",),
            ),
        )
        self.assert_contract_error(
            "embedded-obligation-set-mismatch",
            lambda: parse_embedded_source_assertion_contract(
                evidence,
                self.repo_root,
                expected_scope_slug="applications-menu-search",
                expected_obligation_ids=("OBL-OTHER",),
            ),
        )

if __name__ == "__main__":
    unittest.main()
