---
name: ft-source-locator
description: Находит FT-пакет и создаёт единый source-package manifest для practical route v0.9. Используй до анализа scope, когда нужно определить главный DOCX, обязательный XHTML, PDF, support, решения БА и визуальные материалы.
---

# FT Source Locator

Используй только для выбора FT-пакета и регистрации его входов. Для нового
scope результатом является package-level manifest practical v0.9, а не
legacy handoff, state или тест-кейсы.

До работы прочитай [practical route v0.9](../../references/agent/practical-test-case-route-v0.9.md)
и [формат реестра решений БА](../../references/agent/practical-v0.9-ba-decision-registry-format.md).

## Входы

- запрос пользователя и структура `fts/`;
- доступные `source/`, `support/`, `mockups/` и зарегистрированные Figma links;
- package-specific `AGENT-NOTES.md`, если он есть.

## Выходы

- выбранный корень FT-пакета;
- главный DOCX и matching XHTML основного ФТ;
- доступный PDF для structural/visual cross-check;
- разделённые `support_inputs`, утверждённые решения БА и `visual_inputs`;
- `work/practical-v0.9/source-package-manifest.json`;
- `blocked-input` с причиной `missing-main-ft-xhtml`, если XHTML отсутствует.

## Workflow

1. Найди FT-пакет и проверь его корень. Не смешивай соседние версии и
   предыдущие прогоны с выбранным пакетом.
2. Определи главный DOCX ФТ и matching XHTML в `source/`. DOCX задаёт смысл,
   XHTML обязателен для машиночитаемого извлечения. При отсутствии XHTML
   зафиксируй `blocked-input` и остановись до scope analysis.
3. Найди PDF того же ФТ. Передавай его только как structural/visual
   cross-check; отсутствие PDF не блокирует practical route.
4. Найди `AGENT-NOTES.md`, стабильные support-файлы, package-level файл
   `*-approved-ba-decisions.md`, локальные макеты и
   `support/figma/figma-design-index.md`, если он есть. Зарегистрируй макеты
   и Figma как необязательные визуальные источники: решения БА передавай
   только через `--ba-decisions`, а макеты и Figma — только через `--visual`;
   на этой стадии не открывай scope и не выводи бизнес-правила только из
   visual inputs.
5. Создай единый package-level manifest штатной командой:

   ```text
   python scripts/create_practical_source_manifest.py --ft-package-root <package> --docx <docx> --xhtml <xhtml> [--pdf <pdf>] [--support <stable-support>] [--visual <mockup-or-figma-index>] [--ba-decisions <approved-ba-decisions>] --output work/practical-v0.9/source-package-manifest.json
   ```

6. Проверь, что manifest содержит только входы текущего FT-пакета и их
   актуальные SHA-256. Если выбор источника неоднозначен, перечисли кандидаты
   и не создавай scope artifacts.
7. Передай выбранный package и manifest в `ft-scope-analyzer` либо
   `ft-practical-route`. Не создавай `scope-obligations.json`, matrix,
   test-cases, review artifacts, `workflow-state.json`, legacy handoff-папки,
   session logs или prompts следующих этапов.

## Clean Diagnostic Isolation

Если пользователь запросил clean diagnostic/eval run:

- работай только внутри выбранного FT-пакета;
- не используй соседние пакеты, старые baseline или прошлые test-cases как
  источник требований или тестовых данных;
- общие `skills/`, `references/` и scripts допустимы как правила агента;
- если чужой package artifact всё же был открыт, сообщи о contamination risk
  и не называй результат clean.

## Канонические references

- [Practical route v0.9](../../references/agent/practical-test-case-route-v0.9.md)
- [Реестр решений БА](../../references/agent/practical-v0.9-ba-decision-registry-format.md)
- [Границы skill-ов](../../references/agent/skill-boundaries.md)

## Ограничения

- Не анализируй разделы и не формируй `OBL-*`.
- Не создавай matrix, тест-кейсы, reviewer output или automation-ready версию.
- Не используй Figma/макет как источник бизнес-правила, обязательности,
  валидации или expected result.
