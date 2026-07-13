# Stop Gate: V4r1 blocked-input

## Решение

`STOP — fixture-input-required`

## Подтверждено

- Prepared compiler и writer quality gate распознают ранее наблюдавшиеся V3 placeholders.
- Exact per-TC intent selection устраняет sibling-TC contamination.
- Verified `codex exec` запускает отдельную writer-сессию без SDK fallback.
- Writer корректно отказался придумывать отсутствующее содержимое fixtures.
- Создана ровно одна live attempt; reviewer отсутствует; production shadow отсутствует.

## Не подтверждено

- Полный draft из 47 TC.
- Прохождение deterministic writer gates полным V5 draft-ом.
- Reviewer acceptance и sign-off.
- Production/UI readiness.

## Blocking evidence

- `FIX-ACPD-SAVE-001` не раскрывает конкретный resettable save baseline.
- `FIX-ACPD-DADATA-001` не раскрывает точную проверенную тройку `ФИО → suggestion → Пол`.
- `cycle-state.yaml`: `workflow_status=blocked-input`, `accepted_terminal_state=false`, `final_promoted=false`.

## Условия возобновления

1. Обе fixtures зарегистрированы по `fixture-registration-request.md` без PII и секретов.
2. Новый compiler gate отклоняет absent/unresolved/generic fixture catalog до live.
3. Bad/corrected fixture-resolution eval и regression проходят.
4. Собран новый immutable V5 с исходными coverage counts, gap/dictionary refs и matching hashes.
5. Context/seed/dispatcher preflight и новый checkpoint проходят до единственного V5 live.

V4 и V4r1 запрещено retry, resume, rewrite или использовать как production output.
