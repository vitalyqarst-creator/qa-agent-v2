# Актуальность независимого review

Matrix и canonical TC проверяются в отдельных верхнеуровневых Codex-сессиях. Человекочитаемый итог хранится в `work/reviews/<scope>/<matrix|tc>-review.md`, а рядом создаётся машиночитаемая запись `<matrix|tc>-review.json`.

## Формат записи

```json
{
  "schema_version": 1,
  "review_kind": "matrix",
  "artifact_path": "work/practical/<scope>/test-design-matrix.md",
  "artifact_sha256": "<64 hex>",
  "reviewer_session_type": "codex-thread",
  "reviewer_session_id": "<top-level thread id>",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "verdict": "matrix-accepted",
  "findings": []
}
```

- `review_kind`: `matrix` или `tc`.
- Допустимые verdict: `matrix-accepted`, `matrix-changes-required`, `tc-accepted`, `tc-changes-required`.
- Accepted verdict требует пустой `findings`; changes-required требует непустой конечный список findings.
- Любое изменение проверенного artifact меняет SHA-256 и делает review устаревшим. После правки нужен новый review-record из отдельной сессии.
- Writer не создаёт TC без успешной проверки принятой matrix. Набор TC не считается выпущенным без успешной проверки `tc-accepted` для текущих байтов файла.

Проверка:

```text
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind matrix --require-accepted
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind tc --require-accepted
```

Review-record подтверждает актуальность и форму независимого review, но не заменяет содержательную проверку источников.
