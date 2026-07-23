from __future__ import annotations

import re
from dataclasses import dataclass


_EXACT_NUMERIC_SYMBOL_RESTRICTION = re.compile(
    r"(?:(?:ограничени[ея]\s+на\s+формат|формат(?:а|е)?\s+значени[ея])"
    r"\s*:\s*)?(?:только|ровно)\s+(?P<length>[1-9][0-9]*)\s+"
    r"(?:числов(?:ых|ого)\s+символ(?:ов|а)|цифр(?:ы|а|у)?)\b",
    re.IGNORECASE,
)
_TEXT_WITH_HYPHEN_RESTRICTION = re.compile(
    r"(?:возможен\s+ввод\s+)?только\s+текстовых\s+символов\s+и\s+"
    r"(?:специальн(?:ый|ого)\s+символ\s+)?[«\"'`](?P<hyphen>[-‐‑‒–—])"
    r"[»\"'`]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RestrictedSymbolClass:
    start: int
    end: int
    restriction_type: str
    literal_anchor: str
    negative_class: str
    representative_invalid_value: str


def _digit_value(length: int) -> str:
    sequence = "1234567890"
    return "".join(sequence[index % len(sequence)] for index in range(length))


def _replace_at(value: str, index: int, replacement: str) -> str:
    return value[:index] + replacement + value[index + 1 :]


def restricted_symbol_classes(source_text: str) -> tuple[RestrictedSymbolClass, ...]:
    """Return only mechanically proven classes outside an explicit allowed set.

    The function does not infer a UI rejection mechanism.  Exact numeric length
    proves both non-empty N-1/N+1 length classes and the standard non-digit
    classes.  Character-class representatives keep the declared length so they
    remain distinct from the boundary checks.  The downstream design may keep
    the observable UI reaction as calibration-pending.
    """

    if not isinstance(source_text, str):
        raise TypeError("source_text must be a string")
    result: list[RestrictedSymbolClass] = []
    for match in _EXACT_NUMERIC_SYMBOL_RESTRICTION.finditer(source_text):
        length = int(match.group("length"))
        valid = _digit_value(length)
        middle = length // 2
        representatives: tuple[tuple[str, str], ...] = (
            *(
                (("length-n-minus-one", _digit_value(length - 1)),)
                if length > 1
                else ()
            ),
            ("length-n-plus-one", _digit_value(length + 1)),
            ("letters", _replace_at(valid, middle, "A")),
            ("spaces", _replace_at(valid, middle, " ")),
            ("special-characters", _replace_at(valid, middle, "@")),
            ("decimal-separator", _replace_at(valid, middle, ".")),
            ("sign", _replace_at(valid, middle, "-")),
        )
        for negative_class, representative in representatives:
            result.append(
                RestrictedSymbolClass(
                    start=match.start(),
                    end=match.end(),
                    restriction_type="numeric",
                    literal_anchor=match.group(0),
                    negative_class=negative_class,
                    representative_invalid_value=representative,
                )
            )
    for match in _TEXT_WITH_HYPHEN_RESTRICTION.finditer(source_text):
        for negative_class, representative in (
            ("digits", "Иванов1"),
            ("special-characters-other-than-hyphen", "Иванов@"),
        ):
            result.append(
                RestrictedSymbolClass(
                    start=match.start(),
                    end=match.end(),
                    restriction_type="format",
                    literal_anchor=match.group(0),
                    negative_class=negative_class,
                    representative_invalid_value=representative,
                )
            )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.start,
                item.end,
            ),
        )
    )
