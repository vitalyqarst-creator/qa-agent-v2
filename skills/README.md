# Runtime skills

В runtime доступны только четыре навыка:

| Skill | Когда использовать | Результат |
| --- | --- | --- |
| `ft-source-locator` | Новый FT-пакет | Подтверждённые primary/support/visual inputs |
| `ft-scope-analyzer` | Новый раздел ФТ | Границы scope, coverage gaps, вопросы БА, план fixtures |
| `ft-test-case-writer` | Подтверждённый scope | Fixtures → matrix → canonical TC по явному переходу |
| `ft-test-case-reviewer` | Matrix или готовые TC | Независимый verdict и ограниченный список findings |

Других default-маршрутов нет.

## Канонические runtime references

- `references/runtime/test-data-fixtures.md` — выбор и материализация тестовых данных;
- `references/runtime/source-selection.md` — формат и machine gate первого этапа;
- `references/runtime/test-design-profiles.md` — универсальные правила покрытия, атомарности и параметризации;
- `references/runtime/test-design-matrix.md` — компактный формат matrix;
- `references/runtime/test-case-runtime.md` — production-формат TC;
- `references/runtime/review-record.md` — независимость и SHA-256-актуальность review.
- `references/runtime/session-topology.md` — controller-owned распределение ролей по Codex-сессиям.

Обязательные проверки переходов: `scripts/runtime_session_registry.py`, `scripts/validate_runtime_source.py`, `scripts/validate_runtime_scope.py`, `scripts/validate_runtime_matrix.py` с inventory/gaps и `scripts/validate_runtime_tc.py` с matrix.
