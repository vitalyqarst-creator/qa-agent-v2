from __future__ import annotations

import re
from collections.abc import Sequence


_PERSISTENCE_CLAIM_PATTERNS = (
    re.compile(
        r"\b(?:сохран(?:ён\w*|ен(?!и)\w*|я(?:ет|ют|ется|ются|тся)\w*|ится\w*)|"
        r"persist(?:ed|s|ing)?|saved)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:сохранени\w*[^.\n;]{0,60}"
        r"(?:блокиру\w*|запрещ\w*|невозмож\w*|"
        r"не\s+(?:выполня\w*|происход\w*|доступ\w*|разреш\w*))|"
        r"(?:значени\w*|данн\w*|выбор\w*)[^.\n;]{0,100}"
        r"(?:оста[её]тся|не\s+сбрасывается)[^.\n;]{0,100}\b(?:после|при)\s+"
        r"(?:повторн\w*\s+)?(?:открыт\w*|перезагруз\w*|возврат\w*|переход\w*)|"
        r"(?:значени\w*|данн\w*)[^.\n;]{0,100}\bпосле\s+"
        r"(?:повторн\w*\s+)?(?:открыт\w*|перезагруз\w*)|"
        r"после\s+(?:повторн\w*\s+)?(?:открыт\w*|перезагруз\w*)"
        r"[^.\n;]{0,100}\b(?:значени\w*|данн\w*)|"
        r"(?:после|при)\s+(?:повторн\w*\s+)?"
        r"(?:открыт\w*|перезагруз\w*|возврат\w*)[^.\n;]{0,160}"
        r"\b(?:пол\w*|элемент\w*|контрол\w*)\b[^.\n;]{0,100}"
        r"\b(?:отобража\w*|содерж\w*|присутств\w*|отсутств\w*|заполн\w*)\b|"
        r"(?:value|data|selection)[^.\n;]{0,100}\b(?:remains?|(?:is|was)\s+retained)\b"
        r"[^.\n;]{0,100}\bafter\s+(?:reopen|reload|refresh)|"
        r"(?:value|data|selection)[^.\n;]{0,100}\bnot\s+reset\b"
        r"[^.\n;]{0,100}\bafter\s+(?:reopen|reload|refresh)|"
        r"after\s+(?:reopen\w*|reload\w*|refresh\w*|return\w*)"
        r"[^.\n;]{0,160}\b(?:field|control|input)\b[^.\n;]{0,100}"
        r"\b(?:displays?|shows?|contains?|is\s+(?:present|absent|filled))\b)",
        re.IGNORECASE,
    ),
)

_LIFECYCLE_CONTEXT_RE = re.compile(
    r"\b(?:(?:после|при)\s+(?:повторн\w*\s+)?"
    r"(?:открыт\w*|перезагруз\w*|возврат\w*|закрыт\w*)|"
    r"after\s+(?:reopen\w*|reload\w*|refresh\w*|return\w*|clos\w*))\b",
    re.IGNORECASE,
)

_REPRESENTATION_RETENTION_RE = re.compile(
    r"\b(?:(?:символ\w*|дефис\w*|пробел\w*|регистр\b|формат\w*|маск\w*)"
    r"[^.\n;]{0,100}\bсохран\w*|"
    r"сохран\w*[^.\n;]{0,60}\b(?:символ\w*|дефис\w*|пробел\w*|"
    r"регистр\b|формат\w*|маск\w*)|"
    r"(?:character|hyphen|space|case|format|mask)[^.\n;]{0,100}\b"
    r"(?:saved|retained|preserved)|"
    r"(?:saved|retained|preserved)[^.\n;]{0,60}\b"
    r"(?:character|hyphen|space|case|format|mask))\b",
    re.IGNORECASE,
)

_QUOTED_FRAGMENT_RE = re.compile(
    r"`[^`\n]*`|«[^»\n]*»|\"[^\"\n]*\"|'[^'\n]*'"
)

_OBSERVATION_ACTION_RE = re.compile(
    r"^\s*(?:проверить|убедиться|сверить|зафиксировать|просмотреть|осмотреть|"
    r"verify|check|compare|record|inspect)\b",
    re.IGNORECASE,
)

