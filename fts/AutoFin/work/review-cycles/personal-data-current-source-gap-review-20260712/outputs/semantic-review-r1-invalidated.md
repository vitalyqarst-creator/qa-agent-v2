# Инвалидация первого запуска semantic review R1

- Статус: `invalidated-process-defect`.
- Причина: bounded semantic prompt включил production-файл `test-cases/14-application-card-client-personal-data.md` вместо активного unsigned draft `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-structure-r1-draft.md`.
- Следствие: findings `SEM-001`..`SEM-003` относятся к рассинхронизации старого baseline с новым test-design package и не являются результатом проверки активного draft.
- Защитное действие: `writer-r2` остановлен до внесения изменений; canonical baseline не изменён.
- Исправление runner: bounded semantic review теперь выбирает тот же active test-case artifact, что и scoped validator gate; writer semantic-revision prompt запрещает менять canonical до reviewer sign-off.
- Решение по циклу: состояние возвращено в `semantic-review-ready`; R1 должен быть запущен повторно в новой reviewer session.
