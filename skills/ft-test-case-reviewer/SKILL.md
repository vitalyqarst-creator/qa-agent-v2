---
name: ft-test-case-reviewer
description: Независимо ревьюировать существующие тест-кейсы или matrix по ФТ: трассировка, покрытие, атомарность, исполнимость и качество формулировок.
---

# FT Test Case Reviewer

Используй для самостоятельного review уже созданной matrix или тест-кейсов.
Для standard practical v0.9 review работай только в отдельной верхнеуровневой
Codex-сессии, назначенной controller-ом. Subagent или та же writer-сессия не
являются независимым review.

Перед review прочитай [формат findings](../../references/qa/review-findings-format.md),
[runtime format TC](../../references/qa/test-case-runtime-format.md) и, для
v0.9 scope, [practical route](../../references/agent/practical-test-case-route-v0.9.md)
с [форматом result](../../references/agent/practical-v0.9-review-result-format.md).

## Входы

- immutable review manifest и его snapshot;
- DOCX/XHTML/PDF, релевантные support, решения БА и visual inputs;
- matrix или canonical TC в зависимости от режима review.

## Выходы

- один raw JSON reviewer result с вердиктом и source-backed findings;
- compact per-OBL receipt, когда его требует manifest.

## Режимы

- `full`: трассировка, структура и test design;
- `traceability`: связи ФТ → OBL → SCN → TC;
- `structure`: обязательные поля, язык, нумерация и исполнимость;
- `test-design`: coverage, атомарность, parameterization и boundary classes;
- `matrix`: обязательный pre-TC review matrix v0.9;
- `test-cases`: обязательный final TC review v0.9.

## Независимая проверка v0.9

1. Работай с immutable manifest/snapshot и сначала восстанови обязательства из
   DOCX/XHTML/PDF/support/approved BA decisions/visual inputs, а не из prose
   writer-а.
2. Сопоставь каждый активный `OBL-*` с matrix; затем, в режиме `test-cases`,
   с canonical TC. Для больших scope верни compact per-OBL vector, а не один
   общий digest.
3. Проверь source modifiers, `flow_kind`, исходные состояния, конкретные
   данные, primary oracle, статусы исполнения и допустимость объединений.
4. Верни один raw JSON по canonical format. Не изменяй matrix, TC,
   `workflow-state.json` или findings других агентов.

Проверяй каждый источник и `OBL-*` одним проходом, фиксируя один finding на
первопричину с перечнем затронутых `SCN-*`. Не повторяй уже сделанный анализ
ради новых формулировок и не создавай внутренние repair/self-check циклы:
после source-to-artifact сопоставления сразу верни raw JSON verdict.

## Вердикт

Допустимы только `approved`, `changes-required`, `blocked-input`. При
`changes-required` каждое content finding формулируй по-русски и привязывай к
source/artifact anchors. Не объявляй source-not-supported ложным и не
переводи его в approval: это спор или blocker для controller-а. Matrix и TC
имеют раздельные бюджеты одной доработки и одного re-review; третьего
автоматического цикла нет.

## Ограничения

Не изменяй matrix, canonical TC, workflow state или raw findings других
участников. Не заменяй independent review subagent-ом, той же writer-сессией
или самоаттестацией.
