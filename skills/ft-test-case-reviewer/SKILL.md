---
name: ft-test-case-reviewer
description: Независимо проверяет matrix или canonical тест-кейсы.
---

# FT Test Case Reviewer

До review прочитай `AGENTS.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-profiles.md`, `references/runtime/test-design-matrix.md`, `references/runtime/test-case-runtime.md` и `references/runtime/review-record.md`.

Review выполняется только в отдельной верхнеуровневой Codex-сессии. Итог сохрани в `work/reviews/<scope>/<matrix|tc>-review.md`: ссылка/идентификатор сессии, verdict и конечный список findings. Рядом создай `<matrix|tc>-review.json`, связанный с SHA-256 проверенного artifact, и проверь его `scripts/validate_runtime_review.py`. Не создавай attestation, immutable snapshot, dispatch receipt или технический transcript.

## Matrix review

Сверь matrix заново с DOCX/XHTML/PDF, `scope-brief.md`, questions и `fixture-catalog.json`.

Блокируй matrix, если:

- пропущена обязанность или context dimension;
- потерян код требования или строка источника; ссылка только на таблицу не заменяет существующий буквенно-цифровой код;
- как TC запланирована обязанность без fixture или наблюдаемого oracle;
- один клик/выбор разбит на однотипные TC без отдельной бизнес-логики;
- разные невалидные классы с разным риском ошибочно слиты;
- пропущен применимый универсальный профиль, обязательное поле или source-backed роль;
- дублирующие строки имеют одну сигнатуру и отличаются только эквивалентным параметром;
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
- `needs-test-data` или `blocked-observability` в финальном runtime TC;
- `candidate-ui-calibration`, который не соответствует узкой политике из `test-design-profiles.md`;
- неисполняемый expected result или лишнее объединение независимых проверок.

Также проверь повторяющиеся ключи данных, корректность параметризации, сквозную нумерацию, группировку по функциональности и дубли по сигнатуре проверки. Вердикт: только `tc-accepted` или `tc-changes-required`. Принимать набор с material waiver нельзя.
