---
name: ft-test-case-reviewer
description: Независимо проверяет matrix или canonical тест-кейсы.
---

# FT Test Case Reviewer

До review прочитай `AGENTS.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-profiles.md`, `references/runtime/test-design-matrix.md`, `references/runtime/test-case-runtime.md` и `references/runtime/review-record.md`.

Review выполняется только в отдельной верхнеуровневой Codex-сессии. Итог сохрани в `work/reviews/<scope>/<matrix|tc>-review.md`: ссылка/идентификатор сессии, verdict и конечный список findings. Рядом создай `<matrix|tc>-review.json`, связанный с SHA-256 проверенного artifact, и проверь его `scripts/validate_runtime_review.py`. Не создавай attestation, immutable snapshot, dispatch receipt или технический transcript.

Начинай review только после operational prompt controller-а с путём dispatch receipt. Первым действием проверь receipt командой `scripts/runtime_review_dispatch.py verify` из `review-record.md`. Если receipt отсутствует, stale, относится к другому artifact/prompt/thread или не требует `codex-thread`, остановись без чтения review inputs и без verdict. Reviewer не создаёт и не заменяет dispatch receipt.

## Matrix review

До содержательного review заново запусти matrix-validator с `--source-inventory` и `--coverage-gaps`; неполная проекция блокирует review.

Сверь matrix заново с DOCX/XHTML/PDF, `scope-brief.md`, questions и `fixture-catalog.json`.

До оценки строк matrix проверь входной inventory: один `SR-*` должен соответствовать одной обязанности, все действия из таблиц должны содержать ссылку на таблицу и точный текст существующей строки первого столбца XHTML, а отменённые утверждённым ответом требования должны находиться в разделе применённых исключений и отсутствовать среди активных `SR-*`. Соседний абзац и элемент примечания не должны быть выданы за строку таблицы. Убедись, что visual cross-check охватывает каждый включённый UI-уровень и каждый локальный путь дословно совпадает с зарегистрированным source locator-ом существующим файлом.

Каждый `GAP-*` должен ссылаться ровно на одну атомарную `SR-*` и переносить эту же связь в отдельную строку matrix с решением `coverage-gap`. Общий вопрос БА может закрывать несколько GAP, но разные объекты, UI-уровни и обязанности не объединяются в один пробел покрытия.

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

До содержательного review заново запусти TC-validator с `--matrix`; неполная проекция принятой матрицы блокирует review.

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
