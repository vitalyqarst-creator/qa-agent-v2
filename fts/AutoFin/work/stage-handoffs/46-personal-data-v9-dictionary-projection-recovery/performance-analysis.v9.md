# V9 Performance Analysis

## Метрики

| stage | duration | input tokens | output tokens | total tokens |
| --- | ---: | ---: | ---: | ---: |
| reviewer-only rebind, 47 TC / 65 OBL | 78.313 s | 42,939 | 3,980 | 46,919 |
| total | 78.313 s | 42,939 uncached | 3,980 | 46,919 |

Одна reviewer session выполнила `0` commands и `0` file changes. Writer LLM не запускался; deterministic gates выполнены runner-ом до reviewer.

## Сравнение с V8 recovery

- Время снизилось с `188.625 s` до `78.313 s`: на `110.312 s` (`58.5%`).
- Токены снизились с `83,537` до `46,919`: на `36,618` (`43.8%`).
- Устранена целая writer-сессия V8 стоимостью `93.750 s` и `35,715` токенов.
- Reviewer input почти не изменился: `42,959` токенов в V8 против `42,939` в V9. Экономия получена за счёт корректного межэтапного handoff и отсутствия ненужной регенерации, а не за счёт урезания reviewer evidence.

## Вывод

Reviewer-only rebind оправдан только для hash-bound source-correct draft: он заметно ускоряет recovery и сохраняет полный reviewer context. Это не универсальная замена writer; новый scope должен пройти обычный writer-reviewer маршрут.
