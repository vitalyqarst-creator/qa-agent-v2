# Metadata preflight blocker

Benchmark v15 не запускался. Делегированный turn остановлен fail-closed на фазе `request-metadata`, потому что metadata содержала `thread_source=subagent`.

- production wrapper не вызывался;
- benchmark attempt не создавался;
- handoff, cycle и shadow artifact не создавались;
- canonical и исходные DOCX/XHTML/PDF сохранили ожидаемые SHA-256;
- тот же config v15 остаётся пригодным для одного clean run.

Исправление: metadata call и schema-v2 bootstrap выполняет лично primary root-agent исходного user turn без `spawn_agent`, дочерней задачи или другого thread.
