# Производительность V4r1

## Фактический результат

| метрика | значение |
| --- | ---: |
| live stages | 1 writer; reviewer не запускался |
| wall time | 17 172 ms |
| input tokens | 38 071 |
| output tokens | 308 |
| total tokens | 38 379 |
| commands | 0 |
| file changes агентом | 0 |
| validator invocations | 0 |

`exec` transport сработал быстро и корректно: capability preflight занял 93 ms, fallback не использовался, first output получен примерно за 0,766 s.

## Оценка с точки зрения цели процесса

Остановка за 17 секунд лучше, чем генерация неполного draft и дорогой reviewer-pass. Но расход 38 071 входного токена на обнаружение отсутствующего содержимого двух fixtures всё ещё слишком велик: blocker можно было найти локальным deterministic preflight без обращения к модели.

Следующая оптимизация должна быть не сокращением writer context вслепую, а переносом fixture-resolution в compiler/pre-live gate:

1. каждый `fixture_id` разрешается в `fixture-catalog.md`;
2. generic/conditional/отсутствующий `concrete_data` отклоняется до package build;
3. dependency и cleanup обязательны для save/integration fixtures;
4. live writer получает только уже доказанный execution contract.

## Неблокирующие технические наблюдения

- `cycle-state.yaml` содержит путь `draft_test_cases`, хотя при `blocked-input` файл draft не создан. Состояние не было изменено задним числом; это отдельный кандидат на исправление runner-state semantics.
- `legacy_notify` hook сообщил Windows `os error 206` из-за длины имени, но exec contract и writer-result сохранены полностью; на исход итерации это не повлияло.
