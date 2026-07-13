# Visual Assessment Medium-Scope Benchmark — Performance Analysis

## Сравнение С V4

| metric | V4 small scope | V1 medium scope | вывод |
| --- | ---: | ---: | --- |
| terminal result | `accepted` | `changes-required` | скорость улучшилась, semantic acceptance не достигнут |
| obligations | `4` | `13` | объём вырос в `3.25x` |
| test cases | `4` | `12` | объём вырос в `3x` без sharding |
| total duration | `66.562 s` | `108.813 s` | рост `63.5%`, но target `<120 s` выполнен |
| writer duration | `35.078 s` | `65.594 s` | writer обработал 12 TC за одну fresh session |
| reviewer duration | `31.484 s` | `43.219 s` | reviewer обработал 13 OBL за одну fresh session |
| total tokens | `43,535` | `55,198` | рост `26.8%` при росте obligations в `3.25x` |
| uncached input tokens | `41,458` | `49,970` | рост `20.5%` |
| uncached tokens / OBL | `10,364.5` | `3,843.85` | снижение `62.9%`; target `<8,000` выполнен |
| commands / file changes | `0 / 0` | `0 / 0` | read-only LLM boundary сохранился |

## Что Доказано

- Fixed context действительно амортизируется: средняя стоимость на obligation уменьшилась почти в `2.7x`.
- Один writer и один reviewer справились с medium scope без sharding, retry и filesystem tools.
- Полный chain занял `108.813 s`, на `11.187 s` меньше целевого лимита.
- Runtime identity, source evidence, package digest и production boundary сохранились.

## Что Не Доказано

- Semantic quality не масштабировалась автоматически вместе со скоростью.
- Writer получил полный hierarchical `DICT-001`, но в двух кейсах оставил только имена восьми групп и обобщение «все значения».
- Deterministic gates подтвердили structure/traceability, но не проверили concrete leaf-value completeness. Только semantic reviewer остановил цикл.

## Дополнительный Process Gap

Два requiredness-кейса корректно содержат `ui-calibration-required` и `candidate-ui-calibration`, однако runner-owned `calibration-lifecycle.json` имеет `open_count = 0`. Текущая lifecycle-логика регистрирует только `constraint_gap_ids` и не видит source-backed `covered_with_ui_calibration` без gap. Это не причина F-001, но отдельный риск потери handoff к UI calibration.

## Вывод

Главная гипотеза по производительности подтверждена: medium scope существенно дешевле на obligation и укладывается в две минуты. Главная гипотеза по качеству подтверждена частично: reviewer изолированно и быстро обнаруживает потерю данных, но deterministic layer пока пропускает неполное раскрытие словаря. Следующая итерация должна исправлять именно этот gate/materialization contract, а не снова оптимизировать prompt в целом.
