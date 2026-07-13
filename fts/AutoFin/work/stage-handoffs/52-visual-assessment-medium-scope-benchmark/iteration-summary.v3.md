# Medium-Scope Benchmark V3 — Iteration Summary

## Результат

`accepted-not-promoted`

Fresh writer и fresh reviewer через `codex exec` подготовили и приняли 12 test cases, покрывающих все 13 obligations. Production target не создавался, FT-first baseline не изменён.

## Достигнуто

- V1 dictionary completeness defect закрыт и не регрессировал.
- Два source-backed calibration candidates сохранены без invented UI behavior.
- V2 alternative-action и dictionary-path ambiguity закрыты compiler/runner guards и подтверждены live reviewer.
- 13/13 obligations reviewer-covered, 0 findings.
- Uncached efficiency: 3,110.31 tokens/OBL; validator=1; orchestration overhead=1.48%.
- Три protected baseline hashes неизменны; promotion target отсутствует.

## Не Достигнуто

- Duration 124.532 s превышает target 120 s на 4.532 s.
- Draft дублирует exhaustive dictionary: writer вручную перечисляет значения, затем runner добавляет каноническую projection. Это не ломает качество, но увеличивает output и writer workload.

## Решение

V3 terminal и не повторяется. Следующая итерация должна быть offline-first: убрать дублирование dictionary projection, определить устойчивую latency metric и только затем решать, нужен ли новый live benchmark.
