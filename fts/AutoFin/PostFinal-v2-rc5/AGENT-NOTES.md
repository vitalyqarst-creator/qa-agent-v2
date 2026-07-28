# PostFinal-v2-rc5 — package notes

Этот пакет предназначен для UI-калибровки уже написанных FT-first тест-кейсов по `PostFinal-v2-rc5`.

## Границы пакета

- В пакет включены только test-case markdown-файлы и материалы для UI-калибровки.
- Исходные `DOCX` / `XHTML` / `PDF`, support-файлы и макеты намеренно не включены.
- Нельзя запускать новый source analysis, writer, reviewer, bridge, benchmark или sharding, если пользователь прямо не дал отдельное задание и не предоставил исходные ФТ/source/support/mockup inputs.

## Основной сценарий

Используй этот пакет для прохождения кейсов со статусом `candidate-ui-calibration` на стенде:

1. Открой `work/ui-calibration-prep/UI-AGENT-NOTES.md`.
2. Открой `work/ui-calibration-prep/ui-calibration-index.md`.
3. Работай только с перечисленными calibration-кейсами.
4. Фиксируй фактическое поведение в `work/ui-calibration-prep/results/`.
5. Не изменяй файлы в `test-cases/` напрямую.

## Что считать результатом

Результат UI-калибровки — это не переписанный canonical файл, а evidence/report:

- какие кейсы прошли;
- какое фактическое UI-поведение увидели;
- какой trigger запускает проверку;
- какой exact message / marker / filtering / blocking / save effect отображается;
- какие кейсы остались не проверены и почему.

