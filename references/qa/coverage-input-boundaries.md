# Coverage Input Boundaries

Deep coverage reference for numeric, date/time, length, mask and allowed-symbol constraints. Use it only when the confirmed scope contains these dimensions or when reviewer/validator reports a missed boundary/input class.

## Numeric And Amount Inputs

- Test valid representative value.
- Test exact min and exact max when source defines boundaries.
- Test min-1 / max+1 or equivalent off-boundary rejection when source defines rejection behavior.
- Test decimal separator, sign, spaces, letters and special characters only when source wording supports those classes.
- Do not invent rounding, precision or formatting rules.
- When source says numeric-only / digits-only, create separate obligations for valid digits, letters, spaces, special characters, decimal separator and sign; one mixed value such as `12A00` is not enough.

## Length And Mask

- For exact length, create separate `N`, `N-1` and `N+1` coverage classes. When the source defines only the allowed length but not the exact UI response for `N-1`/`N+1`, keep those two classes as neutral `candidate-ui-calibration` obligations or as two narrow class-specific `GAP-*`; do not invent filtering, a message, clearing, persistence or transition behavior.
- For max length, test max acceptance and max+1 behavior.
- For mask, test visible field state, not navigation, unless source defines validation on action.
- If trim, multi-byte characters, newline handling or counting rule is missing, create `GAP-*`.
- Exact length requires separate `N`, `N-1` and `N+1` obligations or narrow class-specific `GAP-*`; one generic invalid-length assertion or gap cannot stand for both shorter and longer values.

## Date And Time

- Test valid date in range.
- Test exact lower and upper boundaries when source defines them.
- Test outside-window dates only with source-backed expected behavior.
- If current date, timezone, business calendar or boundary inclusivity is undefined, create `GAP-*`.

## Allowed Symbols

- Split independently checkable classes when source says `only ...`.
- Do not collapse all invalid symbols into one generic TC if classes are source-derivable.
- Use concrete values in TC test data, not placeholders like `invalid value`.
