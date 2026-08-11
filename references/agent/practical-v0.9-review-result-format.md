# Формат независимого результата review practical v0.9

```json
{
  "review_manifest_sha256": "<sha256 manifest>",
  "scope_id": "<scope id from manifest>",
  "scope_slug": "<scope slug from manifest>",
  "review_mode": "matrix",
  "execution_surface": "codex-thread",
  "reviewer_thread_id": "<другая верхнеуровневая Codex-сессия>",
  "independent_obligations": ["OBL-001", "OBL-002"],
  "verdict": "approved",
  "findings": []
}
```

`reviewer_thread_id` — устойчивый UUID другой верхнеуровневой Codex-сессии;
он должен отличаться от `controller_thread_id` из manifest. Массив
`independent_obligations` должен содержать в точности идентификаторы `OBL-*`
из зафиксированного `scope-obligations.json`.

Сначала reviewer читает источники и формирует `independent_obligations`; затем сопоставляет их с matrix и, при `review_mode: test-cases`, с TC. Нельзя использовать transcript writer-а, self-check или изменения matrix/TC как вход первичной оценки.

`findings` содержит `id`, русскоязычное описание, `source_anchor`, `artifact_anchor`, `category`, `blocking` и `remediation_owner`.
