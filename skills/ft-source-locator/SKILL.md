---
name: ft-source-locator
description: Находит FT-пакет и регистрирует минимальный набор исходников для дальнейшего выбора scope или practical v1.
---

# FT Source Locator

Используй до scope analysis, когда нужно определить FT-пакет, основной ФТ,
support-файлы и макеты. Не создавай test design или тест-кейсы.

Для нового обычного маршрута прочитай
[practical route v1](../../references/agent/practical-test-case-route-v1.md).

## Входы

- запрос пользователя и структура `fts/`;
- доступные `source/`, `support/`, `mockups/` и Figma links;
- `AGENT-NOTES.md`, если он есть.

## Выходы

- выбранный корень FT-пакета;
- главный DOCX и matching XHTML основного ФТ;
- доступный PDF, support, утверждённые ответы БА и visual inputs;
- компактный `work/practical-v1/source-selection.md`, если результат нужно
  передать другому этапу;
- `blocked-input`, если нет DOCX или matching XHTML.

## Последовательность

1. Найди FT-пакет и не смешивай его с соседними версиями и прошлыми прогонами.
2. Выбери DOCX и matching XHTML из `source/`; DOCX задаёт смысл, XHTML
   обязателен для извлечения структуры.
3. Найди PDF для structural/visual cross-check, `AGENT-NOTES.md`, support,
   утверждённые ответы БА, макеты и доступный Figma index.
4. Если нужен handoff, создай `source-selection.md` с путями к фактически
   выбранным входам, их ролью и кратким объяснением приоритета. Не хешируй
   файлы и не создавай manifests, obligations, workflow state или receipts.
5. Передай выбранный package в `ft-scope-analyzer` либо в `ft-practical-route`.

## Ограничения

- Не анализируй требования и не формируй матрицу или TC.
- Не используй Figma/макет как источник бизнес-правила.
- Не создавай `practical-v0.9` artifacts, если пользователь прямо не просит
  продолжить уже существующий v0.9 scope.
