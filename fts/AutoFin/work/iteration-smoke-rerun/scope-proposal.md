# Scope Proposal

- FT package: `fts/AutoFin`
- Main FT: `source/FT4AutoFinFinal.docx`
- Mandatory machine-readable source: `source/FT4AutoFinFinal.xhtml`
- PDF cross-check: `source/FT4AutoFinFinal.pdf`
- Proposed scope slug: `iteration-smoke-search-clear-context`
- Section: `4.2. Меню «Заявки в системе»`
- Source anchor: action table row for button `«Очистить»`
- Requirement id: `BSR 32`

## Proposed Scope

Проверить действие кнопки `«Очистить»` в меню `«Заявки в системе»`: при нажатии система очищает контекст поиска.

In scope:

- button label `«Очистить»`;
- business need `Очистить контекст поиска`;
- action `Нажатие`;
- expected system behavior from `BSR 32`: clears filters, sorting, pagination and row-selection state.

Out of scope:

- search execution through `«Найти»` / `BSR 31`;
- row information button `«i»` / `BSR 33`, `BSR 34`;
- `«Продолжить»`, `«Создать заявку»`, calculator and application opening actions;
- exact default sort/page-size values unless they are observable as the initial UI state during execution.

## Selection Rationale

This scope is small enough for a process smoke rerun, has one direct requirement id, is sourced from `FT4AutoFinFinal` rather than prior generated artifacts, and is unrelated to the prior section 3 widget-selection smoke or persistence-calibration scopes.

## Process Intent

Use the session-based runner workflow. Do not create a manual final test-case artifact. If the live SDK cannot run or cannot advance the cycle, record the terminal blocker and leave production test cases unsigned.
