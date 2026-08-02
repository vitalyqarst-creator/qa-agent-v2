# Coverage Class Catalog

This catalog defines the minimum practical coverage classes for ordinary FT
test-case writing. Use it with `practical_v0_7`.

The goal is better test-design coverage without returning to heavy production
routes, large obligation ledgers, benchmark runs, sharding, semantic bridge or
immutable runner loops.

## Activation rule

Apply a class group only when the current FT/support/source actually contains
the corresponding restriction, dependency or behavior.

Do not generate a Cartesian product across all fields. Decompose each
source-backed rule into representative classes, then map every class to one of:

- a concrete `TC-*`;
- `candidate-ui-calibration` when the obligation is clear but exact UI reaction
  is unknown;
- `blocked-observability` when the obligation cannot be observed in the current
  package;
- `needs-test-data` when execution needs a missing fixture.

One mixed invalid value must not claim coverage for several independently
derivable invalid classes.

## Input format / allowed symbols

### `digits-only` / numeric-symbol input

Use when the source says `только цифры`, `digits only`, numeric symbols only, or
equivalent.

Minimum classes:

- valid digits;
- Latin letters;
- Cyrillic letters;
- spaces;
- hyphen or sign;
- decimal separator;
- punctuation or special symbol.

### text-only / name-like input

Use when the source restricts a field to text characters, letters, person names,
organization names, or explicitly allows only letters plus selected separators.

Minimum classes:

- valid Cyrillic text when the FT is Russian-facing or examples are Cyrillic;
- valid allowed separator, for example hyphen, if the source allows it;
- digits;
- Latin letters when language is not explicitly allowed;
- spaces when the source does not explicitly allow spaces;
- dot/comma;
- punctuation or special symbol.

If the source explicitly allows Latin letters, spaces or punctuation, move that
class to positive coverage instead of negative coverage.

### alphanumeric input

Use when the source allows letters and digits but restricts other symbols.

Minimum classes:

- valid letters plus digits;
- valid letters only, if allowed;
- valid digits only, if allowed;
- spaces;
- hyphen/sign;
- decimal separator;
- punctuation or special symbol.

### mask / pattern

Use when the source defines a mask or pattern, for example phone, document
series/number, code or account-like pattern.

Minimum classes:

- valid value matching the mask;
- value with too few required characters;
- value with too many required characters;
- wrong character class inside the mask;
- separator mismatch only if separators are user-entered or source-significant.

## Length

### exact length `N`

Use when the source says exactly `N` characters/digits/symbols.

Minimum classes:

- `N`;
- `N-1`;
- `N+1`;
- empty value, if the field is required;
- invalid character inside an otherwise length-valid value, if format is also
  constrained.

### min/max length

Use when the source gives minimum and/or maximum length.

Minimum classes:

- minimum valid length;
- one less than minimum;
- maximum valid length;
- one more than maximum;
- representative value inside the range, when both bounds exist;
- empty value, if the field is required.

## Numeric ranges and amounts

Use when the source gives `не менее X`, `не больше Y`, numeric min/max, amount,
term, percent, count or similar range.

Minimum classes:

- `X` lower boundary;
- `X-1` below lower boundary, when lower boundary exists;
- `Y` upper boundary;
- `Y+1` above upper boundary, when upper boundary exists;
- representative value inside range, when both bounds exist;
- non-numeric value, if the field accepts keyboard input;
- empty value, if the field is required.

## Dates and date/time

Use when the source defines date format, current-date dependency, future/past
restriction or validity period.

Minimum classes:

- valid date in source format;
- current date when the rule depends on current date;
- current date minus one day, when past/current boundary matters;
- current date plus one day, when future/current boundary matters;
- minimum allowed date, when source defines it;
- maximum allowed date, when source defines it;
- invalid format;
- impossible calendar date, for example `31.02.<year>`;
- empty value, if the field is required.

Use dynamic formulas such as `current date + 1 day` when a stable literal would
become stale.

## Requiredness and conditional requiredness

