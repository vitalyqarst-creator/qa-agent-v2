---
name: ft-test-case-writer
description: Писать или корректировать тест-кейсы для уже подтверждённого scope ФТ, сохраняя трассировку, исполнимость и пригодность для ручного тестирования и автоматизации.
---

# FT Test Case Writer

Используй этот skill только для изолированной writer-фазы, когда FT package,
scope и активный workflow уже подтверждены. Для обычной новой задачи «написать
тест-кейсы по ФТ» используй [ft-practical-route](../ft-practical-route/SKILL.md),
а не этот skill напрямую.

Перед работой прочитай [runtime contract](../../references/agent/writer-runtime-contract.md),
[runtime workflow](../../references/agent/writer-runtime-workflow.md),
[формат production TC](../../references/qa/test-case-runtime-format.md) и,
если это v0.9 scope, [practical v0.9 route](../../references/agent/practical-test-case-route-v0.9.md).

## Входы

Выбранный scope, его main DOCX/XHTML/PDF/support/visual inputs,
`AGENT-NOTES.md`, актуальный `workflow-state.json`, source obligations,
matrix и findings reviewer-а, если это разрешённая доработка.

## Выходы

Только текущая matrix либо canonical TC своего scope и обновлённый
`workflow-state.json`; не создавай self-check, stage summary или новые
процессные копии покрытия.

## Правила

1. Один TC имеет один пользовательский поток, одну основную проверку и один
   primary expected result. Однотипные значения одного элемента объединяй
   параметризацией только при одном действии и одинаковой реакции.
2. Одна matrix строка связана с одним `OBL-*`, одним `CTX-*` и одним `SCN-*`.
   Контекстный lifecycle определяй по `flow_kind`, а не по названию `CTX-*`.
3. Сохраняй коды требований, таблицы/строки и source anchors. Не выдумывай
   правило по макету, UI или названию поля.
4. В runtime-полях пиши по-русски. Английские enum допустимы только для
   согласованных metadata. Не включай в TC `SETUP-*`, URL, маршрут входа,
   конкретные логины, роли, пароли или токены.
5. Тестовые данные содержат конкретные значения, файлы или точные свойства и
   способ подготовки. Для DaData используй сохранённый проверенный fixture;
   синтетические данные не подменяют интеграционный источник.
6. Для `create` с успешным сохранением укажи конкретный ключ объекта,
   исходное отсутствие объекта и изоляцию/очистку, если ФТ требует создание.
7. До TC writing matrix должна пройти mandatory independent matrix review.
   После TC writing требуется separate-session final TC review. В каждой
   фазе разрешена только одна целевая доработка и один re-review.

## Ограничения

Не запускай reviewer в той же сессии и не изменяй raw reviewer result. Не
используй benchmark, sharding, semantic bridge или повторные repair-loop.
Не превращай gap или source contradiction в выдуманный executable TC.
