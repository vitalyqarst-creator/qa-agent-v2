# Live Canary Report: prepared runtime contract drift

## Итог

- Статус: `blocked-input`.
- Cycle: `codex-exec-prepared-widget-selection-live-v11-20260711`.
- Writer session: fresh ephemeral thread `019f4f94-14fe-7061-9019-fe79b87914ff`.
- Reviewer, standard control and promotion: не запускались.

## Blocker

Writer корректно вернул `route-to-standard-writer` и не создал draft:

1. Embedded `prepared-writer-runtime-profile.md` разрешает package version `3`, тогда как текущий fast-path package имеет version `4`.
2. Runner задаёт output нового v11 attempt, но immutable `stage-instructions.md` использованного compiled package содержит output/attempt path исходного compiler-cycle.

В v10 агент самостоятельно выбрал верхнеуровневый runtime path и продолжил. Это недетерминированно: конфликт должен быть устранён до LLM launch, а не решаться моделью.

## Safety

- Draft отсутствует.
- Intended canonical `test-cases/3-iteration-smoke-widget-selection-types.md` не создан.
- Promotion flags не передавались.
- Existing unrelated untracked test case и SDK diagnostics не изменялись.

## Следующее исправление

- закрепить prepared writer eligibility на package v4;
- компилировать immutable package непосредственно для target cycle/attempt;
- добавить runner preflight exact-match для declared `attempt_root` и `output_path`;
- mismatched package блокировать до thread start;
- после full tests повторить fast/control только в новых cycle directories.

