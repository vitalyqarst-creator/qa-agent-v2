# Формат независимого результата review practical v0.9

```json
{
  "review_manifest_sha256": "<sha256 manifest>",
  "scope_id": "<scope id from manifest>",
  "scope_slug": "<scope slug from manifest>",
  "review_mode": "matrix",
  "execution_surface": "codex-thread",
  "reviewer_thread_id": "<другая верхнеуровневая Codex-сессия>",
  "independent_obligations": [
    {
      "source_anchor": "Раздел 9.1, строка «Партнеры»",
      "statement": "В меню доступен пункт «Партнеры».",
      "obligation_ids": ["OBL-001"]
    }
  ],
  "verdict": "approved",
  "findings": []
}
```

`reviewer_thread_id` — устойчивый UUID другой верхнеуровневой Codex-сессии;
он должен отличаться от `controller_thread_id` из manifest. Каждый элемент
`independent_obligations` содержит восстановленные reviewer-ом `source_anchor`
и `statement`, а также связанные `obligation_ids`. Все `obligation_ids` в
сумме должны в точности покрывать `OBL-*` из зафиксированного
`scope-obligations.json`.

Сначала reviewer читает источники и формирует `independent_obligations`; затем сопоставляет их с matrix и, при `review_mode: test-cases`, с TC. Нельзя использовать transcript writer-а, self-check или изменения matrix/TC как вход первичной оценки.

При восстановлении нельзя упрощать исходную норму до более широкого утверждения:
обязательно сохраняй контекст выполнения (например, создание и
редактирование), кванторы, граничные значения, условия и исключения. Если
разные контексты или классы входных данных дают самостоятельные проверяемые
потоки, они должны быть разложены на разные `OBL-*`/matrix rows/TC.

`blocked-observability` — допустимый статус исполнения для представимого
утверждения ФТ. Finding о том, что matrix/TC должен использовать этот статус,
не объявляет требование external blocker и не должен автоматически иметь
`blocking: true`; блокирующим остаётся только отсутствие представимого
source-backed покрытия или противоречие источников.

`findings` содержит `id`, русскоязычное описание, `source_anchor`, `artifact_anchor`, `category`, `severity`, `blocking`, `blocking_reason` и `remediation_owner`.

Reviewer возвращает этот объект как один raw JSON submission. Controller не
исправляет и не переформулирует его поля, в том числе source anchors, а
сохраняет byte-for-byte через `capture_practical_review_result.py`. Ошибка
кодировки исправляется только новым submission reviewer-а или исправлением
validator-а; она не даёт controller-у права нормализовать evidence.
