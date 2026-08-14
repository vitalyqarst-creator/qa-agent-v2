---
name: ft-scope-analyzer
description: Выделять внешние scope ФТ, подтверждать границы выбранного scope и фиксировать source-backed coverage gaps до test design.
---

# FT Scope Analyzer

Используй после выбора FT package, когда пользователю нужно выбрать или
подтвердить раздел/подраздел для дальнейшей работы. Для обычного выпуска
тест-кейсов этот skill выполняет только source/scope часть practical v0.9;
matrix и TC здесь не создаются.

Прочитай [scope decomposition policy](../../references/agent/scope-decomposition-policy.md),
[формат обязательств и gaps practical v0.9](../../references/agent/practical-v0.9-scope-obligations-format.md),
[source parity](../../references/agent/source-parity-check-format.md) и для
practical v0.9 [канонический маршрут](../../references/agent/practical-test-case-route-v0.9.md).

## Входы

- выбранный FT-пакет с DOCX/XHTML и доступным PDF;
- подтверждённый внешний scope или запрос на его выбор;
- package-specific notes, support и visual inputs в пределах FT-пакета.

## Выходы

- `scope-obligations.json` с независимыми source-backed `OBL-*`, `CTX-*` с
  `flow_kind` и нужными `SETUP-*`;
- `scope-clarification-requests.md`, в том числе с явной отметкой об
  отсутствии вопросов БА;
- `workflow-state.json`, созданный штатным init script;
- при наличии PDF — `source-parity-check.md`; при закрытом справочнике —
  полный `dictionary-inventory.md`.

## Правила

1. Сначала восстанови границы по DOCX/XHTML; PDF используй только для
   structural/visual cross-check. Макеты/Figma уточняют видимый контрол, но
   не меняют бизнес-правило. При наличии visual input заполни
   `visual_evidence_check` и `visual_binding` для подтверждённых UI-деталей.
   Figma — необязательный источник: отсутствие доступа к нему не является
   `blocked-input`; зафиксируй это в `visual_evidence_check` и продолжи по
   ФТ и локальным макетам.
2. Разделяй внешний scope по разделам ФТ. Не создавай внутренние work package
   ради размера текста.
   Если scope ещё не выбран пользователем, создай только
   `work/practical-v0.9/scope-selection/scope-options.md` и
   `work/practical-v0.9/scope-selection/scope-selection-prompts.md`. Это
   package-level карта выбора, а не legacy handoff: не создавай
   legacy numbered handoff tree.
3. Сохраняй один `OBL-*` на независимое утверждение ФТ и один основной
   наблюдаемый результат. Разные объекты, роли, lifecycle flow, классы
   значений и результаты разделяй; одинаковые значения одного контрола с
   одной реакцией можно параметризовать позднее.
4. Всегда проверь DOCX/XHTML/PDF/support до вопроса БА. Вопросы БА относятся
   только к реальной неоднозначности бизнес-правила; данные, роли, fixtures
   и runtime UI oracle фиксируй как setup/status, а не придумывай.
   Расхождение терминов источников фиксируй как
   `source-terminology-discrepancy` с цитатами обоих источников.
5. Package-level утверждённое решение БА имеет приоритет в своей явно заданной
   области. Сохрани его связь с GAP/OBL; при противоречии без решения создай
   `CLR-*`.
6. До matrix разрешён только `validate_practical_obligations.py`; не называй
   его полной валидацией scope.
   До запуска штатного init script сначала создай обязательные scope-local
   `source-parity-check.md` и `dictionary-inventory.md`, если они применимы.
   Init script сам связывает их из `workflow-state.json` и останавливается,
   если обязательный artifact отсутствует. После появления state не подменяй
   его новым: metadata-only обновление меняет только ссылки на уже созданные
   scope-local artifacts, не OBL, gaps, статусы или phase.
7. Когда собраны строки источников, parity и применимые справочники, оформи
   все scope-артефакты одним ограниченным проходом и заверши этап. Не
   возвращайся к повторному извлечению тех же источников и не создавай
   экспериментальные helpers: отсутствующие факты фиксируй как `GAP-*`.

## Ограничения

Не создавай matrix, TC, reviewer receipt, source assertion review, benchmark,
sharding, semantic bridge или temporary debug artifacts для normal practical
route. Не используй прежние practical маршруты как fallback.
