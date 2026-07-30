# Manual review remediation — 13-4.3-employment-info

Дата: 2026-07-30.

## Результат

- Исправлен canonical файл `fts/AutoFin/PostFinal-v2-rc5/test-cases/13-4.3-employment-info.md`.
- Количество тест-кейсов сохранено: `83`.
- Добавлен человекочитаемый статус автоматизации:
  - `confirmed`: `32`;
  - `blocked-observability`: `51`.
- Внутренние lifecycle-маркеры `candidate-ui-calibration` сохранены для gate-совместимости.

## Что исправлено

- Удалены служебные placeholders `TEST-VALUE-1`.
- Убраны английские runtime-формулировки из названий, шагов и ожидаемых результатов.
- Убраны старые source-rule/oracle smell-формулировки вида `Требование BSR N:` в runtime-тексте.
- Убраны BSR/ATOM/SRC/OBL/ASSERT/SO-CAL из поля `Название`; трассировка сохранена только в `Трассировка`.
- Тест-кейсы переписаны вручную в едином UI-ready стиле: конкретные данные, action-oriented предусловия и шаги, без generic source projection.
- Candidate-кейсы получили честную пометку `blocked-observability`.
- Вопросы к UI-калибровке переписаны в вид, пригодный для агента на стенде.
- Исправлены наиболее рискованные группы:
  - `TC-EMP-046/047` — рабочий телефон;
  - `TC-EMP-052–057` — ограничения загрузки документов;
  - `TC-EMP-067/068` — нечисловой доход;
  - `TC-EMP-006–008/063` — удаление/повторители;
  - `TC-EMP-028/030/049/060` — Госуслуги, просмотр/удаление документа, архив.

## Проверки

- `production-tc-runtime-gate-v2`: passed.
- `test_case_count`: `83`.
- `execution_ready_count`: `32`.
- `calibration_candidate_count`: `51`.
- `suite_readiness`: `ft-first-reviewed-with-calibration-pending`.
- `findings`: `0`.
- `py_compile`: passed.
- `git diff --check`: passed.
- Smell-grep по `TEST-VALUE`, английским runtime-фрагментам и старым source-rule oracle: `0`.

## Остаточный статус

Файл не является `signed-off production release`: финальный independent reviewer не запускался, а 51 кейс требует UI-калибровки/наблюдаемости. Файл пригоден как controlled FT-first baseline для передачи автоматизатору с явными статусами.
