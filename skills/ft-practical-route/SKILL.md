---
name: ft-practical-route
description: Основной компактный маршрут для выпуска трассируемых и исполнимых тест-кейсов по подтверждённому scope ФТ. Используй для обычной задачи написать тест-кейсы по ФТ или его разделу.
---

# Practical route v0.9

Используй только для нового обычного scope. Предыдущие practical-маршруты не
продолжаются и не являются fallback.

До работы прочитай [канонический маршрут](../../references/agent/practical-test-case-route-v0.9.md).
При создании obligations/workflow дополнительно прочитай
[формат обязательств](../../references/agent/practical-v0.9-scope-obligations-format.md)
и [формат workflow state](../../references/agent/practical-v0.9-workflow-state-format.md).
Перед dispatch, triage или finalization независимого review прочитай
[формат результата review](../../references/agent/practical-v0.9-review-result-format.md).
Для create/save, duplicate rule или provider-backed selection дополнительно
прочитай [формат fixture catalog](../../references/agent/fixture-catalog-format.md).

## Входы

- подтверждённый FT-пакет и выбранный scope;
- DOCX и matching XHTML основного ФТ, доступный PDF, support и visual inputs;
- package-specific `AGENT-NOTES.md`, если он есть;
- утверждённые решения БА, если они уже помещены в пакет.

## Выходы

В scope остаются только source manifest, `scope-obligations.json`, всегда
создаваемый `scope-clarification-requests.md`, `workflow-state.json`, matrix,
canonical TC, scoped validator report и immutable артефакты review. Все
человекочитаемые поля — на русском.

## Последовательность

1. Зафиксируй DOCX/XHTML, доступный PDF, support, package-level решения БА,
   `AGENT-NOTES.md` и visual inputs в source manifest.
2. Нормализуй независимые source-backed `OBL-*`, `CTX-*` с явным `flow_kind`
   и `SETUP-*`; проверь ФТ figures/PDF/Figma как visual evidence, не как
   источник бизнес-правил. Создай или сохрани файл вопросов БА.
3. Создай workflow и русскоязычную matrix; прогони scoped validator.
4. Проведи обязательный independent matrix review в отдельной верхнеуровневой
   Codex-сессии. Controller создаёт immutable manifest, записывает
   controller-owned session attestation с фактическим reviewer thread ID и
   ждёт raw verdict. Этап review нельзя завершать по одному факту dispatch:
   сначала захвати raw result, затем выполни triage/finalization.
5. Только после approved matrix напиши canonical TC, снова проверь scope и
   проведи independent final TC review тем же способом.
6. Для каждой фазы разрешена одна содержательная writer-доработка и ровно один
   fresh re-review. Повторный `changes-required` блокирует scope; не запускай
   новый repair-loop без явного решения пользователя.

## Ограничения

- Не создавай benchmark, sharding, semantic bridge, source assertion review,
  self-check, WQG, stage summary, dispatch receipt или дубли coverage state.
- Matrix review и TC review нельзя заменить subagent-ом, совместной сессией или
  самозаявленным reviewer receipt.
- Не выдумывай UI, данные, роли или поведение. Неясность — GAP/вопрос БА либо
  честный execution status; source contradiction — blocker.
- Не помещай в canonical TC URL, маршрут входа, логины, пароли, токены,
  конкретные учётные записи и `SETUP-*`.
