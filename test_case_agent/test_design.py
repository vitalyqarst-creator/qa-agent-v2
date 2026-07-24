from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import (
    CoverageCase,
    CoverageGraph,
    CoverageObligation,
    CoverageProperty,
)


class DesignError(ValueError):
    """A typed coverage item cannot be rendered without inventing behavior."""


_SPACE = re.compile(r"\s+")
_CALIBRATION_PROCESS_MARKER = re.compile(
    r"(?:калибр|candidate[-_ ]ui|ui[- ]реакц|ui[- ]триггер|"
    r"требует\s+подтвержден)",
    re.IGNORECASE,
)
_QUALIFIED_SUBJECT = re.compile(
    r"^(?:поле|список|кнопка|элемент|блок)\b",
    re.IGNORECASE,
)
_INPUT_ACTION_KINDS = frozenset(
    {
        "editability",
        "positive-input",
        "invalid-input",
        "source-editability",
        "source-format",
        "source-date-boundary",
        "source-exact-length",
    }
)
_HIDDEN_STATE = re.compile(
    r"(?:\bскрыт\w*\b|\bотсутств\w*\b|\bне\s+отображ\w*\b)",
    re.IGNORECASE,
)
_BEFORE_TRANSITION = re.compile(r"\b(?:до|перед)\b", re.IGNORECASE)
_DISPLAYED_STATE = re.compile(r"\bотображ\w*\b", re.IGNORECASE)
_DEFAULT_STATE = re.compile(r"\bпо\s+умолчанию\b", re.IGNORECASE)
_ALWAYS_INVARIANT = re.compile(r"\bвсегда\b", re.IGNORECASE)
_OPEN_DISPLAYED_ACTION = re.compile(
    r"^открыть\s+(?:уже\s+)?отображаем\w*\b",
    re.IGNORECASE,
)
_OPEN_STATE_ACTION = re.compile(r"^открыть\s+состояние\b", re.IGNORECASE)
_POST_HIDDEN_TRANSITION = re.compile(
    r"\s+(?:и|,)\s+(?:затем\s+)?(?:отображ|появ)\w*\b",
    re.IGNORECASE,
)
_REPEATER_ADD_CONTRACT = ("source-add-row", "repeater-add")
_REPEATER_DELETE_CONTRACT = ("source-delete-row", "repeater-delete")
_REPEATER_ADD_CONTRACTS = frozenset(
    {
        _REPEATER_ADD_CONTRACT,
        ("source-action", "repeatable-add"),
    }
)
_REPEATER_DELETE_CONTRACTS = frozenset(
    {
        _REPEATER_DELETE_CONTRACT,
        ("source-action", "repeatable-delete"),
    }
)
_REPEATER_MUTATION_CONTRACTS = _REPEATER_ADD_CONTRACTS | _REPEATER_DELETE_CONTRACTS
_INVARIANT_TRANSITION_CONTRACTS = frozenset(
    {
        # An add-row action changes the repeater state without consuming the
        # add control.  Other state changes (especially delete) are not assumed
        # to preserve the invariant subject.
        *_REPEATER_ADD_CONTRACTS,
    }
)
_SETUP_ACTION_START = re.compile(
    r"^(?:авторизоваться|войти|открыть|перейти|нажать|удалить|"
    r"очистить|создать|добавить|выбрать|установить|ввести|заполнить|"
    r"оставить|загрузить|перетащить|вставить|раскрыть|развернуть|"
    r"закрыть|активировать|выделить|прокрутить|получить|сохранить|указать|"
    r"найти|включить|выполнить|"
    r"log\s+in|open|navigate|click|delete|clear|create|add|select|set|"
    r"enter|fill|leave|upload|drag|drop|insert|expand|close|activate|"
    r"scroll)\b",
    re.IGNORECASE,
)
_LOCATIVE_SETUP_ACTION = re.compile(
    r"^(?:в|на)\s+(?:[А-ЯЁа-яё-]+\s+){0,3}"
    r"(?:пол(?:е|я|ю|ем)|блок(?:е|а|у|ом)|списк(?:е|а|у|ом)|"
    r"переключател(?:е|ь|я|ю|ем))\b[^.\n;]{0,160}\b"
    r"(?:выбрать|установить|ввести|заполнить|оставить|очистить|нажать|"
    r"выполнить)\b",
    re.IGNORECASE,
)
_RUNTIME_LABEL = re.compile(r"`([^`\r\n]+)`|«([^»\r\n]+)»")
_CARD_CONTEXT = re.compile(r"\bкарточк\w*\b", re.IGNORECASE)
_BLOCK_CONTEXT = re.compile(r"\bблок(?:е|а|у|ом|и|ов)?(?:-повторител[ья])?\b", re.IGNORECASE)
_FIELD_CONTEXT = re.compile(r"\bпол(?:е|я|ю|ем)\b", re.IGNORECASE)
_SELECTED_VALUE_STATE = re.compile(
    r"\b(?:выбран(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"установлен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?)\b"
    r"[^.\n;]{0,80}\bзначени\w*\b",
    re.IGNORECASE,
)
_REPEATER_ROW_CONTEXT = re.compile(
    r"(?:после\s+(?:действия\s+)?добавлен\w+|"
    r"\bстрок(?:а|и|у|ой|е)\b|"
    r"\b(?:ввод|выбор)\s+(?:значени\w*|дат\w*)\s+в\s+пол(?:е|я|ю|ем)\b|"
    r"\bпол(?:е|я|ю|ем)\b[^.\n;]{0,120}\bблок(?:е|а|у|ом|и)?\b)",
    re.IGNORECASE,
)
_GENERIC_VALIDATION_TRIGGER = re.compile(
    r"(?:проверить\s+обязательност|проверить\s+валидац|"
    r"выполнить\s+действие\s+проверки/валидации|"
    r"инициир\w*\s+доступн\w*\s+точк\w*\s+проверк|"
    r"check\s+requiredness|trigger\s+validation)",
    re.IGNORECASE,
)


DETERMINISTIC_PROPERTY_KINDS = frozenset(
    {
        "visibility",
        "default",
        "editability",
        "dictionary",
        "positive-input",
        "requiredness",
        "optionalness",
        "invalid-input",
    }
)


@dataclass(frozen=True)
class DesignContext:
    package_id: str
    scope_title: str
    base_preconditions: tuple[str, ...]
    subject_labels: Mapping[str, str]
    condition_preconditions: Mapping[str, str]
    priorities: Mapping[str, str] | None = None

    def validate(self) -> None:
        if not self.package_id.strip():
            raise DesignError("package_id must be non-empty")
        if not self.scope_title.strip():
            raise DesignError("scope_title must be non-empty")
        if any(not item.strip() for item in self.base_preconditions):
            raise DesignError("base_preconditions must contain only non-empty steps")
        for key, label in self.subject_labels.items():
            if not key.strip() or not label.strip():
                raise DesignError("subject_labels must contain non-empty keys and labels")
        for key, precondition in self.condition_preconditions.items():
            if key == "always" or not key.strip() or not precondition.strip():
                raise DesignError(
                    "condition_preconditions must define non-always typed conditions"
                )
        for case_key, priority in (self.priorities or {}).items():
            if not case_key.strip() or priority not in {"низкий", "средний", "высокий"}:
                raise DesignError("priorities contains an invalid entry")


