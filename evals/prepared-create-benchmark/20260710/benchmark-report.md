# Prepared writer create-contract benchmark

## Итог

- Canary v8: `accepted-not-promoted`.
- Benchmark 1/3: `accepted-not-promoted`.
- Benchmark 2/3: `blocked-first-artifact-deadline`.
- Benchmark 3/3 не запускался по live stop-condition.
- Promotion во всех запусках выключен; production test case не создан.

## Результаты

| run | writer first artifact | writer duration | first file event | reviewer | terminal status |
| --- | ---: | ---: | --- | ---: | --- |
| canary v8 | `51.844 s` | `83.875 s` | `add` | `accepted`, `26.703 s` | `accepted-not-promoted` |
| benchmark 1 | `79.015 s` | `102.687 s` | `add` | `accepted`, `20.219 s` | `accepted-not-promoted` |
| benchmark 2 | отсутствует | `90.079 s` | отсутствует | не запускался | `blocked-first-artifact-deadline` |

## Проверка предыдущего blocker

Create-vs-update дефект устранён:

- в canary и benchmark 1 первым файловым событием был успешный `file_change kind=add`;
- в benchmark 2 writer не выполнял update-only patch и не получил `file not found`;
- writer корректно сообщил, что создаст output, выполнил environment probe и подтвердил достаточность inline evidence.

Следовательно, benchmark 2 обнаружил другой blocker: абсолютный first-artifact deadline `90 s` пересекается с реальным верхним хвостом времени формирования полного первого draft.

## Инженерный вывод

First-artifact deadline сейчас используется как correctness blocker, хотя по факту это latency guard. Сохранённые успешные live runs уже показывали первые artifacts примерно на `69–86 s`; новый корректный benchmark дошёл до `79.015 s`. Запас до `90 s` слишком мал для вариативности model inference. В blocked run не было forbidden read, update-file ошибки или semantic/package failure — процесс остановлен во время формирования первого `Add File`.

## Следующая узкая итерация

Рекомендуемый вариант:

1. Сохранить writer hard timeout `180 s` и post-write idle timeout `60 s`.
2. Увеличить только first-artifact deadline до `120 s` как отдельный bounded latency experiment.
3. Не считать agent messages и environment probe meaningful artifact: deadline должен завершаться только после реальной записи draft.
4. Добавить unit regression для независимости hard/idle/first-artifact budgets и документировать `120 s` как experimental SLO, а не автоматический retry.
5. Повторить canary, затем заново выполнить benchmark 3/3.

Удалять first-artifact guard полностью или предварительно создавать runner-owned output не рекомендуется: первый вариант теряет раннее обнаружение зависания, второй нарушает stage producer ownership.

## Readiness

Статус остаётся `experimental-only`. Create contract подтверждён, но `90 s` first-artifact SLO недостаточно устойчив для benchmark 3/3.
