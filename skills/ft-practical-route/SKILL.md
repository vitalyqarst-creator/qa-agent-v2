---
name: ft-practical-route
description: Основной компактный маршрут для выпуска трассируемых и исполнимых тест-кейсов по подтверждённому scope ФТ. Используй для обычной задачи написать тест-кейсы по ФТ или его разделу.
---

# Practical route v1

Используй для нового обычного scope. До работы прочитай
[канонический маршрут](../../references/agent/practical-test-case-route-v1.md)
и применимый [runtime-формат тест-кейса](../../references/qa/test-case-runtime-format.md).
`practical-v0.9` допускается только для уже начатого v0.9 scope по прямому
указанию пользователя; для такого legacy scope дополнительно прочитай
[формат реестра решений БА v0.9](../../references/agent/practical-v0.9-ba-decision-registry-format.md).

## Входы

- подтверждённый FT-пакет и выбранный scope;
- DOCX и matching XHTML основного ФТ, доступные PDF, support и visual inputs;
- package-specific `AGENT-NOTES.md`, если он есть;
- утверждённые решения БА, если они уже помещены в пакет.

## Выходы

В scope остаются только `source-scope.md`, всегда создаваемый
`scope-clarification-requests.md`, matrix и краткие результаты двух review.
Тест-кейсы создаются по обычному пути `test-cases/` и до принятия помечены как
draft. Все человекочитаемые поля — на русском.

## Последовательность

1. Зафиксируй scope, источники, решения БА и visual bindings в `source-scope.md`.
2. Всегда создай или сохрани файл вопросов БА; не задерживай им работу с
   однозначными требованиями.
3. Создай русскоязычную matrix и выполни self-check покрытия/атомарности.
4. Проведи independent matrix review в отдельной верхнеуровневой Codex-сессии.
   При замечаниях исправь matrix одним пакетом и получи краткое подтверждение
   закрытия findings.
5. Только по принятой matrix напиши видимые draft TC.
6. Проведи independent TC review в отдельной верхнеуровневой Codex-сессии.
   При замечаниях исправь TC одним пакетом и получи краткое подтверждение
   закрытия findings. Второй отказ даёт `review-failed`, а не новый цикл.

## Ограничения

- Не создавай benchmark, sharding, semantic bridge, source assertion review,
  immutable manifest, attestation, dispatch receipt, workflow state или
  дубли coverage state.
- Matrix review и TC review нельзя заменить subagent-ом или совместной сессией.
- Не выдумывай UI, данные, роли или поведение. Неясность — GAP/вопрос БА либо
  честный execution status; source contradiction — blocker.
- Не помещай в TC URL, маршрут входа, логины, пароли, токены, конкретные
  учётные записи и внутренние setup-идентификаторы.