def _normalized_text(value: str) -> str:
    return _SPACE.sub(" ", value).strip().casefold()


def _contains_token_bounded_text(source: str, fragment: str) -> bool:
    """Match a source fragment without accepting a substring of another word."""

    source_text = _normalized_text(source)
    fragment_text = _normalized_text(fragment)
    if not fragment_text:
        return False
    start = 0
    while True:
        index = source_text.find(fragment_text, start)
        if index < 0:
            return False
        end = index + len(fragment_text)
        left_cut = index > 0 and source_text[index - 1].isalnum() and fragment_text[0].isalnum()
        right_cut = (
            end < len(source_text)
            and source_text[end].isalnum()
            and fragment_text[-1].isalnum()
        )
        if not left_cut and not right_cut:
            return True
        start = index + 1


def validate_design_context_for_graph(
    graph: CoverageGraph,
    context: DesignContext,
    *,
    expected_package_id: str | None = None,
) -> None:
    """Bind every behavioral context string to the accepted graph projection.

    ``DesignContext`` is presentation/configuration data, not another prose source.
    Subject labels therefore must occur in the source-backed property projection,
    while preconditions must be exact accepted canonical/atomic/oracle statements.
    This prevents a config or model from smuggling new UI behavior into a case.
    """

    context.validate()
    if expected_package_id is not None:
        if (
            not isinstance(expected_package_id, str)
            or not expected_package_id.strip()
            or expected_package_id != expected_package_id.strip()
        ):
            raise DesignError("expected_package_id must be non-empty trimmed text")
        if context.package_id != expected_package_id:
            raise DesignError(
                "design_context.package_id does not match the bound obligation "
                f"package: expected={expected_package_id}, actual={context.package_id}"
            )
    tc_properties = {
        item.property_id: item for item in graph.properties if item.disposition == "tc"
    }
    expected_subjects = {item.subject_key for item in tc_properties.values()}
    actual_subjects = set(context.subject_labels)
    if actual_subjects != expected_subjects:
        raise DesignError(
            "subject_labels must exactly cover graph subjects; "
            f"missing={sorted(expected_subjects - actual_subjects)}, "
            f"unknown={sorted(actual_subjects - expected_subjects)}"
        )

    context_statements = tuple(
        dict.fromkeys(
            text
            for text in (
                *(item.canonical_statement for item in graph.properties),
                *(
                    clause
                    for item in graph.properties
                    for clause in item.condition_clauses
                ),
                *(
                    text
                    for item in graph.obligations
                    for text in (
                        item.atomic_statement,
                        item.observable_oracle,
                        item.validation_trigger,
                    )
                ),
            )
            if text.strip()
        )
    )
    if context.scope_title != graph.scope_slug and not any(
        _contains_token_bounded_text(statement, context.scope_title)
        for statement in context_statements
    ):
        raise DesignError(
            "scope_title is not present in a source-backed context statement"
        )

    obligations_by_property: dict[str, list[CoverageObligation]] = {
        key: [] for key in tc_properties
    }
    for obligation in graph.obligations:
        if obligation.property_id in obligations_by_property:
            obligations_by_property[obligation.property_id].append(obligation)
    properties_by_source_row: dict[str, list[CoverageProperty]] = {}
    for prop in tc_properties.values():
        properties_by_source_row.setdefault(prop.source_row_id, []).append(prop)
    for property_id, prop in tc_properties.items():
        label = context.subject_labels[prop.subject_key]
        # A table row owns one UI subject even when an atomic sibling (for
        # example a date boundary) omits the repeated field name.  Bind labels
        # only within the same immutable source row; never borrow a label from
        # another row or from free configuration text.
        row_properties = properties_by_source_row[prop.source_row_id]
        evidence = []
        for row_property in row_properties:
            evidence.append(row_property.canonical_statement)
            evidence.extend(
                text
                for obligation in obligations_by_property[row_property.property_id]
                for text in (
                    obligation.atomic_statement,
                    obligation.observable_oracle,
                    obligation.validation_trigger,
                )
            )
        if not any(_contains_token_bounded_text(text, label) for text in evidence):
            raise DesignError(
                f"subject label for {prop.subject_key} is not present in its "
                "source-backed graph projection"
            )

    expected_conditions = {
        item.condition_key for item in graph.obligations if item.condition_key != "always"
    }
    actual_conditions = set(context.condition_preconditions)
    if actual_conditions != expected_conditions:
        raise DesignError(
            "condition_preconditions must exactly cover graph conditions; "
            f"missing={sorted(expected_conditions - actual_conditions)}, "
            f"unknown={sorted(actual_conditions - expected_conditions)}"
        )

    for index, precondition in enumerate(context.base_preconditions):
        if precondition not in context_statements:
            raise DesignError(
                f"base_preconditions[{index}] is not an exact source-backed "
                "context statement"
            )
    for condition_key, precondition in context.condition_preconditions.items():
        condition_obligations = tuple(
            item
            for item in graph.obligations
            if item.condition_key == condition_key
        )
        if not condition_obligations:  # pragma: no cover - set equality owns this
            raise DesignError(
                f"condition_preconditions[{condition_key!r}] has no obligation"
            )
        for item in condition_obligations:
            prop = tc_properties[item.property_id]
            if prop.condition_clauses:
                allowed = (
                    prop.condition_clauses
                    if len(prop.condition_clauses) == 1
                    else (prop.canonical_statement,)
                )
            else:
                # Compatibility for explicitly supplied legacy derivations. New
                # compiler output always carries accepted condition clauses on
                # the graph property.
                allowed = (item.atomic_statement, item.observable_oracle)
            if precondition not in allowed:
                raise DesignError(
                    f"condition_preconditions[{condition_key!r}] is not the "
                    "exact accepted condition for its source property"
                )

    unknown_priorities = set(context.priorities or ()) - {
        item.case_key for item in graph.cases
    }
    if unknown_priorities:
        raise DesignError(
            f"priorities reference unknown cases {sorted(unknown_priorities)}"
        )


