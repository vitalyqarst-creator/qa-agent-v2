Готово.

Что сделано:
- Создан исправленный unsigned draft: `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-structure-r1-draft.md`.
- TC перенумерованы в непрерывную последовательность `TC-ACPD-001`..`TC-ACPD-046`.
- Runtime-блоки приведены к parser-supported `### Предусловия / Тестовые данные / Шаги / Итоговый ожидаемый результат / Постусловия`.
- Обновлены ссылки на TC в текущих writer-owned artifacts и `cycle-state.yaml`.
- `cycle-state.yaml` переведен в `stage_status: writer-draft-ready`, `draft_test_cases` указывает на новый draft.
- Production файл `fts/AutoFin/test-cases/14-application-card-client-personal-data.md` не изменялся.

Проверка:
- Scoped profile: `unresolved_warning_error_count = 0`.
- Быстрый structure check: 46 TC, contiguous IDs, missing runtime sections: none.
- `validate_agent_artifacts.py` обновлен точечно, чтобы общий validator корректно читал canonical `###` runtime sections; после этого active draft/test-design scoped warning/error count = `0`.

Глобальный validator по всему `fts/AutoFin` всё еще показывает unrelated backlog в старых artifacts, но текущий draft/scope чистый для этого stage.