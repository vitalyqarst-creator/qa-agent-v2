# Prepared reviewer live canary v5: blocker report

## Итог

- Статус: `blocked-timeout`; benchmark из трёх независимых циклов не запускался.
- Writer завершился успешно в отдельной ephemeral-сессии `019f4c12-9ac4-72b2-8818-cc4537a29b08`.
- Reviewer был запущен в новой read-only ephemeral-сессии `019f4c13-eba3-7242-8e6a-0aa213a61fa6`.
- Reviewer создал события `thread.started` и `turn.started`, но не выдал ни одного последующего semantic event до срабатывания idle-timeout.
- Promotion оставался выключен; production test case не создан.

## Подтверждённая часть изменения

Writer сформировал immutable draft с SHA-256 `9049ef12b3c90c0cf84f87775d54db5fd84c93037cdc25b2159811bb37bc2ec7`.

| проверка | результат |
| --- | --- |
| writer status | `completed` |
| writer duration | `86.344 s` |
| writer commands | `2 / 8` |
| obligation gate | `prepared-package-obligation-gate-v2`, `passed` |
| testable obligations | `3 / 3` |
| obligation findings | `0` |
| seed gate | `passed` |
| writer evidence-access gate | `passed`, запрещённых чтений `0` |

Исправление Markdown-границ obligation gate подтверждено не только replay старых артефактов, но и новым live draft: set-level gap не приписан последнему тест-кейсу, все три testable obligations покрыты.

## Реальный блокер

| показатель reviewer | результат |
| --- | ---: |
| hard timeout budget | `90 s` |
| idle timeout budget | `45 s` |
| фактическая длительность | `50.203 s` |
| semantic events после `turn.started` | `0` |
| commands | `0` |
| evidence-access gate | `passed` |
| termination reason | `idle-timeout` |

Низкоуровневый `stage-status.json` различает причины корректно: `timed_out=false`, `idle_timed_out=true`. Высокоуровневый `stage-result.json` сворачивает оба вида остановки в `timed_out=true` и terminal outcome `blocked`.

Это не похоже на ошибку схемы, command budget, доступа к evidence или obligation gate: CLI принял `--output-schema`, создал thread и начал turn; reviewer не выполнял команд и не обращался к запрещённым источникам. Canary v4 с тем же prepared reviewer contract завершил reviewer за `18.796 s`, поэтому наблюдается вариативность времени молчаливого model inference, а не детерминированный отказ stage contract.

## Инженерный вывод

Текущая комбинация `--output-schema` и reviewer idle-timeout `45 s` внутренне несогласована. Read-only reviewer не обязан выполнять shell-команды и может не отправлять промежуточные события: его первый содержательный результат является финальным structured object. Поэтому отсутствие stream-событий в течение 45 секунд не отличает корректное молчаливое формирование ответа от зависания и может обрывать процесс раньше hard budget `90 s`.

## Следующая узкая итерация

Рекомендуемый вариант:

1. Для prepared reviewer считать terminal hard deadline `90 s` основным ограничителем.
2. До первого semantic output не применять более короткий idle cutoff либо приравнять reviewer idle budget к terminal deadline с учётом требований валидатора конфигурации.
3. Повторить один immutable live canary с тем же package, promotion off и общим terminal budget не более `90 s`.
4. Только после успешного canary запускать benchmark из трёх независимых циклов.

Просто увеличивать hard timeout не требуется. Heartbeat через команды или текстовый прогресс также не рекомендуется: он усложнит read-only/structured-output contract и не даст более надёжного сигнала готовности.

## Readiness

Текущий статус: `experimental-only`. Stage-contract v2 и obligation gate v2 подтверждены локальными тестами и replay, но live benchmark заблокирован ложноположительным reviewer idle cutoff.
