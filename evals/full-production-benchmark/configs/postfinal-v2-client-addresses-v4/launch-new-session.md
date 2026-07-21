# Чистый запуск «Адреса клиента» v4

Это новый immutable attempt после terminal failure v2 и offline-диагностики v3.
Запускать только в новой Codex-сессии. Старые test-cases/model outputs не
передаются writer/reviewer. Canonical файл не перезаписывается: результат идёт в
shadow artifact.

## Команда

Передайте контроллеру фактические request metadata новой сессии:

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/start_full_process_observation.py `
  --config evals/full-production-benchmark/configs/postfinal-v2-client-addresses-v4.json `
  --request-started-epoch-ms <REQUEST_EPOCH_MS> `
  --codex-turn-id <NEW_TURN_ID> `
  --request-start-source codex-request-metadata `
  --execute
```

## Ожидаемый маршрут

- observation wrapper автоматически включает semantic capacity preflight;
- при текущих 44 rows / 27 included rows ожидается 4 последовательных semantic
  shard-а с лимитами 10 included и 16 total rows;
- каждый shard использует fresh tool-free model session и ровно одну попытку;
- materialization разрешена только после deterministic merge и полного исходного
  semantic validator;
- writer/reviewer получают только новый materialized handoff; один full reviewer
  запускается после writer merge;
- promotion выпускает только shadow v4, canonical baseline не меняется.

При failure не продолжать повреждённый cycle: сохранить observation directory и
начать новый immutable attempt с новыми handoff/cycle/output идентификаторами.