@dataclass(frozen=True)
class TestCaseDesign:
    case_key: str
    tc_id: str
    status: str
    title: str
    case_type: str
    priority: str
    package_id: str
    traceability: tuple[str, ...]
    preconditions: tuple[str, ...]
    test_data: tuple[str, ...]
    steps: tuple[str, ...]
    expected_result: str
    postconditions: tuple[str, ...]
    calibration_question: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WriterReference:
    reference_id: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class WriterCard:
    case_key: str
    tc_id: str
    status: str
    property_id: str
    assertion_id: str
    subject_key: str
    subject_label: str
    property_kind: str
    condition_key: str
    condition_clauses: tuple[str, ...]
    obligation_id: str
    atom_id: str
    coverage_variant: str
    atomic_statement: str
    observable_oracle: str
    requirement_codes: tuple[str, ...]
    validation_trigger: str
    fixture_values: tuple[str, ...]
    cleanup_strategy: str
    source_oracle_id: str
    calibration_question: str
    writer_required_reason: str
    runner_title: str
    subject_id: str
    expected_result_id: str
    fixture_references: tuple[WriterReference, ...]
    data_references: tuple[WriterReference, ...]
    action_references: tuple[WriterReference, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlockedCard:
    case_key: str
    tc_id: str
    obligation_id: str
    property_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class _RepeaterMutationSupport:
    add_prop: CoverageProperty
    add_obligation: CoverageObligation
    delete_prop: CoverageProperty
    delete_obligation: CoverageObligation


@dataclass(frozen=True)
class _InvariantTransition:
    prop: CoverageProperty
    obligation: CoverageObligation
    mutation_support: _RepeaterMutationSupport


@dataclass(frozen=True)
class TestDesignPlan:
    schema_version: int
    graph_digest: str
    deterministic_cases: tuple[TestCaseDesign, ...]
    writer_cards: tuple[WriterCard, ...]
    blocked_cards: tuple[BlockedCard, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _one_case_obligation(
    case: CoverageCase,
    obligations: Mapping[str, CoverageObligation],
) -> CoverageObligation:
    if len(case.obligation_ids) != 1:
        raise DesignError(
            f"{case.tc_id} must own exactly one obligation before deterministic design"
        )
    obligation_id = case.obligation_ids[0]
    try:
        return obligations[obligation_id]
    except KeyError as exc:  # pragma: no cover - coverage graph validation owns this
        raise DesignError(f"{case.tc_id} references unknown {obligation_id}") from exc


def _traceability(
    prop: CoverageProperty,
    obligation: CoverageObligation,
    *,
    support_obligations: Sequence[
        tuple[CoverageProperty, CoverageObligation]
    ] = (),
) -> tuple[str, ...]:
    values: list[str] = []

    def append_projection(
        source_prop: CoverageProperty,
        source_obligation: CoverageObligation,
    ) -> None:
        values.extend(
            (
                source_obligation.obligation_id,
                source_obligation.atom_id,
                source_prop.assertion_id,
                *source_obligation.requirement_codes,
            )
        )
        if source_obligation.source_oracle_id:
            values.append(source_obligation.source_oracle_id)

    append_projection(prop, obligation)
    for support_prop, support_obligation in support_obligations:
        append_projection(support_prop, support_obligation)
    return tuple(dict.fromkeys(item for item in values if item))


def _support_fragments(obligation: CoverageObligation) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            item.strip()
            for item in (obligation.validation_trigger, obligation.cleanup_strategy)
            if item.strip()
        )
    )


def _materialized_support_obligations(
    *,
    primary_obligation: CoverageObligation,
    materialized_items: Sequence[str],
    invariant_transition: _InvariantTransition | None = None,
    repeater_support: _RepeaterMutationSupport | None = None,
) -> tuple[tuple[CoverageProperty, CoverageObligation], ...]:
    """Return only sibling obligations literally used by this case design.

    Reviewer evidence requires role-tagged support chains only for sibling
    obligations materialized in setup/action/cleanup.  Tracing every available
    repeater sibling creates false traceability when a reusable add/delete pair
    exists in the graph but the current case did not use that exact source
    action.
    """

    support: list[tuple[CoverageProperty, CoverageObligation]] = []
    seen: set[str] = {primary_obligation.obligation_id}
    rendered_items = tuple(item for item in materialized_items if item.strip())

    def append_if_materialized(
        source_prop: CoverageProperty,
        source_obligation: CoverageObligation,
    ) -> None:
        if source_obligation.obligation_id in seen:
            return
        fragments = _support_fragments(source_obligation)
        if not fragments:
            return
        if not any(
            fragment in item for fragment in fragments for item in rendered_items
        ):
            return
        seen.add(source_obligation.obligation_id)
        support.append((source_prop, source_obligation))

    if invariant_transition is not None:
        append_if_materialized(
            invariant_transition.prop,
            invariant_transition.obligation,
        )
        repeater_support = invariant_transition.mutation_support
    if repeater_support is not None:
        append_if_materialized(
            repeater_support.add_prop,
            repeater_support.add_obligation,
        )
        append_if_materialized(
            repeater_support.delete_prop,
            repeater_support.delete_obligation,
        )
    return tuple(support)


def _writer_card(
    *,
    case: CoverageCase,
    prop: CoverageProperty,
    obligation: CoverageObligation,
    subject_label: str,
    reason: str,
) -> WriterCard:
    def reference_id(prefix: str, index: int, text: str) -> str:
        digest = hashlib.sha256(
            f"{case.case_key}|{prefix}|{index}|{text}".encode("utf-8")
        ).hexdigest()[:16].upper()
        return f"{prefix}-{digest}"

    fixture_references = tuple(
        WriterReference(
            reference_id=reference_id("FIX", index, value),
            text=value,
        )
        for index, value in enumerate(obligation.fixture_values, 1)
    )
    data_references = tuple(
        WriterReference(
            reference_id=reference_id("DATA", index, fixture.text),
            text=f"Тестовое значение для {subject_label}: `{fixture.text}`.",
        )
        for index, fixture in enumerate(fixture_references, 1)
    )
    action_texts = [obligation.atomic_statement]
    if obligation.validation_trigger.strip():
        action_texts.append(obligation.validation_trigger)
    action_references = tuple(
        WriterReference(
            reference_id=reference_id("ACT", index, text),
            text=text,
        )
        for index, text in enumerate(action_texts, 1)
        if text.strip()
    )
    expected_result_id = obligation.source_oracle_id or reference_id(
        "ORACLE", 1, obligation.observable_oracle
    )
    return WriterCard(
        case_key=case.case_key,
        tc_id=case.tc_id,
        status=case.status,
        property_id=prop.property_id,
        assertion_id=prop.assertion_id,
        subject_key=prop.subject_key,
        subject_label=subject_label,
        property_kind=prop.property_kind,
        condition_key=obligation.condition_key,
        condition_clauses=prop.condition_clauses,
        obligation_id=obligation.obligation_id,
        atom_id=obligation.atom_id,
        coverage_variant=obligation.coverage_variant,
        atomic_statement=obligation.atomic_statement,
        observable_oracle=obligation.observable_oracle,
        requirement_codes=obligation.requirement_codes,
        validation_trigger=obligation.validation_trigger,
        fixture_values=obligation.fixture_values,
        cleanup_strategy=obligation.cleanup_strategy,
        source_oracle_id=obligation.source_oracle_id,
        calibration_question=obligation.calibration_question,
        writer_required_reason=reason,
        runner_title=obligation.atomic_statement.rstrip(". "),
        subject_id=prop.subject_key,
        expected_result_id=expected_result_id,
        fixture_references=fixture_references,
        data_references=data_references,
        action_references=action_references,
    )


def _blocked_card(
    *,
    case: CoverageCase,
    prop: CoverageProperty,
    obligation: CoverageObligation,
    reason: str,
) -> BlockedCard:
    return BlockedCard(
        case_key=case.case_key,
        tc_id=case.tc_id,
        obligation_id=obligation.obligation_id,
        property_id=prop.property_id,
        reason=reason,
    )


