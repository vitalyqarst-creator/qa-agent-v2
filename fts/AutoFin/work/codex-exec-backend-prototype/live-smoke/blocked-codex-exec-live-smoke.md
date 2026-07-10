# Live smoke blocker: `codex exec`

Статус: `blocked-codex-exec-unavailable`.

Live smoke не запускался. Единственный найденный `codex` executable из packaged WindowsApps installation возвращает `Access is denied` до обработки `--version` или `exec --help`. Поэтому невозможно подтвердить:

- наличие и синтаксис `codex exec`;
- sandbox/read-only enforcement;
- JSON/JSONL event schema;
- working-directory и output-last-message flags;
- auth и non-interactive approval behavior.

Запуск с предполагаемыми flags был бы небезопасным и не доказал бы reviewer isolation. Prototype проверен только fake process executor-ом. Writer/reviewer live stages не стартовали, final test-case artifact не создавался и fake success не фиксировался.