_VALUE_MUTATION_RE = re.compile(
    r"\b(?:ввести|вводить|выбрать|установить|указать|задать|вставить|"
    r"заменить|изменить|очистить|заполнить|переключить|отметить|"
    r"добавить|прикрепить|загрузить|удалить|"
    r"оставить[^.\n;]{0,80}\bпуст\w*|"
    r"enter|type|choose|select|set|specify|paste|replace|change|clear|fill|"
    r"toggle|add|attach|upload|remove|delete|"
    r"leave[^.\n;]{0,80}\bempty)\b",
    re.IGNORECASE,
)

_ACTION_CLAUSE_PREFIX = (
    r"(?:^|[.;]\s*|\b(?:и|затем|далее|после\s+этого|then|and(?:\s+then)?)\s+)"
)

_COMMIT_OR_TRANSITION_RE = re.compile(
    _ACTION_CLAUSE_PREFIX
    + r"(?:сохранить\b|"
    r"(?:попытаться|попробовать)\s+сохранить\b|"
    r"выполнить\s+(?:подтверждени\w*|сохранени\w*)\s+"
    r"(?:форм\w*|заявк\w*|анкет\w*|карточк\w*|изменени\w*|данн\w*)|"
    r"нажать\s+(?:кнопку\s+)?(?:«сохранить»|\"сохранить\"|сохранить\b)|"
    r"подтвердить(?:\s+(?:изменени\w*|данн\w*|ввод\w*|форм\w*|"
    r"заявк\w*|анкет\w*|карточк\w*|значени\w*))|"
    r"нажать\s+(?:кнопку\s+)?(?:«(?:продолжить|далее|подтвердить)»|"
    r"\"(?:продолжить|далее|подтвердить)\")|"
    r"отправить\s+(?:форм\w*|заявк\w*|анкет\w*|изменени\w*|данн\w*)|"
    r"снять\s+фокус|перевести\s+фокус|потерять\s+фокус|"
    r"нажать\s+(?:клавишу\s+)?tab\b|кликнуть\s+вне\b|"
    r"повторно\s+открыть\s+(?:карточк\w*|форм\w*|заявк\w*|анкет\w*|"
    r"страниц\w*)|"
    r"перезагрузить\s+(?:карточк\w*|форм\w*|заявк\w*|анкет\w*|страниц\w*)|"
    r"save\b|(?:attempt|try)\s+to\s+save\b|"
    r"perform\s+(?:the\s+)?(?:form|application|changes|data)\s+confirmation\b|"
    r"click\s+(?:the\s+)?(?:save\s+button|save)\b|"
    r"click\s+(?:the\s+)?(?:continue|next|confirm|submit)\s+button\b|"
    r"submit\s+(?:the\s+)?(?:form|application|changes|data)\b|"
    r"confirm\s+(?:the\s+)?(?:changes|data|input|form|application|value)\b|"
    r"blur(?:\s+(?:the\s+)?(?:field|input|control))?\b|"
    r"press\s+tab\b|click\s+outside\b|"
    r"reopen\s+(?:the\s+)?(?:card|form|application|page)\b|"
    r"reload\s+(?:the\s+)?(?:card|form|application|page)\b|"
    r"refresh\s+(?:the\s+)?(?:card|form|application|page)\b)",
    re.IGNORECASE,
)

_PERSISTENCE_EVIDENCE_RE = re.compile(
    _ACTION_CLAUSE_PREFIX
    + r"(?:проверить|убедиться|сверить|зафиксировать)"
    r"[^.\n;]{0,120}(?:(?:запис\w*|сохран\w*|содерж\w*|связан\w*|"
    r"налич\w*)[^.\n;]{0,100}\b(?:архив\w*|хранилищ\w*)\b|"
    r"(?:архив\w*|хранилищ\w*)[^.\n;]{0,100}\b(?:запис\w*|сохран\w*|"
    r"содерж\w*|связан\w*|налич\w*)\b)|"
    + _ACTION_CLAUSE_PREFIX
    + r"(?:verify|check|compare|record)"
    r"[^.\n;]{0,120}(?:(?:record|entry|saved|stored|contains?|linked)"
    r"[^.\n;]{0,100}\b(?:archive|storage|repository)\b|"
    r"(?:archive|storage|repository)[^.\n;]{0,100}\b"
    r"(?:record|entry|saved|stored|contains?|linked)\b)",
    re.IGNORECASE,
)

