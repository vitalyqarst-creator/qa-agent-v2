# Scope Execution Options

## Контекст

- Scope: `application-card-calculator-summary-entrypoints`
- Source: `FT4AutoFinFinal` DOCX/XHTML/PDF.
- Gap status: один non-blocking `GAP-001`.

## Recommended Route

1. Запустить `ft-test-case-reviewer` в режиме `scope_gap_review`.
2. При passed verdict перевести workflow в `scope-gap-review-passed` / `scope-ready-for-writer`.
3. Скомпилировать новый prepared-standard package из Final-source handoff.
4. Запустить независимые writer/reviewer sessions без production promotion.

## Alternative Routes

- `blocked-input`: только если reviewer обнаружит противоречие источников или неправильную классификацию gap.
- `ft-source-locator`: только если исчезнет или изменится выбранное семейство Final источников.

## Запреты

- Не запускать writer до passed gap review.
- Не использовать handoff 05 или PreFinal как активное requirement evidence.
- Не продвигать candidate draft в production в этой итерации.
