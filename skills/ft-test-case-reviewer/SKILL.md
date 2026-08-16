---
name: ft-test-case-reviewer
description: Независимо ревьюировать matrix или тест-кейсы по ФТ: покрытие, атомарность, трассировка, исполнимость и качество формулировок.
---

# FT Test Case Reviewer

Используй для отдельного review matrix или существующих тест-кейсов. Для
practical v1 reviewer работает в отдельной верхнеуровневой Codex-сессии, а не
в writer-сессии и не как subagent.

Перед review прочитай [practical route v1](../../references/agent/practical-test-case-route-v1.md),
[rubric test design](../../references/qa/test-design-review-rubric.md) и
[runtime format TC](../../references/qa/test-case-runtime-format.md).

## Входы

- DOCX/XHTML/PDF, релевантные support, решения БА и visual inputs;
- `source-scope.md` и `scope-clarification-requests.md`;
- matrix или набор TC в зависимости от режима.

## Выходы

- `matrix-review.md` с `matrix-accepted` или `matrix-changes-required`;
- либо `test-cases-review.md` с `tc-accepted` или `tc-changes-required`;
- ID отдельной reviewer-сессии, нумерованные findings и короткий итог.

## Режимы

- `matrix` — до написания TC: покрытие, атомарность, техники, классы данных,
  дубли и вопросы БА;
- `test-cases` — после matrix acceptance: соответствие matrix, трассировка,
  исполнимость, данные, oracle и смысловые дубли;
- `full` — review уже существующего набора вне practical v1.

## Последовательность

1. Используй source locator из `source-scope.md` как навигацию и независимо
   проверь каждое релевантное требование в DOCX/XHTML вместе с применимыми
   глобальными правилами типа данных. Не считай matrix или TC доказательством
   требования и не перечитывай весь пакет без cross-reference или признака
   противоречия. ID текущей reviewer-сессии должен быть передан в задаче;
   не ищи другие Codex-задачи и не собирай их историю.
2. Для matrix проверь, что каждое независимое утверждение ФТ и каждый код из
   `source-scope.md` покрыт строкой или явным gap, а одинаковые действия и
   результаты не раздроблены или не продублированы. Для применимых ограничений
   проверь граничные и контекстные классы; для create/edit/save/cancel/close —
   самостоятельные outcomes разных entry-state. Проверь, что у каждого
   `BAQ-*` есть поля `Статус`, `Ответ БА` и `Решение для тест-дизайна`;
   отсутствие ответа не блокирует однозначные matrix-строки. Для релевантной
   Figma-записи проверь, что указан завершённый итог visual-check, а не
   `not_checked`; известный `node-id` необязателен. Подтверждённые Figma
   подписи и расположение могут конкретизировать UI-шаги, но не бизнес-правила.
3. Для TC проверь соответствие принятой matrix, конкретность тестовых данных,
   единственность primary oracle, no-save oracle, классы негативных данных и
   прямую связь каждого покрытого matrix-кода с трассировкой TC. Коды без TC
   допустимы только как точные `GAP-*`.
4. Сформулируй один finding на первопричину, с source/artifact ref и точным
   исправлением. Не создавай новых design artifacts и не исправляй writer.
5. После одной writer revision проверяй только исходные findings и связанные
   с ними регрессии. Допускается один `micro-closure` уже найденной локальной
   неточности по условиям practical route v1; укажи точную замену и проверь
   только её. Если появляется новый или сохраняется существенный finding,
   зафиксируй `review-failed`; не запускай новую итерацию.

## Ограничения

- Не выдумывай роли, UI-реакции, тестовые данные и поведение системы.
- Не заменяй independent review subagent-ом, совместной сессией или
  самоаттестацией.
- Не создавай manifests, snapshots, controller receipts, workflow state или
  бесконечные repair-loop.
