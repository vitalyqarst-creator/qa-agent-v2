# Coverage Class Catalog

This catalog defines the minimum practical coverage classes for ordinary FT
test-case writing. Use it with `practical_v0_8`.

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

## Quick field-rule matrix

Use this table before writing `test-design-matrix.md`. It is the minimum
practical decomposition for the most common FT field rules. If a class applies
but exact UI reaction is unknown, keep the class and mark the planned TC as
`candidate-ui-calibration` or `blocked-observability`; do not remove it.

| Source rule | Minimum classes to represent in `test-design-matrix.md` |
| --- | --- |
| `только цифры` / digits-only | valid digits; Latin letters; Cyrillic letters; spaces; hyphen/plus/minus sign; dot/comma decimal separator; other special symbol; if length is defined: `N-1`/min-1, exact/min valid length, `N+1`/max+1 |
| text / only Cyrillic / letters-only / name-like field | valid Cyrillic text; allowed separator such as hyphen when source allows it; Latin letters when not allowed; digits; spaces when not allowed; apostrophe; dot/comma; other special symbol |
| dictionary / closed list / autocomplete / integration-backed selector | every source-listed value or a justified full relevant subset; empty value when required; exact-value search when applicable; partial search when applicable; invalid/free-text value when manual input is possible or closed-set behavior must be proven; no-result query only with verified fixture/evidence |
| date / date-time / current-date-dependent rule | valid date in source format; current date `D`; `D-1`; `D+1`; minimum boundary when defined; maximum boundary when defined; invalid format; impossible calendar date; empty value when required |
| required field | empty value with the source-backed trigger/commit action; filled valid value; split by input mechanism: typed field, dictionary/autocomplete selection, system-filled, dependent autofill, readonly, repeatable-row/action-created, conditional requiredness |
| create/add a new independent object, child record or row | create object A with distinctive user-entered values; invoke the same create action for object B; verify that B does not contain values entered for A; retain only source-defined defaults, context values, inheritance or autofill |

The quick matrix is intentionally not a Cartesian-product generator. Activate
only the classes that follow from the current source rule.

## Input format / allowed symbols

### `digits-only` / numeric-symbol input

Use when the source says `только цифры`, `digits only`, numeric symbols only, or
equivalent.

Minimum classes:

- valid digits;
- Latin letters;
- Cyrillic letters;
- spaces;
- hyphen or sign, including plus/minus sign;
- dot or comma decimal separator;
- punctuation or special symbol.

If the same field also has exact/min/max length, include the corresponding
length boundary classes for the same source row in the matrix.

### text-only / name-like input

Use when the source restricts a field to text characters, letters, person names,
organization names, or explicitly allows only letters plus selected separators.

Minimum classes:

- valid Cyrillic text when the FT is Russian-facing or examples are Cyrillic;
- valid allowed separator, for example hyphen, if the source allows it;
- digits;
- Latin letters when language is not explicitly allowed;
- spaces when the source does not explicitly allow spaces;
- apostrophe when it is not explicitly allowed;
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

First split requiredness by input mechanism. Do not create one generic
requiredness test case for all required fields unless every listed field has the
same source-backed input mechanism, the same trigger, and the same observable
oracle.

Minimum mechanism classes:

- user-entered required value: the tester types or pastes the value directly;
- dictionary/autocomplete required selection: the tester must select a value
  from a list, dictionary, DaData, BIK or similar source;
- system-filled required value: the application populates the value without
  direct user input;
- dependent autofilled required value: another user action or selected value
  fills the field;
- readonly required value: the field must be present/filled but cannot be edited
  directly;
- action-created/repeatable row required value: requiredness applies only after
  the user creates a child row/block;
- conditional requiredness or conditional visibility states.

For each applicable mechanism, cover these classes where source-backed:

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

If a test case lists several required fields in `Тестовые данные`, every listed
field must be exercised in the steps, or the title/scope of the case must be
narrowed. System-filled, autofilled and readonly fields must not be tested as
"leave manually empty" negatives unless the source or UI evidence defines a way
to make them empty.

## Dictionaries, closed lists, autocomplete and integrations

Use when the source/support references a dictionary, fixed list, DaData, CBR/BIK
or another selectable/autocomplete source.

Minimum classes:

- valid values from the full relevant dictionary/list, or a justified full
  relevant subset when the list is too large for one TC;
- empty value when the field is required;
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

