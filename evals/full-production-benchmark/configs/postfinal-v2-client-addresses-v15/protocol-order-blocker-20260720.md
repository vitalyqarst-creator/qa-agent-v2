# Диагностика второго preflight blocker v15

Статус: `blocked-before-benchmark`. Это не benchmark attempt.

В task `019f7f8a-3a13-7732-b7d2-2558a52c8132` запуск выполнял primary
root-agent без делегации, но остановился до wrapper. Причина — противоречие
инструкций: `AGENTS.md` и skill contract требуют сначала прочитать обязательные
инструкции и проверить runtime, а timing reference одновременно требовал сделать
metadata самым первым инструментальным действием.

Исправление: разрешён ограниченный pre-bootstrap preflight только для routing,
обязательных инструкций и environment probe. Затем тот же root-agent обязан без
промежуточных task actions выполнить пару metadata-bootstrap. Timer по-прежнему
начинается от исходного `turn_started_at_unix_ms`, поэтому время обязательного
preflight входит в `routing-preflight`.

Wrapper не вызывался; handoff, cycle и shadow output не создавались. Конфигурация
v15 остаётся неизменной и пригодна для следующего чистого запуска.
