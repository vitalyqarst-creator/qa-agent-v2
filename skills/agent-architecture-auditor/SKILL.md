---
name: agent-architecture-auditor
description: "Аудировать lean QA runtime-v1: его active skills, references, маршруты и канонические архитектурные инварианты. Используй только для сопровождения agent-layer, не в FT route."
---

# Agent Architecture Auditor

Dev-only governance skill. Он аудирует указанный runtime-v1 и не должен попадать в clean FT workspace.

## Входы

- явный `--root` актуального runtime-v1;
- `AGENTS.md`, четыре active skills, `references/runtime/`, scripts и runtime tests внутри этого корня.

## Выходы

- findings по severity;
- фактический профиль и список выполненных/пропущенных проверок;
- битые и недостижимые references, legacy markers, кандидаты дублирования;
- верхнюю оценку объявленного instruction context каждого skill по достижимым ссылкам.

## Baseline audit

1. Запусти script-first workflow:

   `python skills/agent-architecture-auditor/scripts/audit_agent_architecture.py --root <runtime-v1-root> --profile runtime-v1 --json --fail-on error`

2. Для короткой инженерной итерации добавь `--with-tests`. Без флага аудит намеренно быстрый.
3. Если профиль не распознан, остановись. Не применяй legacy-правила к неизвестному дереву.

## Manual follow-up

- Разбирай вручную только findings и `duplication_map`, где нужно архитектурное суждение.
- Не превращай точное текстовое совпадение в ошибку без проверки: краткое напоминание может быть допустимым.
- После изменений прогони audit с `--with-tests`, а затем отдельный lint, если он есть в репозитории.

## Канонические references

- [Audit output](../../references/agent/audit-output-format.md)
- [Content placement](../../references/agent/content-placement.md)
- [Duplication policy](../../references/agent/duplication-policy.md)
- [Instruction authoring](../../references/agent/instruction-authoring-policy.md)

## Ограничения

- Аудит только для `runtime-v1`; legacy/full архитектура не поддерживается.
- Не запускай его как этап source/scope/writer/reviewer.
- Baseline audit read-only. Не исправляй findings без запроса.
- Не проверяй через него содержание конкретного ФТ, матрицы или TC.
