# V7 Performance Analysis

## Фактический расход

| metric | value |
| --- | ---: |
| dispatcher runs | 1 |
| writer sessions | 1 |
| reviewer sessions | 1 |
| wall time | 178.406 s |
| writer duration | 47.578 s |
| reviewer duration | 130.828 s |
| writer tokens | 25175 |
| reviewer tokens | 48671 |
| total tokens | 73846 |
| uncached input tokens | 64991 |

## Оценка

По сравнению с V6 writer route стал существенно дешевле: одна targeted session вместо четырёх full-set shards, при этом `43/47` секций не регенерировались. Writer занял около 27% wall time и 34% tokens.

Основной расход теперь приходится на reviewer: 73% wall time и 66% tokens были потрачены до post-parse отклонения одного несовместимого verdict. Следующий наибольший выигрыш даёт schema-level ограничение verdict-ов до запуска, а не повторная оптимизация writer.

Кэш входного контекста не использовался. Для следующей итерации важнее сократить риск потерянной reviewer-сессии и структурировать dictionary projection; уменьшение общего evidence без этих гарантий создаст больший риск ложных findings.