def _unique_steps(*values: str) -> list[str]:
    """Keep ordered executable actions without normalized duplicates."""

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value.strip():
            continue
        normalized = _normalized_text(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return result


def _is_setup_action(value: str) -> bool:
    text = value.strip()
    return (
        _SETUP_ACTION_START.match(text) is not None
        or _LOCATIVE_SETUP_ACTION.match(text) is not None
    )


def _runtime_labels_with_context(value: str) -> tuple[tuple[str, str], ...]:
    labels: list[tuple[str, str]] = []
    for match in _RUNTIME_LABEL.finditer(value):
        label = (match.group(1) or match.group(2) or "").strip()
        prefix = value[max(0, match.start() - 80) : match.start()]
        labels.append((label, prefix))
    return tuple(labels)


def _navigation_setup_from_source(value: str) -> tuple[str, ...]:
    """Infer only card/block navigation from exact source labels.

    This does not turn a passive source condition into a runtime assertion.  It
    uses already accepted UI container labels to build the minimum executable
    path required before a TC can interact with controls inside that container.
    """

    card = ""
    block = ""
    for label, prefix in _runtime_labels_with_context(value):
        if not any(character.isalnum() for character in label):
            continue
        if not card and _CARD_CONTEXT.search(prefix):
            card = label
        if not block and _BLOCK_CONTEXT.search(prefix):
            block = label
    if card and block:
        return (f"Открыть карточку `{card}` и перейти к блоку `{block}`.",)
    if block:
        return (f"Перейти к блоку `{block}`.",)
    if card:
        return (f"Открыть карточку `{card}`.",)
    return ()


def _selection_setup_from_condition(value: str) -> str:
    labels = _runtime_labels_with_context(value)
    if len(labels) < 2 or _SELECTED_VALUE_STATE.search(value) is None:
        return ""
    first_label = labels[0][0]
    second_label = labels[1][0]
    first_prefix = labels[0][1]
    if _FIELD_CONTEXT.search(first_prefix):
        return f"В поле `{first_label}` выбрать значение `{second_label}`."
    return ""


def _condition_needs_repeater_row(value: str) -> bool:
    if _DEFAULT_STATE.search(value) or _HIDDEN_STATE.search(value):
        return False
    if _DISPLAYED_STATE.search(value) and _BLOCK_CONTEXT.search(value):
        return True
    return _REPEATER_ROW_CONTEXT.search(value) is not None


def _looks_like_generic_fixture(value: str) -> bool:
    return _normalized_text(value) in {"тест", "тестовое значение"}


def _subject_fixture_values(
    graph: CoverageGraph,
    properties: Mapping[str, CoverageProperty],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    for obligation in graph.obligations:
        prop = properties.get(obligation.property_id)
        if prop is None:
            continue
        for value in obligation.fixture_values:
            item = value.strip()
            if not item or _looks_like_generic_fixture(item):
                continue
            result.setdefault(prop.subject_key, [])
            if item not in result[prop.subject_key]:
                result[prop.subject_key].append(item)
    return {key: tuple(values) for key, values in result.items()}


def _editability_fixture_values(
    *,
    prop: CoverageProperty,
    obligation: CoverageObligation,
    subject_fixture_values: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    related = subject_fixture_values.get(prop.subject_key, ())
    if related:
        return related[:2]
    return tuple(
        value
        for value in obligation.fixture_values
        if value.strip() and not _looks_like_generic_fixture(value)
    )[:2]


def _source_input_action_with_value(
    *,
    kind: str,
    action: str,
    label: str,
    value: str,
) -> str:
    bound_action = _bind_input_action(kind=kind, action=action, label=label)
    return f"{bound_action.rstrip('. ')}; использовать значение `{value}`."


def _validation_commit_step(
    *,
    label: str,
    action: str,
    calibration_candidate: bool = False,
) -> str:
    value = action.strip().rstrip(". ")
    if _normalized_text(value).startswith("оставить "):
        return f"{value}."
    if calibration_candidate and _GENERIC_VALIDATION_TRIGGER.search(value):
        return (
            f"Инициировать проверку для {label}: завершить ввод, перевести "
            "фокус из поля или выполнить другое доступное действие проверки."
        )
    return (
        f"Выполнить действие проверки/валидации для {label}: "
        f"{value}."
    )


def _repeater_navigation_from_context(context: DesignContext) -> tuple[str, ...]:
    for value in context.condition_preconditions.values():
        navigation = _navigation_setup_from_source(value)
        if any(_BLOCK_CONTEXT.search(item) for item in navigation):
            return navigation
    return ()


def _requires_phone_exact_length_negatives(
    *,
    label: str,
    obligation: CoverageObligation,
) -> bool:
    text = _normalized_text(
        " ".join((label, obligation.atomic_statement, obligation.observable_oracle))
    )
    return "телефон" in text and "10" in text and "числов" in text


def _requires_text_hyphen_negatives(obligation: CoverageObligation) -> bool:
    text = _normalized_text(
        " ".join((obligation.atomic_statement, obligation.observable_oracle))
    )
    return "только" in text and ("дефис" in text or "`-`" in text or "символ `-`" in text)


def _future_date_fixture() -> str:
    return "31.12.2099"


def runtime_preconditions_for_binding(
    *,
    prop: CoverageProperty,
    obligation: CoverageObligation,
    context: DesignContext,
    repeater_add_action: str = "",
    include_repeater_reveal: bool = True,
) -> tuple[str, ...]:
    """Build production-runtime setup without losing source condition evidence.

    ``DesignContext.condition_preconditions`` remains the source-first binding
    for reviewer projection.  Runtime TC preconditions are a different layer:
    they must be executable actions.  Passive source states are therefore used
    only to infer safe navigation/reveal setup from source labels or exact
    source action triggers; if that cannot be done, the case is blocked.
    """

    condition = ""
    if obligation.condition_key != "always":
        condition = context.condition_preconditions.get(obligation.condition_key, "").strip()
        if not condition:
            raise DesignError(f"missing precondition for {obligation.condition_key}")

    actions: list[str] = []
    for item in (*context.base_preconditions, condition):
        value = item.strip()
        if not value:
            continue
        if _is_setup_action(value):
            actions.append(value)
            continue
        actions.extend(_navigation_setup_from_source(value))
    if condition:
        selected_value_setup = _selection_setup_from_condition(condition)
        if selected_value_setup:
            if include_repeater_reveal and repeater_add_action.strip():
                actions.append(repeater_add_action.strip())
            actions.append(selected_value_setup)
        if (
            include_repeater_reveal
            and repeater_add_action.strip()
            and _condition_needs_repeater_row(condition)
        ):
            actions.append(repeater_add_action.strip())

    unique = tuple(_unique_steps(*actions))
    if unique:
        return unique
    if condition:
        raise DesignError(
            f"{obligation.condition_key} has no executable runtime setup path"
        )
    return ("Не требуются.",)


def _display_subject(label: str) -> str:
    """Render a typed label without guessing grammatical gender or UI kind."""

    value = label.strip()
    if _QUALIFIED_SUBJECT.match(value) or (value.startswith("«") and value.endswith("»")):
        return value
    return f"«{value.strip('«»')}»"


def _bind_input_action(*, kind: str, action: str, label: str) -> str:
    """Add a target only for input-like kinds whose typed action omitted it.

    The accepted action remains byte-for-byte inside the resulting step.  This
    is a deterministic scoping wrapper, not a linguistic rewrite of source
    behavior.
    """

    value = action.strip()
    if kind not in _INPUT_ACTION_KINDS or _contains_token_bounded_text(value, label):
        return value
    target = (
        f"({label})"
        if _QUALIFIED_SUBJECT.match(label)
        else f"«{label.strip('«»')}»"
    )
    return f"В целевом элементе {target} выполнить действие: {value}"


def _hidden_before_source_clause(
    *,
    prop: CoverageProperty,
    obligation: CoverageObligation,
) -> str:
    """Return only an accepted clause that explicitly owns the initial hidden state.

    The runner may add an observation wrapper, but it must not synthesize an
    initial state merely because a later-state visibility oracle exists.  Prefer
    the observable oracle and fall back to the canonical property statement.
    """

    for source in (obligation.observable_oracle, prop.canonical_statement):
        for raw_clause in re.split(r";\s*", source.strip()):
            clause = raw_clause.strip().rstrip(". ")
            if not clause:
                continue
            if not _HIDDEN_STATE.search(clause) or not _BEFORE_TRANSITION.search(clause):
                continue
            # A canonical sentence can own both states ("hidden until ... and
            # then displayed").  Retain its exact initial substring rather than
            # paraphrasing that behavior into a new oracle.
            boundary = _POST_HIDDEN_TRANSITION.search(clause)
            return (clause[: boundary.start()] if boundary else clause).strip()
    return ""


def _source_observation_step(*, prefix: str, source_clause: str) -> str:
    """Wrap an exact accepted clause as an executable observation."""

    return f"{prefix}: {source_clause.strip().rstrip('. ')}."


def _source_row_action(*, row: str, action: str) -> str:
    """Bind an exact accepted action to a deterministic test-row identity."""

    return f"Для {row} выполнить действие: {action.strip()}"


def _select_repeater_mutation_support(
    *,
    graph: CoverageGraph,
    properties: Mapping[str, CoverageProperty],
    context: DesignContext,
    executable_obligations: set[str],
) -> dict[str, _RepeaterMutationSupport]:
    """Pair exact add/delete actions; ordinal row identity needs no field data."""

    def mutation_candidates(
        contracts: frozenset[tuple[str, str]],
    ) -> list[tuple[CoverageProperty, CoverageObligation]]:
        result: list[tuple[CoverageProperty, CoverageObligation]] = []
        for item in graph.obligations:
            prop = properties.get(item.property_id)
            if prop is None:
                continue
            if (
                (prop.property_kind, item.coverage_variant) in contracts
                and item.obligation_id in executable_obligations
                and item.coverage_status == "testable"
                and item.validation_trigger.strip()
            ):
                result.append((prop, item))
        return sorted(result, key=lambda pair: pair[1].obligation_id)

    adds = mutation_candidates(_REPEATER_ADD_CONTRACTS)
    deletes = mutation_candidates(_REPEATER_DELETE_CONTRACTS)
    if not adds or not deletes:
        return {}

    pairs: list[
        tuple[
            tuple[CoverageProperty, CoverageObligation],
            tuple[CoverageProperty, CoverageObligation],
        ]
    ] = []
    if len(adds) == 1 and len(deletes) == 1:
        pairs.append((adds[0], deletes[0]))
    else:
        for add in adds:
            add_evidence = " ".join(
                (
                    add[0].canonical_statement,
                    add[1].atomic_statement,
                    add[1].observable_oracle,
                )
            )
            for delete in deletes:
                delete_label = context.subject_labels.get(
                    delete[0].subject_key,
                    "",
                )
                if delete_label and _contains_token_bounded_text(
                    add_evidence,
                    delete_label,
                ):
                    pairs.append((add, delete))

    supports: dict[str, _RepeaterMutationSupport] = {}
    for (add_prop, add_obligation), (delete_prop, delete_obligation) in pairs:
        support = _RepeaterMutationSupport(
            add_prop=add_prop,
            add_obligation=add_obligation,
            delete_prop=delete_prop,
            delete_obligation=delete_obligation,
        )
        supports[add_obligation.obligation_id] = support
        supports[delete_obligation.obligation_id] = support
    return supports


def _candidate_product_title(value: str) -> str:
    """Keep only source-backed product behavior in candidate title metadata."""

    source = value.strip()
    marker = _CALIBRATION_PROCESS_MARKER.search(source)
    if marker is None:
        return source.rstrip(". ")
    prefix = source[: marker.start()]
    # Remove the complete process clause that owns the marker.  Selecting the
    # last boundary avoids truncating at dots inside an earlier requirement
    # reference such as `BSR 182. Ограничение ...`.
    boundaries = tuple(
        re.finditer(r"(?:;\s*|[.!?](?:[»\"])?\s+)", prefix)
    )
    if not boundaries:
        return ""
    return prefix[: boundaries[-1].start()].strip().rstrip(". ")


def _candidate_question(
    value: str,
    *,
    label: str,
    fixtures: Sequence[str],
) -> str:
    """Turn a declarative missing-oracle note into an explicit bounded question."""

    question = value.strip()
    if question.endswith("?"):
        return question
    normalized_label = label.strip()
    if re.match(r"(?i)^(?:поле|список|кнопка|элемент|блок)\b", normalized_label):
        target = normalized_label
    else:
        target = f"элемента «{normalized_label.strip('«»')}»"
    if fixtures:
        return (
            "Какой точный наблюдаемый UI-отклик возникает при использовании "
            f"значения «{fixtures[0]}» для {target}?"
        )
    return f"Какой точный наблюдаемый UI-отклик возникает для {target}?"


def _materialize(
    *,
    case: CoverageCase,
    prop: CoverageProperty,
    obligation: CoverageObligation,
    context: DesignContext,
    subject_fixture_values: Mapping[str, tuple[str, ...]],
    invariant_transition: _InvariantTransition | None = None,
    repeater_support: _RepeaterMutationSupport | None = None,
) -> TestCaseDesign | WriterCard | BlockedCard:
    label = context.subject_labels.get(prop.subject_key, "").strip()
    if not label:
        return _blocked_card(
            case=case,
            prop=prop,
            obligation=obligation,
            reason="missing typed subject label",
        )
    kind = prop.property_kind
    condition = ""
    if obligation.condition_key != "always":
        condition = context.condition_preconditions.get(obligation.condition_key, "").strip()
        if not condition:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=f"missing precondition for {obligation.condition_key}",
            )
        if (
            not obligation.validation_trigger.strip()
            and prop.property_kind != "default"
        ):
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=(
                    f"{obligation.condition_key} has no source-backed setup/action trigger"
                ),
            )
    expected_result = obligation.observable_oracle.strip()
    if not expected_result:
        return _blocked_card(
            case=case,
            prop=prop,
            obligation=obligation,
            reason="missing source-backed observable oracle",
        )
    if (
        prop.property_kind not in DETERMINISTIC_PROPERTY_KINDS
        and not prop.property_kind.startswith("source-")
    ):
        return _writer_card(
            case=case,
            prop=prop,
            obligation=obligation,
            subject_label=label,
            reason=f"unsupported deterministic property_kind: {prop.property_kind}",
        )
    if (
        case.status == "candidate-ui-calibration"
        and kind == "positive-input"
        and (
            _requires_phone_exact_length_negatives(
                label=label,
                obligation=obligation,
            )
            or _requires_text_hyphen_negatives(obligation)
        )
    ):
        return _blocked_card(
            case=case,
            prop=prop,
            obligation=obligation,
            reason=(
                "candidate positive-input bundles derived invalid classes; "
                "semantic design must split positive acceptance and each "
                "invalid-input candidate before TC rendering"
            ),
        )

    repeater_add_action = (
        repeater_support.add_obligation.validation_trigger if repeater_support else ""
    )
    try:
        runtime_setup = runtime_preconditions_for_binding(
            prop=prop,
            obligation=obligation,
            context=context,
            repeater_add_action=repeater_add_action,
            include_repeater_reveal=(
                (kind, obligation.coverage_variant) not in _REPEATER_MUTATION_CONTRACTS
                and obligation.coverage_variant != "default-hidden"
            ),
        )
    except DesignError as exc:
        return _blocked_card(
            case=case,
            prop=prop,
            obligation=obligation,
            reason=str(exc),
        )
    fixtures = obligation.fixture_values
    preconditions = (
        []
        if runtime_setup == ("Не требуются.",)
        else list(runtime_setup)
    )
    if (
        repeater_support is not None
        and repeater_add_action.strip()
        and repeater_add_action.strip() in preconditions
        and not any(_BLOCK_CONTEXT.search(item) for item in preconditions)
    ):
        preconditions = [
            *_repeater_navigation_from_context(context),
            *preconditions,
        ]
    if kind == "source-conditional-visibility" and fixtures:
        selected_fixture = _normalized_text(fixtures[0])
        preconditions = [
            item
            for item in preconditions
            if not (
                selected_fixture
                and selected_fixture in _normalized_text(item)
                and ("выбрать" in _normalized_text(item) or "установить" in _normalized_text(item))
            )
        ]
    title = ""
    case_type = "позитивный"
    test_data: list[str] = []
    steps: list[str] = []
    postconditions_override: tuple[str, ...] = ()

    if (kind, obligation.coverage_variant) in _REPEATER_MUTATION_CONTRACTS:
        if repeater_support is None:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=(
                    "repeater mutation lacks a source-backed sibling add/delete "
                    "action pair; classify as calibration/gap"
                ),
            )
        title = obligation.atomic_statement.rstrip(". ")
        case_type = "негативный" if prop.polarity == "negative" else "позитивный"
        add_action = repeater_support.add_obligation.validation_trigger
        delete_action = repeater_support.delete_obligation.validation_trigger
        if (kind, obligation.coverage_variant) in _REPEATER_ADD_CONTRACTS:
            steps = [obligation.validation_trigger]
            postconditions_override = (
                _source_row_action(
                    row="добавленной тестовой строки",
                    action=delete_action,
                ),
            )
        else:
            test_data = [
                "Первая тестовая строка: первая по порядку.",
                "Вторая тестовая строка: вторая по порядку.",
            ]
            preconditions.extend((add_action, add_action))
            steps = [
                _source_row_action(
                    row="первой тестовой строки",
                    action=obligation.validation_trigger,
                )
            ]
            postconditions_override = (
                _source_row_action(
                    row="оставшейся второй тестовой строки",
                    action=delete_action,
                ),
            )
    elif kind in {"source-requiredness", "source-optionalness"}:
        if not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=f"{kind} requires an explicit validation trigger",
            )
        is_required = kind == "source-requiredness"
        case_type = "негативный" if is_required else "позитивный"
        title = obligation.atomic_statement.rstrip(". ")
        test_data = [f"{label}: оставить пустым."]
        steps = _unique_steps(
            f"Оставить {label} пустым.",
            _validation_commit_step(
                label=label,
                action=obligation.validation_trigger,
                calibration_candidate=case.status == "candidate-ui-calibration",
            ),
        )
    elif kind == "source-editability":
        if not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="source-editability requires an exact action contract",
            )
        values = _editability_fixture_values(
            prop=prop,
            obligation=obligation,
            subject_fixture_values=subject_fixture_values,
        )
        if not values:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="source-editability requires a valid same-subject fixture value",
            )
        title = obligation.atomic_statement.rstrip(". ")
        case_type = "негативный" if prop.polarity == "negative" else "позитивный"
        test_data = [f"Тестовое значение: `{values[0]}`."]
        steps = _unique_steps(
            _source_input_action_with_value(
                kind=kind,
                action=obligation.validation_trigger,
                label=label,
                value=values[0],
            )
        )
    elif kind == "source-date-boundary" and obligation.coverage_variant == "not-future":
        if not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="source-date-boundary requires an exact action contract",
            )
        future_value = _future_date_fixture()
        title = obligation.atomic_statement.rstrip(". ")
        case_type = "негативный"
        test_data = [f"Недопустимое значение даты больше текущей даты: `{future_value}`."]
        steps = _unique_steps(
            _source_input_action_with_value(
                kind=kind,
                action=obligation.validation_trigger,
                label=label,
                value=future_value,
            )
        )
    elif kind.startswith("source-"):
        if not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="source-bound generic design requires an exact action contract",
            )
        if prop.polarity not in {"positive", "negative"}:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="source-bound generic design requires positive/negative polarity",
            )
        title = obligation.atomic_statement.rstrip(". ")
        case_type = "негативный" if prop.polarity == "negative" else "позитивный"
        test_data = [f"Тестовое значение: `{item}`." for item in fixtures]
        steps = _unique_steps(
            _bind_input_action(
                kind=kind,
                action=obligation.validation_trigger,
                label=label,
            )
        )
    elif kind == "visibility":
        title = f"Отображение: {_display_subject(label)}"
        fallback = f"Проверить отображение {label}."
        if obligation.coverage_variant == "always-visible" or _ALWAYS_INVARIANT.search(
            obligation.atomic_statement
        ):
            transition_obligation = (
                invariant_transition.obligation
                if invariant_transition is not None
                else repeater_support.add_obligation
                if repeater_support is not None
                else None
            )
            transition_cleanup = (
                invariant_transition.mutation_support.delete_obligation.validation_trigger
                if invariant_transition is not None
                else repeater_support.delete_obligation.validation_trigger
                if repeater_support is not None
                else ""
            )
            if transition_obligation is None:
                return _blocked_card(
                    case=case,
                    prop=prop,
                    obligation=obligation,
                    reason=(
                        "always-visible invariant has no executable source-backed "
                        "same-subject preserving transition; classify as "
                        "calibration/gap instead of testing one state"
                    ),
                )
            transition_action = transition_obligation.validation_trigger.strip()
            if not transition_action:  # pragma: no cover - selector owns this
                return _blocked_card(
                    case=case,
                    prop=prop,
                    obligation=obligation,
                    reason="always-visible invariant transition has no exact action",
                )
            initial_observation = _source_observation_step(
                prefix="Проверить исходное состояние",
                source_clause=expected_result,
            )
            after_observation = _source_observation_step(
                prefix="Проверить состояние после перехода",
                source_clause=expected_result,
            )
            steps = _unique_steps(
                obligation.validation_trigger,
                initial_observation,
                transition_action,
                after_observation,
            )
            postconditions_override = (
                _source_row_action(
                    row="добавленной тестовой строки",
                    action=transition_cleanup,
                ),
            )
        else:
            hidden_before = _hidden_before_source_clause(
                prop=prop,
                obligation=obligation,
            )
            initial_observation = (
                _source_observation_step(
                    prefix="Проверить исходное состояние",
                    source_clause=hidden_before,
                )
                if hidden_before
                else ""
            )
            trigger = obligation.validation_trigger or fallback
            if (
                obligation.coverage_variant in {"conditional-visibility", "visible"}
                and _DISPLAYED_STATE.search(condition)
                and (
                    _OPEN_DISPLAYED_ACTION.search(trigger.strip())
                    or _OPEN_STATE_ACTION.search(trigger.strip())
                )
            ):
                # The exact condition already establishes the displayed container.
                # Do not turn a generated "open displayed ..." phrase into product
                # behavior; observe the accepted oracle in that bounded state.
                trigger = _source_observation_step(
                    prefix="Проверить наблюдаемое состояние",
                    source_clause=expected_result,
                )
            steps = _unique_steps(initial_observation, trigger)
    elif kind == "default":
        if obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=(
                    "default initial-state observation must not carry a "
                    "focus/click validation trigger"
                ),
            )
        if len(fixtures) != 1:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="default requires exactly one concrete fixture value",
            )
        title = f"Значение по умолчанию: {_display_subject(label)}"
        test_data = [f"Ожидаемое значение: `{fixtures[0]}`."]
        if "курсор" in _normalized_text(
            " ".join((obligation.atomic_statement, expected_result))
        ):
            steps = _unique_steps(
                f"Нажать на {_display_subject(label)}.",
                _source_observation_step(
                    prefix="После нажатия проверить наблюдаемое состояние",
                    source_clause=expected_result,
                ),
            )
        else:
            # A default is the value present before the user changes the control.
            # Observe the exact accepted oracle immediately; a focus/click trigger
            # can itself mutate lazy masks, placeholders, or other initial UI state.
            steps = _unique_steps(
                _source_observation_step(
                    prefix=(
                        f"Не переводя фокус на {_display_subject(label)} "
                        "и не взаимодействуя с ним, проверить "
                        "первоначальное значение"
                    ),
                    source_clause=expected_result,
                )
            )
    elif kind == "editability":
        if len(fixtures) != 2 or fixtures[0] == fixtures[1]:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="editability requires two distinct concrete fixture values",
            )
        title = f"Редактирование: {_display_subject(label)}"
        test_data = [
            f"Исходное значение: `{fixtures[0]}`.",
            f"Новое значение: `{fixtures[1]}`.",
        ]
        preconditions.append(f"Ввести в {label} значение `{fixtures[0]}`.")
        fallback = (
            f"Заменить в {label} значение `{fixtures[0]}` на `{fixtures[1]}`."
        )
        steps = _unique_steps(
            _bind_input_action(
                kind=kind,
                action=obligation.validation_trigger or fallback,
                label=label,
            )
        )
    elif kind == "dictionary":
        if not fixtures:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="dictionary requires its complete concrete value set",
            )
        title = f"Состав списка: {_display_subject(label)}"
        test_data = ["Полный перечень: " + ", ".join(f"`{item}`" for item in fixtures) + "."]
        expected_result = (
            "Список содержит полный перечень значений: "
            + ", ".join(f"`{item}`" for item in fixtures)
            + "."
        )
        fallback = f"Открыть список {label}."
        steps = _unique_steps(obligation.validation_trigger or fallback)
    elif kind == "positive-input":
        if len(fixtures) != 1:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="positive-input requires exactly one concrete fixture value",
            )
        title = f"Ввод допустимого значения: {_display_subject(label)}"
        test_data = [f"Допустимое значение: `{fixtures[0]}`."]
        fallback = f"Ввести `{fixtures[0]}` в {label}."
        if _requires_phone_exact_length_negatives(
            label=label,
            obligation=obligation,
        ):
            test_data = [
                f"Допустимое значение: `{fixtures[0]}`.",
                "Недопустимое значение короче 10 цифр: `999123456`.",
                "Недопустимое значение длиннее 10 цифр: `99912345678`.",
                "Недопустимое нечисловое значение: `99912A4567`.",
            ]
            steps = _unique_steps(
                f"Ввести `{fixtures[0]}` в {label}.",
                f"Проверить, что значение `{fixtures[0]}` соответствует правилу: {expected_result.rstrip('. ')}.",
                f"Очистить {label} после проверки `{fixtures[0]}`.",
                "Ввести `999123456` в {label}.".format(label=label),
                "Проверить, что значение `999123456` не соответствует правилу: {oracle}.".format(
                    oracle=expected_result.rstrip(". ")
                ),
                f"Очистить {label} после проверки `999123456`.",
                "Ввести `99912345678` в {label}.".format(label=label),
                "Проверить, что значение `99912345678` не соответствует правилу: {oracle}.".format(
                    oracle=expected_result.rstrip(". ")
                ),
                f"Очистить {label} после проверки `99912345678`.",
                "Ввести `99912A4567` в {label}.".format(label=label),
                "Проверить, что значение `99912A4567` не соответствует правилу: {oracle}.".format(
                    oracle=expected_result.rstrip(". ")
                ),
            )
        elif _requires_text_hyphen_negatives(obligation):
            test_data = [
                f"Допустимое значение: `{fixtures[0]}`.",
                f"Недопустимое значение с цифрой: `{fixtures[0]}1`.",
                f"Недопустимое значение со спецсимволом: `{fixtures[0]}@`.",
            ]
            steps = _unique_steps(
                f"Ввести `{fixtures[0]}` в {label}.",
                f"Проверить, что значение `{fixtures[0]}` соответствует правилу: {expected_result.rstrip('. ')}.",
                f"Очистить {label} после проверки `{fixtures[0]}`.",
                f"Ввести `{fixtures[0]}1` в {label}.",
                f"Проверить, что значение `{fixtures[0]}1` не соответствует правилу: {expected_result.rstrip('. ')}.",
                f"Очистить {label} после проверки `{fixtures[0]}1`.",
                f"Ввести `{fixtures[0]}@` в {label}.",
                f"Проверить, что значение `{fixtures[0]}@` не соответствует правилу: {expected_result.rstrip('. ')}.",
            )
        else:
            steps = _unique_steps(
                _bind_input_action(
                    kind=kind,
                    action=obligation.validation_trigger or fallback,
                    label=label,
                )
            )
    elif kind in {"requiredness", "optionalness"}:
        if not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason=f"{kind} requires an explicit validation trigger",
            )
        case_type = "негативный" if kind == "requiredness" else "позитивный"
        title = (
            f"Обязательность {label}"
            if kind == "requiredness"
            else f"Необязательность {label}"
        )
        test_data = [f"{label}: оставить пустым."]
        steps = _unique_steps(
            f"Оставить {label} пустым.",
            _validation_commit_step(
                label=label,
                action=obligation.validation_trigger,
                calibration_candidate=case.status == "candidate-ui-calibration",
            ),
        )
    elif kind == "invalid-input":
        if len(fixtures) != 1 or not obligation.validation_trigger.strip():
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="invalid-input requires one fixture and an explicit validation trigger",
            )
        case_type = "негативный"
        title = f"Отклонение недопустимого значения: {_display_subject(label)}"
        test_data = [f"Недопустимое значение: `{fixtures[0]}`."]
        steps = _unique_steps(
            f"Ввести `{fixtures[0]}` в {label}.",
            _bind_input_action(
                kind=kind,
                action=obligation.validation_trigger,
                label=label,
            ),
        )

    postconditions = postconditions_override or (
        (obligation.cleanup_strategy,)
        if obligation.cleanup_strategy.strip()
        else ("Не требуются.",)
    )
    calibration_question = ""
    if case.status == "candidate-ui-calibration":
        title = _candidate_product_title(title)
        if not title:
            return _blocked_card(
                case=case,
                prop=prop,
                obligation=obligation,
                reason="calibration candidate has no product-behavior title",
            )
        calibration_question = _candidate_question(
            obligation.calibration_question,
            label=label,
            fixtures=fixtures,
        )
    rendered_preconditions = tuple(preconditions or ["Не требуются."])
    support_obligations = _materialized_support_obligations(
        primary_obligation=obligation,
        materialized_items=(
            *rendered_preconditions,
            *steps,
            *postconditions,
        ),
        invariant_transition=invariant_transition,
        repeater_support=repeater_support,
    )
    return TestCaseDesign(
        case_key=case.case_key,
        tc_id=case.tc_id,
        status=case.status,
        title=title,
        case_type=case_type,
        priority=(context.priorities or {}).get(case.case_key, "средний"),
        package_id=context.package_id,
        traceability=_traceability(
            prop,
            obligation,
            support_obligations=support_obligations,
        ),
        preconditions=rendered_preconditions,
        test_data=tuple(test_data or ["Не требуются."]),
        steps=tuple(steps),
        expected_result=expected_result,
        postconditions=postconditions,
        calibration_question=calibration_question,
    )