Проверка лимита «один файл» относится к полю или типу документа, указанному в
источнике, а не к расширению второго файла. Для неё добавь второй валидный файл
в то же поле и наблюдай результат добавления; не подменяй это проверкой «второй
файл того же расширения», если такое ограничение не задано источником.

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

## Independent creation and form isolation (`R-CREATE-FORM-ISOLATION`)

Apply this class when a source-backed `Создать` / `Добавить` action opens a
form for a new independent object, child record or row. It is not a clone,
copy, import, inherited child or an explicitly persistent draft flow.

Minimum class:

- create object A with distinctive values in one or more editable fields;
- invoke the same creation action for object B;
- immediately verify the new form for B before any edit, focus-changing or
  save action;
- list the fields checked for leakage and verify that none contains the
  distinctive values entered for A.

The creation of A is setup for this check; the single main expected result is
the absence of leaked values in B. Do not require source-defined defaults,
context values, inherited values or documented autofill to be empty. If the
source explicitly defines copying, inheritance or persistent draft values,
cover that behavior instead and mark this class not applicable with the source
reason.

## Uniqueness and duplicate checks

Use when the source defines unique keys or duplicate prevention.

Minimum classes:

- create/save a unique valid object;
- duplicate on the exact source-backed key;
- same partial data but different key, if needed to prove the key boundary;
- duplicate across the stated container only, for example same partner, same
  application or global scope.

The duplicate class is negative by default. Do not model duplicate prevention as
a positive save/reopen TC. The expected result must use the source-backed
no-save, popup, validation, conflict or "duplicate is not created" oracle. A
unique-value save is a separate positive TC.

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

Separate business state from the observable result. A status such as
`Подтвержден` / `Скрыт`, `active` / `archived` or `approved` / `hidden` may be a
business state, while the UI may expose it through a color indicator, available
action, list presence, badge, API field or document output. The planned TC must
name the observable artifact it checks. Do not expect status text unless the
source/support/UI evidence confirms that the text is actually displayed.

## Downstream or future-stage obligations

Use when the source describes a rule whose pass/fail can be observed only in a
later FT, another module, an issuance/payment stage, an external system or a
future role/status model.

- Do not convert a downstream applicability rule into a current-screen
  save/validation rejection unless the source explicitly defines local
  enforcement.
- Cover only the observable current-scope part in executable TC.
- Put the downstream/use-stage part into a narrow `blocked-observability`,
  `needs-future-clarification`, `GAP-*` or `unclear` entry with the same source
  token.
- If the current screen only stores data later consumed elsewhere, the current
  TC may verify field presence, allowed input and save/reopen persistence, but
  not the later business decision.

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

- a source-backed restriction has no explicit coverage-class row in
  `test-design-matrix.md`;
- one invalid representative is used as proof for several independent classes;
- a requiredness check merges fields with different input mechanisms without a
  clear parameter table or separate `TC-*`;
- a requiredness test lists fields that are not actually exercised in steps;
- a system-filled, autofilled or readonly required field is tested as manually
  empty without source-backed setup that makes the empty state reachable;
- a candidate UI-calibration case omits the concrete representative value;
- a source-backed class disappears because exact UI reaction is unknown;
- a dictionary/list/integration rule uses examples instead of the relevant list
  or a fixture need;
- boundary classes are missing for exact length, min/max range, date/current-date
  or file size limits;
- a source-backed independent creation action has no form-isolation class, or
  the planned check omits its checked field list, delays the observation with
  an unrelated focus/edit action, or wrongly treats source-defined defaults,
  inheritance or autofill as leaked values.
- status/lifecycle coverage checks only an internal/business state label and
  does not name an observable UI/API/document artifact.
- TC объединяет создание и редактирование, либо другой набор вариантов с
  разными объектами, UI-уровнями или входными действиями.
- TC заявляет очистку/изменение системно заполненного или автозаполненного
  поля, но источник или UI evidence не задаёт способ достигнуть этого
  состояния.
- TC, который создаёт, изменяет, архивирует, привязывает или сохраняет объект,
  заканчивается нажатием команды без последующей проверки наблюдаемого
  результата в корректном месте (после повторного открытия, возврата в список,
  перехода или иного source-backed наблюдения).
- file-count TC проверяет только одинаковое расширение второго файла вместо
  ограничения количества файлов в source-defined поле/типе документа.
