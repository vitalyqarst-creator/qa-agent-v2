# Provenance кандидата v3 — 9.3.2 «Карточка партнёра»

Кандидат v3 — отдельная версия для сравнения с baseline v2. Он не заменяет
canonical test cases и не является самостоятельным новым practical handoff.

## Канонические входы scope

- `work/practical-v0.9/9.3.2-kartochka-partnera/workflow-state.json` —
  состояние исходного practical scope.
- `work/practical-v0.9/9.3.2-kartochka-partnera/scope-obligations.json` —
  source-backed обязательства и связанные coverage gaps.
- `work/practical-v0.9/9.3.2-kartochka-partnera/validator-report.json` —
  последняя проверка исходного scope.
- `work/practical-v0.9/9.3.2-kartochka-partnera/test-cases-v2-final-review-manifest.json`
  и `test-cases-v2-final-review-result.json` — receipt независимого review
  baseline v2.

## Изменения v3

- Матрица и тест-кейсы v3 находятся в этой папке и в
  `test-cases/candidates/`; baseline v2 не изменяется.
- Добавлены атомарные границы длины текстовых полей, одиночный выбор типа
  партнёра и частичные совпадения ключа дубликата `Наименование + ИНН` по
  `BA-DEC-003`.
- Для `OBL-046` источником перехода к существующей карточке является
  DOCX/XHTML, раздел 9.3, `AS.5`, пункт 1; это отдельное parent-level
  обязательство, а не вывод из Таблицы 7.
- Статусы, требующие подтверждения конкретного UI-контрола, установлены в
  `candidate-ui-calibration`; отсутствие внешних карточек, файлов или
  доступа остаётся `needs-test-data`.

## Граница выпуска

После положительного независимого review v3 остаётся проверенным кандидатом.
Для замены baseline потребуется отдельная формальная migration-процедура с
обновлением canonical workflow state; она не выполняется в этой итерации.