def build_test_design_plan(
    graph: CoverageGraph,
    *,
    context: DesignContext,
    expected_package_id: str | None = None,
) -> TestDesignPlan:
    validate_design_context_for_graph(
        graph,
        context,
        expected_package_id=expected_package_id,
    )
    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    executable_obligations = {
        obligation_id
        for graph_case in graph.cases
        if graph_case.status == "executable"
        for obligation_id in graph_case.obligation_ids
    }
    mutation_supports = _select_repeater_mutation_support(
        graph=graph,
        properties=properties,
        context=context,
        executable_obligations=executable_obligations,
    )
    fixture_values_by_subject = _subject_fixture_values(graph, properties)
    default_repeater_support = (
        sorted(
            {
                support.add_obligation.obligation_id: support
                for support in mutation_supports.values()
            }.values(),
            key=lambda item: item.add_obligation.obligation_id,
        )[0]
        if mutation_supports
        else None
    )
    invariant_transitions: dict[str, list[_InvariantTransition]] = {}
    for candidate in graph.obligations:
        candidate_prop = properties.get(candidate.property_id)
        if candidate_prop is None:  # pragma: no cover - graph validation owns this
            continue
        if (
            candidate.obligation_id not in executable_obligations
            or candidate.coverage_status != "testable"
            or not candidate.validation_trigger.strip()
            or candidate.obligation_id not in mutation_supports
            or (
                candidate_prop.property_kind,
                candidate.coverage_variant,
            )
            not in _INVARIANT_TRANSITION_CONTRACTS
        ):
            continue
        invariant_transitions.setdefault(candidate_prop.subject_key, []).append(
            _InvariantTransition(
                prop=candidate_prop,
                obligation=candidate,
                mutation_support=mutation_supports[candidate.obligation_id],
            )
        )
    for transitions in invariant_transitions.values():
        transitions.sort(key=lambda item: item.obligation.obligation_id)
    deterministic: list[TestCaseDesign] = []
    writer_cards: list[WriterCard] = []
    blocked_cards: list[BlockedCard] = []
    for case in sorted(graph.cases, key=lambda item: item.case_key):
        obligation = _one_case_obligation(case, obligations)
        try:
            prop = properties[obligation.property_id]
        except KeyError as exc:  # pragma: no cover - graph validation owns this
            raise DesignError(
                f"{obligation.obligation_id} references unknown property"
            ) from exc
        result = _materialize(
            case=case,
            prop=prop,
            obligation=obligation,
            context=context,
            subject_fixture_values=fixture_values_by_subject,
            invariant_transition=(
                invariant_transitions.get(prop.subject_key, [None])[0]
                if obligation.coverage_variant == "always-visible"
                else None
            ),
            repeater_support=(
                mutation_supports.get(obligation.obligation_id)
                or default_repeater_support
            ),
        )
        if isinstance(result, TestCaseDesign):
            deterministic.append(result)
        elif isinstance(result, WriterCard):
            writer_cards.append(result)
        else:
            blocked_cards.append(result)
    return TestDesignPlan(
        schema_version=1,
        graph_digest=graph.digest,
        deterministic_cases=tuple(deterministic),
        writer_cards=tuple(writer_cards),
        blocked_cards=tuple(blocked_cards),
    )


