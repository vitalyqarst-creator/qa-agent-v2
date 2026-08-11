# Формат `scope-obligations.json` practical v0.9

```json
{
  "schema_version": 1,
  "route_version": "practical-v0.9",
  "source_manifest_sha256": "<sha256 source-package-manifest.json>",
  "scope": {"id": "01", "slug": "9.1-menu", "title": "Меню"},
  "obligations": [
    {
      "id": "OBL-001",
      "source_anchor": "Раздел 9.1, Таблица 2, строка «Партнеры»",
      "statement": "В меню доступен пункт «Партнеры».",
      "risk_flags": []
    }
  ],
  "clarifications": []
}
```

`statement` — точное, проверяемое русскоязычное утверждение ФТ. Здесь не фиксируются шаги, конкретные fixtures, предполагаемый UI oracle, matrix ID и TC ID: это принадлежит последующим этапам.

`risk_flags` используй только из: `status-transition`, `cross-field-rule`, `closed-dictionary`, `integration`, `authorization`, `exception-over-general-rule`, `mapping-table`, `temporal-rule`, `high-fan-out`, `high-risk`. Они запускают conditional matrix review.
