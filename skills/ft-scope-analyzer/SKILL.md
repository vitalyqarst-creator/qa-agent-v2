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
- `scope-clarification-requests.md`, если найден вопрос, меняющий тестовую
  идею; если вопросов нет, явная соответствующая отметка;
- понятное описание того, что передать matrix writer-у.

## Последовательность

1. Восстанови структуру по DOCX/XHTML; PDF используй для structural/visual
   cross-check. Макет/Figma может подтвердить UI-элемент, но не бизнес-правило.
2. Выдели внешний scope по разделу или непрерывному функциональному фрагменту
   ФТ. Не создавай внутренние пакеты ради ограничения объёма артефактов.
3. Для выбранного scope зафиксируй применимые разделы, таблицы, коды
   требований, рисунки и явные исключения в `source-scope.md`.
4. Собери вопрос к БА только при реальной неоднозначности, которая меняет
   expected result, ветку, данные или применимость проверки. Не спрашивай
   заранее про волатильные учётные записи, URL, роли стенда или fixture.
5. Передай scope в `ft-practical-route` для matrix. Не создавай source parity
   отдельным файлом, obligations, workflow state, validator report, matrix,
   test cases или review artifacts.

## Ограничения

- Не подменяй внешний scope техническими work packages.
- Не интерпретируй визуальный элемент как новое требование.
- Не создавай `practical-v0.9` artifacts, если пользователь явно не просит
  продолжить существующий v0.9 scope.
