---
name: ft-test-case-reviewer
description: Независимо проверяет matrix или canonical тест-кейсы.
---

# FT Test Case Reviewer

Review выполняется только в отдельной верхнеуровневой Codex-сессии. Итог сохрани в `work/reviews/<scope>/<matrix|tc>-review.md`: ссылка/идентификатор сессии, verdict и конечный список findings. Не создавай attestation, immutable snapshot, dispatch receipt или технический transcript.

## Matrix review

Сверь matrix заново с DOCX/XHTML/PDF, `scope-brief.md`, questions и `fixture-catalog.json`.

Блокируй matrix, если:

- пропущена обязанность или context dimension;
- как TC запланирована обязанность без fixture или наблюдаемого oracle;
- один клик/выбор разбит на однотипные TC без отдельной бизнес-логики;
- разные невалидные классы с разным риском ошибочно слиты;
- в user-facing matrix остался английский process text.

Вердикт: только `matrix-accepted` или `matrix-changes-required` с конечным списком findings.

## TC review

Проверь canonical TC по matrix, источникам и fixture catalog. Обязательно блокируй:

- process IDs и `GAP-*` вне `Трассировка`;
- неконкретные тестовые данные;
- описание источника вместо значения («фиксированный запрос», «организация из снимка», «ожидаемые реквизиты»);
- интеграционное значение, не совпадающее с сохранённой fixture;
- требование получить fixture в TC;
- действие тестировщика, дублирующееся между предусловиями и шагами;
- подготовительное действие, которое выдаёт промежуточный результат за факт;
- `needs-test-data`, `candidate-ui-calibration` или `blocked-observability` в финальном runtime TC;
- неисполняемый expected result или лишнее объединение независимых проверок.

Вердикт: только `tc-accepted` или `tc-changes-required`. Принимать набор с waiver нельзя.