Use when the source defines `О=Да/Нет`, required markers, conditional
requiredness or optional fields.

Minimum classes:

- required field empty with the triggering action/source-backed commit action;
- required field filled with valid value;
- optional field empty;
- optional field filled with valid value;
- for conditional requiredness: condition true and empty value;
- for conditional requiredness: condition false and empty value;
- for conditional visibility: both visible and hidden/not-applicable states when
  source-backed.

Do not invent error text. If the exact UI reaction is unknown, use
`candidate-ui-calibration` with a concrete trigger and value.

## Dictionaries, closed lists, autocomplete and integrations

Use when the source/support references a dictionary, fixed list, DaData, CBR/BIK
or another selectable/autocomplete source.

Minimum classes:

- valid value from the full relevant dictionary/list or a justified
  representative set;
- search by exact value, if search/autocomplete is source-backed;
- search by partial value, if search/autocomplete is source-backed;
- value outside the list only if closed-set behavior follows from source/support
  or UI evidence;
- no-result query only with a verified fixture or explicit source support;
- manual free text outside the list when the source says selection must come
  from the dictionary.

For DaData or similar integrations, use fixed verified fixtures with exact input
and exact expected suggestion/result. Do not ask the tester to make a live
service call during TC execution.

## File upload

Use when the source defines upload, file type, size or count rules.

Minimum classes:

- each allowed file type, or a justified representative set if the list is long;
- forbidden extension/type;
- file below size limit;
- file exactly on size limit, if a max size is defined;
- file above size limit;
- second file when only one file is allowed;
- delete/replace file only when the source describes or the UI calibration needs
  the behavior.

## Repeatable blocks and child rows

Use when the source allows adding/removing repeated rows, blocks, documents,
phones, addresses, contacts or child entities.

Minimum classes:

- add first row/block;
- add second independent row/block;
- fill required fields in an added row/block;
- delete one row when several exist;
- delete last row or record a narrow gap if empty-state behavior is not defined;
- boundary min/max count when the source defines count limits.

## Uniqueness and duplicate checks

Use when the source defines unique keys or duplicate prevention.

Minimum classes:

- create/save a unique valid object;
- duplicate on the exact source-backed key;
- same partial data but different key, if needed to prove the key boundary;
- duplicate across the stated container only, for example same partner, same
  application or global scope.

## Status and lifecycle

Use when the source defines statuses, transitions or allowed actions by status.

Minimum classes:

- each source-backed transition action;
- action allowed in the source-backed status;
- action unavailable/blocked in a source-backed status, when described;
- terminal/non-terminal boundary only when the source defines statuses or a
  future-source placeholder is explicitly accepted.

Do not create standalone tests for glossary/status-table rows when later FT
sections define the actual screen, action and expected result. Use those rows as
supporting source context.

## Cross-field dependencies and combinations

Use when one field/action changes requiredness, visibility, available values,
autofill or validation of another field.

Minimum classes:

- controlling condition true;
- controlling condition false;
- dependent field/action behavior under each condition;
- conflict/invalid combination only if the source describes it.

Prefer focused pairwise coverage for source-backed dependencies. Do not combine
unrelated fields merely to reduce TC count.

## Generated documents and mappings

Use when the source defines document generation, print forms, tags or field
mapping.

Minimum classes:

- source field/tag populated and rendered in output;
- optional/empty source field behavior, if defined;
- repeated rows rendered, if repeatable;
- formatting/transformation rule, if source-backed;
- missing template/source data only when the source defines an error behavior.

## Reviewer rule

Reviewer must block or return findings when:

- a source-backed restriction has no `coverage_classes` row;
- one invalid representative is used as proof for several independent classes;
- a candidate UI-calibration case omits the concrete representative value;
- a source-backed class disappears because exact UI reaction is unknown;
- a dictionary/list/integration rule uses examples instead of the relevant list
  or a fixture need;
- boundary classes are missing for exact length, min/max range, date/current-date
  or file size limits.
