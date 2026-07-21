# Чистовой запуск «Адреса клиента» v5

Запускать только в новой задаче Codex. Это новый immutable attempt: не продолжать v4,
не переиспользовать его handoff/cycle и не передавать прежние тест-кейсы или model-outputs
writer/reviewer. Результат выпускается только в shadow-файл; canonical baseline защищён от
перезаписи.

## Команда

Передать контроллеру фактические metadata первого пользовательского запроса новой задачи:

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/start_full_process_observation.py `
  --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v5/shadow-benchmark-config.json `
  --request-started-epoch-ms <REQUEST_EPOCH_MS> `
  --codex-turn-id <NEW_TURN_ID> `
  --request-start-source codex-request-metadata `
  --execute
```

## Проверенное ожидание маршрута

- исходный контекст содержит 44 строки, из них 27 включены в scope;
- shard `001` содержит 16 context/excluded-only строк и материализуется детерминированно:
  `model_invoked=false`, `attempt_count=0`;
- shards `002..004` имеют форму `11/10`, `10/10`, `7/7` и выполняются тремя отдельными
  tool-free model-сессиями, по одной попытке на shard;
- после merge полный semantic validator обязан подтвердить все 44 строки и 27 включённых;
- writer и один full reviewer работают только с новым материализованным handoff;
- promotion может записать только shadow v5.

Проверенный offline preview находится в `semantic-shard-plan-preview.json`, а привязка
состояния кода и результаты локальных gates — в `pre-clean-run-readiness.json`.

При terminal failure не продолжать повреждённый cycle. Сохранить observation и создать
следующий immutable attempt с новыми идентификаторами handoff/cycle/output.
