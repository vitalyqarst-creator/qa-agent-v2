# Итоги shadow-итерации ограничений символов ФИО

## Результат

- Из текущего FT4 независимо выделены `BSR 48`, `BSR 51`, `BSR 54`; DaData и production baseline не использовались как evidence.
- Prepared compiler собрал 12 obligations и 1 non-blocking `GAP-001`, выбрав `standard-required`.
- Шесть positive checks используют конкретные значения текста и текста с дефисом.
- Шесть negative checks сохраняют раздельные классы `digits` и `special-chars` как `candidate-ui-calibration`; точная UI-реакция не выдумана.
- V3 завершился `accepted-not-promoted`: reviewer принял 12/12 obligations, blocking findings отсутствуют, semantic overlap отсутствует.
- Целевой production-файл не создан; promotion выключен.

## Immutable cycles

| cycle | результат | причина/доказательство |
| --- | --- | --- |
| V1 | `blocked-configuration` до LLM | writer command budget `8`, контрактный минимум `25` |
| V2 | `blocked-configuration` до LLM | reviewer command budget `4`, контрактный минимум `29` |
| V3 | `accepted-not-promoted` | 12 TC, obligation gate 12/12, reviewer accepted |

## Метрики V3

| metric | value |
| --- | ---: |
| Writer + reviewer | 386.907 с |
| Total tokens | 1 690 384 |
| Uncached input tokens | 208 136 |
| Writer | 197.078 с / 689 460 tokens |
| Reviewer | 189.829 с / 1 000 924 tokens |
| Validator invocations | 1 |
| Command executions | 74 |
| TC / obligations | 12 / 12 |

## Критическая оценка

Качество и изоляция результата приемлемы, но standard-route пока непригоден как регулярный быстрый путь. По сравнению с V6 static-properties (90.031 с / 54 291 tokens) этот цикл приблизительно в 4.3 раза дольше и в 31 раз дороже по total tokens. Scope сложнее, однако разница главным образом связана с большим standard context и повторным resolver/tool traversal в обеих сессиях, а не с количеством итоговых кейсов.

Две preflight-остановки не потратили LLM tokens, но показали, что dispatcher config допускает заведомо неверные budget values и обнаруживает их только после создания immutable cycle. Следующая process-итерация должна:

1. валидировать standard writer/reviewer budget floors до создания cycle-owned outputs;
2. сформировать компактный resolver manifest для prepared standard, чтобы writer/reviewer не перечитывали десятки файлов и не выполняли десятки команд;
3. передавать reviewer только immutable package, draft, deterministic reports и минимальный набор canonical instructions;
4. повторить тот же scope и требовать сохранения 12/12 coverage при существенном снижении uncached tokens и команд.

## Ограничение результата

`GAP-001` остаётся открытым до UI calibration на ПК со стендом. Accepted shadow draft не является regression-ready production набором и не должен promoted до фиксации фактического поведения invalid input.
