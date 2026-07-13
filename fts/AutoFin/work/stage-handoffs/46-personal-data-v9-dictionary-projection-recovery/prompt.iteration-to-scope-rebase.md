# New-Scope Prepared Pipeline Benchmark

## Цель этапа

Выбрать новый независимый AutoFin scope для проверки обычного prepared standard writer-reviewer процесса после успешного V9 recovery. Personal-data повторно не запускать.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/live-result.v9.json`
- `fts/AutoFin/work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/performance-analysis.v9.md`
- `fts/AutoFin/work/stage-handoffs/46-personal-data-v9-dictionary-projection-recovery/stop-gate.md`

## Обязательные действия

1. Сохранить H46/V9 неизменным и не выполнять promotion.
2. Через `ft-scope-analyzer` выбрать один другой внешний scope, для которого доступны обязательный XHTML, DOCX source-of-truth, source parity и актуальные scope artifacts.
3. Не использовать пользовательский untracked production testcase как requirements input и не перезаписывать существующие production test cases.
4. Создать новый numbered handoff и зафиксировать scope contract, gaps, dictionaries и benchmark acceptance criteria.
5. Для следующей iteration разрешить обычные fresh writer и reviewer sessions; reviewer-only rebind неприменим к новому scope.
6. До live потребовать compile, validate-only, artifact validator, exec dry-run, checkpoint/push и отдельную authorization.
7. Сравнить duration/tokens с сопоставимыми standard циклами; не выдавать recovery V9 за writer benchmark.

## Ограничения

- Не запускать UI: benchmark проверяет FT-first pipeline.
- Не возобновлять V8/V9 и не создавать второй dispatcher.
- Не смешивать scope-ы и не делать cross-scope production write.

## Ожидаемый результат

Один подтверждённый benchmark scope и воспроизводимый handoff к `ft-test-case-iteration`, либо `blocked-input` с точным отсутствующим source/scope artifact до любого LLM live-запуска.

## Gate завершения

Scope считается готовым только после явной проверки mandatory XHTML, source parity, atomic obligations, dictionary inventory и coverage gaps. Сам benchmark запускается отдельной итерацией.
