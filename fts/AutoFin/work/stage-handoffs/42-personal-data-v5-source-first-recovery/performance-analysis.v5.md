# Performance Analysis V5

| metric | value |
| --- | ---: |
| stages started | 1 |
| writer sessions | 1 |
| reviewer sessions | 0 |
| duration | 19.609 s |
| input tokens | 38 512 |
| output tokens | 613 |
| total tokens | 39 125 |
| command executions | 0 |
| file changes by writer | 0 |
| produced test cases | 0 |

V5 доказал, что текущий structured one-shot transport не масштабируется до полного набора 47 TC: почти весь расход ушёл на повторную передачу входного контекста, после чего writer не начал полезную генерацию. Следующая оптимизация должна уменьшить одновременно размер входа на writer-сессию и максимальный размер одного output contract.