_BACK_BOUNDARY_RE = re.compile(
    r"^\s*(?:(?:нажать|выбрать)\b[^.\n;]{0,50}(?:`назад`|«назад»|назад\b)|"
    r"(?:click|select)\b[^.\n;]{0,50}(?:`?back`?|back\s+button\b))",
    re.IGNORECASE,
)

_DIALOG_DECISION_RE = re.compile(
    r"^\s*(?:в\s+(?:уведомлени\w*|диалог\w*|подтверждени\w*)[^.\n;]{0,80}"
    r"(?:выбрать|нажать)[^.\n;]{0,40}(?:`да`|`нет`|«да»|«нет»|\bда\b|\bнет\b)|"
    r"in\s+(?:the\s+)?(?:notification|dialog|confirmation)[^.\n;]{0,80}"
    r"(?:select|click|choose)[^.\n;]{0,40}\b(?:yes|no)\b)",
    re.IGNORECASE,
)


def persistence_claim(value: str) -> str | None:
    """Return the first persistence-like result fragment, if any.

    The matcher intentionally excludes the infinitive ``Сохранить`` so a
    visibility oracle for a Save button is not treated as data persistence.
    """

    candidate = value
    if _LIFECYCLE_CONTEXT_RE.search(value) is None:
        candidate = _REPRESENTATION_RETENTION_RE.sub(" ", candidate)
    for pattern in _PERSISTENCE_CLAIM_PATTERNS:
        match = pattern.search(candidate)
        if match is not None:
            return match.group(0)
    return None


def has_commit_or_transition_after_mutation(
    actions: Sequence[str],
    *,
    mutation_already_occurred: bool = False,
    boundary_prompt_already_open: bool = False,
) -> bool:
    """Whether persistence evidence occurs after an explicit mutation.

    Setup performed before the tested mutation cannot prove the later value was
    committed. Ordering is checked inside a combined action as well as between
    actions. Narrow archive/storage observations are accepted as direct
    persistence evidence; generic confirmations and unrelated closes are not.
    """

    normalized = tuple(action.strip() for action in actions if action.strip())
    if not normalized:
        return False
    last_mutation: tuple[int, int] | None = (
        (-1, 0) if mutation_already_occurred else None
    )
    for index, action in enumerate(normalized):
        if _DIALOG_DECISION_RE.search(action) is not None:
            continue
        if _OBSERVATION_ACTION_RE.search(action) is not None:
            continue
        mutation_text = _QUOTED_FRAGMENT_RE.sub(
            lambda match: " " * len(match.group(0)), action
        )
        for match in _VALUE_MUTATION_RE.finditer(mutation_text):
            last_mutation = (index, match.end())
    if last_mutation is None:
        return False

    mutation_index, mutation_end = last_mutation
    boundary_prompt_seen = boundary_prompt_already_open
    start_index = max(mutation_index, 0)
    for index, action in enumerate(normalized[start_index:], start_index):
        if index > mutation_index and _BACK_BOUNDARY_RE.search(action) is not None:
            boundary_prompt_seen = True
        if (
            index > mutation_index
            and boundary_prompt_seen
            and _DIALOG_DECISION_RE.search(action) is not None
        ):
            return True
        for pattern in (_COMMIT_OR_TRANSITION_RE, _PERSISTENCE_EVIDENCE_RE):
            for match in pattern.finditer(action):
                if index > mutation_index or match.start() >= mutation_end:
                    return True
    return False


def split_action_contract(value: str) -> tuple[str, ...]:
    """Split the compiler's ordered action contract without parsing prose."""

    return tuple(
        item.strip()
        for item in re.split(r"(?:[;\n\r]+)", value)
        if item.strip()
    )


__all__ = [
    "has_commit_or_transition_after_mutation",
    "persistence_claim",
    "split_action_contract",
]
