# Runtime skills

В runtime доступны только четыре навыка:

| Skill | Когда использовать | Результат |
| --- | --- | --- |
| `ft-source-locator` | Новый FT-пакет | Подтверждённые primary/support/visual inputs |
| `ft-scope-analyzer` | Новый раздел ФТ | Границы scope, source-level gaps, вопросы БА, логический контракт тестовых данных |
| `ft-test-case-writer` | Подтверждённый scope | Matrix → независимое принятие → материализация данных → canonical TC |
| `ft-test-case-reviewer` | Matrix или готовые TC | Независимый verdict и ограниченный список findings |

Других default-маршрутов нет.

## Канонические runtime references

- `references/runtime/test-data-fixtures.md` — логический контракт, материализация данных и сохранение внешних ответов;
- `references/runtime/source-selection.md` — формат и machine gate первого этапа;
- `references/runtime/scope-analysis.md` — углублённый анализ области и единый реестр вопросов к БА;
- `references/runtime/external-dependency-coverage.md` — условный контракт отсутствующих и поздних внешних источников;
- `references/runtime/test-design-profiles.md` — универсальные правила покрытия, атомарности и параметризации;
- `references/runtime/test-design-matrix.md` — компактный формат matrix;
- `references/runtime/test-case-runtime.md` — production-формат TC;
- `references/runtime/review-record.md` — независимость и SHA-256-актуальность review.
- `references/runtime/session-topology.md` — controller-owned распределение ролей по Codex-сессиям.

Нормализация канонического DOCX выполняется `scripts/normalize_ft_source.py`, а временный визуальный рендер PDF — `scripts/render_runtime_pdf.py`. Обязательные проверки переходов: `scripts/runtime_session_registry.py`, `scripts/validate_runtime_source.py`, `scripts/validate_runtime_scope.py`, `scripts/validate_runtime_matrix.py` с inventory/gaps, `scripts/validate_runtime_test_data.py` после принятия matrix и `scripts/validate_runtime_tc.py` с matrix/materialization. Review/re-review используют `scripts/runtime_review_dispatch.py`, `scripts/runtime_review_delta.py` и `scripts/validate_runtime_review.py`.
