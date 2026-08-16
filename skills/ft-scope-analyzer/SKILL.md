---
name: ft-scope-analyzer
description: Выделять внешние scope ФТ, подтверждать границы выбранного scope и фиксировать только важные вопросы до test design.
---

# FT Scope Analyzer

Используй после выбора FT package, когда нужно предложить или подтвердить
раздел/подраздел для дальнейшей работы. Для practical v1 этот skill готовит
только границы scope; matrix и TC здесь не создаются.

Прочитай [scope decomposition policy](../../references/agent/scope-decomposition-policy.md)
и [practical route v1](../../references/agent/practical-test-case-route-v1.md).

## Входы

- выбранный FT-пакет с DOCX/XHTML и доступным PDF;
- подтверждённый внешний scope либо запрос на выбор;
- package-specific notes, support и visual inputs текущего FT-пакета.

## Выходы

- при необходимости выбора: `work/practical-v1/scope-options.md`;
- для выбранного scope: заготовка `source-scope.md` с границами и source refs;
- всегда создаваемый `scope-clarification-requests.md`: карточки `BAQ-*` по
  [формату practical v1](../../references/agent/practical-v1-clarification-requests-format.md),
  если вопрос меняет тестовую идею, либо явная отметка при их отсутствии;
- понятное описание того, что передать matrix writer-у.

## Последовательность

1. Восстанови структуру по DOCX/XHTML; PDF используй для structural/visual
   cross-check. Если в пакете есть Figma-запись, релевантная scope, один раз
   открой её до матрицы: используй `node-id`, если он указан, иначе сам найди
   страницу/фрейм по названию scope, экрана или элемента. Не требуй `node-id`
   от пользователя. В `source-scope.md` зафиксируй страницу/фрейм и итог
   `checked-and-used`, `checked-no-new-information`, `unavailable` или
   `not-relevant`; `not_checked` после анализа недопустим. Недоступная Figma
   не блокирует работу. Макет/Figma может подтвердить UI-элемент, но не
   бизнес-правило.
2. Выдели внешний scope по разделу или непрерывному функциональному фрагменту
   ФТ. Не создавай внутренние пакеты ради ограничения объёма артефактов.
3. Для выбранного scope зафиксируй применимые разделы, таблицы, коды
   требований, рисунки, явные исключения и глобальные правила типов данных
   его полей в `source-scope.md`.
4. Собери вопрос к БА только при реальной неоднозначности, которая меняет
   expected result, ветку, данные или применимость проверки. Создай для него
   поля `Статус`, `Ответ БА` и `Решение для тест-дизайна`; при повторной
   материализации сохрани уже введённый ответ. Не спрашивай заранее про
   волатильные учётные записи, URL, роли стенда или fixture.
5. Передай scope в `ft-practical-route` для matrix. Не создавай source parity
   отдельным файлом, obligations, workflow state, validator report, matrix,
   test cases или review artifacts.

## Ограничения

- Не подменяй внешний scope техническими work packages.
- Не интерпретируй визуальный элемент как новое требование.
- Не создавай `practical-v0.9` artifacts, если пользователь явно не просит
  продолжить существующий v0.9 scope.
