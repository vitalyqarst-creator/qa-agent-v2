---
name: agent-architecture-auditor
description: Аудировать структуру AGENTS, skills, references и вспомогательных скриптов на предмет дублирования, неправильного размещения знаний и разрастания skill-слоя. Используй навык, когда нужно проверить, остается ли агентная архитектура проекта чистой, каноничной и удобной для роста.
---

# Agent Architecture Auditor

Используй этот навык как governance-аудитор agent-layer.

## Входы

- `AGENTS.md`;
- `skills/`;
- shared references в `references/`;
- вспомогательные скрипты;
- архитектурные тесты agent-layer.

## Выходы

- findings по severity;
- duplication map;
- recommended moves;
- список устаревших файлов, секций и references;
- краткий remediation plan.

## Workflow

### Baseline audit

1. Сначала запусти helper script `skills/agent-architecture-auditor/scripts/audit_agent_architecture.py` как preferred audit path.
2. Используй его вывод как базовый источник фактов: `checks`, `findings`, `duplication_map`, `stale_items` и `summary`.
3. Если нужен машиночитаемый отчет, используй `--json`; если нужен быстрый человеческий обзор, используй `--text`; по умолчанию скрипт выдает оба формата.
4. Не подменяй script-first workflow ручным перечитыванием файлов, если скрипт уже может доказать или опровергнуть нарушение автоматически.

### Manual follow-up

1. После baseline audit вручную разберись только с теми зонами, где скрипт не может уверенно доказать проблему.
2. Уточняй severity и `recommended_move`, если вывод требует архитектурного суждения.
3. Не создавай новые доменные правила; ссылайся на канонические references и предлагай перенос в правильное место.
4. Если agent instructions изменены, определи затронутые instruction-loading scenarios и проверь материал с позиции целевого агента, которому доступен только фактически загружаемый контекст.

## Формат результата

- findings перечисляй по severity;
- duplication map отделяй от основной ленты findings;
- `recommended_move` формулируй как конкретное следующее действие;
- outdated или stale items выноси отдельным блоком;
- заверши ответ кратким remediation plan.

## Канонические references

- Индекс контрактов инструкций: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Размещение знаний: [../../references/agent/content-placement.md](../../references/agent/content-placement.md)
- Границы skill-ов: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)
- Политика против дублирования: [../../references/agent/duplication-policy.md](../../references/agent/duplication-policy.md)
- Правила написания инструкций: [../../references/agent/instruction-authoring-policy.md](../../references/agent/instruction-authoring-policy.md)
- Чек-лист аудита: [../../references/agent/maintenance-checklist.md](../../references/agent/maintenance-checklist.md)
- Формат audit findings: [../../references/agent/audit-output-format.md](../../references/agent/audit-output-format.md)

## Ограничения

- Не создавай новые доменные правила как источник истины.
- Не подменяй собой writer, reviewer, source locator или scope analyzer.
- Не исправляй автоматически все найденные проблемы без отдельного запроса; по умолчанию сначала давай audit findings.
- Не редактируй файлы в baseline audit режиме; helper script должен оставаться read-only.
