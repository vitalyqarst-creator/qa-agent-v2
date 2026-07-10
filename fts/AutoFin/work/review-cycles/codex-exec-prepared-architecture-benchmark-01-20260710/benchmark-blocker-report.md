# Prepared pipeline architecture benchmark: live blocker

## Итог

- Benchmark cycle 1: `blocked-first-artifact-deadline`.
- Writer session: `019f4c43-b614-7c33-8aa4-f2ca45900f93`.
- Duration: `90.078 s`; commands: `1 / 8`; meaningful draft не создан.
- Reviewer не запускался.
- Benchmark cycles 2 и 3 не запускались.
- Promotion выключен; production test case не создан.

## Root cause

Runner создаёт immutable template как `runner-input/draft-seed.md`, но не создаёт файл по stage-produced output path `stage-output/draft.md`. При этом prepared writer profile и prompt используют формулировки `replace the draft seed at the declared output path` / `replace every seed sentinel`.

В этом запуске writer интерпретировал инструкцию как обновление существующего output-файла и вызвал `apply_patch` в режиме update. На `79 s` runtime вернул точную ошибку:

`apply_patch verification failed: ... stage-output/draft.md: файл не найден`.

До first-artifact deadline оставалось около `11 s`; retry/add-file не завершился. Это не model silence, source access, package v3 validation или semantic obligation failure. Это несогласованность file-state contract: instruction требует replace, а output file отсутствует.

## Почему это реальный архитектурный blocker

- Ошибка воспроизводима из сохранённого runner event и stderr, а не выводится косвенно из latency.
- Writer выполнил разрешённый environment probe и явно сообщил, что inline payload достаточен.
- Output parent существовал, но сам declared stage-produced file отсутствовал по design.
- First-artifact deadline корректно остановил попытку, однако он проявил неоднозначный create-vs-update contract.

## Рекомендуемая следующая итерация

Предпочтительный вариант:

1. Оставить `runner-input/draft-seed.md` immutable и runner-owned.
2. Не создавать seed или пустой файл в stage output: это размывает producer ownership и может давать ложный required-output progress.
3. Исправить prepared writer profile и generated prompt: output file изначально отсутствует; writer обязан создать его одним первым `Add File`/эквивалентным atomic write, используя seed только как inline template.
4. Добавить regression-тест, который фиксирует отсутствие output до stage и проверяет create-file wording в prompt/profile.
5. Повторить один immutable canary и только затем заново начать benchmark 3/3.

Увеличивать first-artifact deadline до исправления create-vs-update contract не рекомендуется: больший budget лишь дольше скрывал бы детерминированную ошибку первой записи.

## Readiness

Текущий статус: `experimental-only`. Package v3 P0/P1 trust-boundary remediation подтверждена успешным canary v7, но benchmark остановлен новым writer file-creation contract blocker.