def _numbered(items: Sequence[str]) -> str:
    if tuple(items) == ("Не требуются.",):
        return "Не требуются."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def _bulleted(items: Sequence[str]) -> str:
    if tuple(items) == ("Не требуются.",):
        return "Не требуются."
    return "\n".join(f"- {item}" for item in items)


def render_test_cases(
    cases: Sequence[TestCaseDesign],
    *,
    scope_title: str,
) -> str:
    lines = [f"# Тест-кейсы: {scope_title}", ""]
    tc_ids: set[str] = set()
    for case in sorted(cases, key=lambda item: item.case_key):
        if case.tc_id in tc_ids:
            raise DesignError(f"duplicate TC-ID during rendering: {case.tc_id}")
        tc_ids.add(case.tc_id)
        lines.extend(
            [
                f"## {case.tc_id}",
                "",
                f"**Название:** {case.title}",
                f"**Тип:** {case.case_type}",
                f"**Приоритет:** {case.priority}",
                f"**package_id:** {case.package_id}",
                f"**Трассировка:** {'; '.join(case.traceability)}",
            ]
        )
        if case.status == "candidate-ui-calibration":
            if not case.calibration_question.strip():
                raise DesignError(
                    f"{case.tc_id} is a calibration candidate without a question"
                )
            lines.extend(
                [
                    "**Статус oracle:** ui-calibration-required",
                    "**Статус тест-кейса:** candidate-ui-calibration",
                    f"**Требуется подтверждение:** {case.calibration_question}",
                ]
            )
        lines.extend(
            [
                "",
                "### Предусловия",
                "",
                _numbered(case.preconditions),
                "",
                "### Тестовые данные",
                "",
                _bulleted(case.test_data),
                "",
                "### Шаги",
                "",
                _numbered(case.steps),
                "",
                "### Итоговый ожидаемый результат",
                "",
                case.expected_result,
                "",
                "### Постусловия",
                "",
                _bulleted(case.postconditions),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
