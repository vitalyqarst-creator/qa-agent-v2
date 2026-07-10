# Prepared writer create-contract canary v8

## Итог

- Статус: `accepted-not-promoted`.
- Writer создал declared output первым file-change событием с kind `add`.
- First meaningful artifact: `51.844 s` при deadline `90 s`.
- Writer duration: `83.875 s`; commands: `2 / 8`.
- Reviewer duration: `26.703 s`; commands: `0 / 1`; status `accepted`.
- Reviewer verdicts: `3 covered`, `3 gap-preserved`; blocking findings `0`.
- Draft SHA-256: `f496f694c1e48102676e6bbf674421b6dc8b4fa2ea488197f0e797684e3a6cd0`.
- Promotion выключен; production test case не создан.

## Create-contract evidence

Сохранённый JSONL stream фиксирует последовательность:

1. writer получил prepared prompt;
2. первое файловое событие для `stage-output/draft.md` имеет `kind = add`;
3. файл успешно создан до environment probe и последующей технической проверки;
4. seed sentinel отсутствует, структура и obligation gate прошли;
5. reviewer принял точный immutable draft hash.

Post-write `git status` внутри диагностической команды получил sandbox `dubious ownership`, но это не затронуло draft, evidence access, deterministic gates или reviewer verdict. Production mutation отсутствует.

## Решение

Create-vs-update blocker устранён. Canary допускает запуск benchmark из трёх независимых package v3 cycles с теми же budgets и promotion off.
