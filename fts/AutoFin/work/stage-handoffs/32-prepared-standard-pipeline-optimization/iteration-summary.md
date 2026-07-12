# Итоги блоков 1–10 масштабной итерации

## Реализовано

1. Выполнена script-first архитектурная инвентаризация; baseline и duplication map сохранены в `architecture-baseline.md`.
2. `stage-input.json` сохранен каноническим manifest; runner выпускает derived `artifact-graph.json` с lifecycle, producer/consumer и access policy.
3. Dispatcher запускает authoritative runner `--validate-only` до записи backend selection и до live cycle outputs; проверяется также drift `cycle_dir`.
4. Deterministic seed дополнен calibration metadata; runner materializes structured writer result.
5. Добавлены `prepared-standard-writer-mode=structured|assisted`; structured является default, assisted — только явный новый cycle.
6. Добавлены context profiles: simple field, character restriction, boundary, integration/persistence, conditional/state, general standard.
7. До reviewer создаётся quality bundle: structure/seed/obligation, unique titles, constraint gaps, calibration markers, overlap и evidence access.
8. Создаётся `calibration-lifecycle.json` со статусом `awaiting-ui-calibration` и обязательным re-review перед regression-ready.
9. Сохранены immutable attempt binding, no-resume и no-SDK-fallback правила; structured stages запрещают Git/search/file commands.
10. Performance report дополнен context bytes, instruction count, commands/file changes, TC/obligation counts и efficiency ratios.

## Проверенная миграция

- Static-properties package v5: validate-only `prepared-fast`, read-only, writer budget 0, final absent.
- Character-restrictions V4 package: 12 obligations, 1 gap, `standard-required`, profile `character-restriction-calibration`.
- V4 validate-only: writer read-only, command budget 0, compact reviewer, cycle artifacts не создавались.
- Production targets отсутствуют и не изменялись.

## Сравнение контекста

| metric | V3 live baseline | V4 validate-only | изменение |
| --- | ---: | ---: | ---: |
| Writer primary context | 204696 B | 44338 B | −78.3% |
| Writer instruction bytes | 166069 B | 3193 B | −98.1% |
| Writer instruction artifacts | 17 | 1 | −94.1% |
| Writer command budget | минимум 25 | 0 | закрыто |
| Reviewer input model | 19 files / 326387 B | embedded profile + verified payload | live measurement deferred |

Reviewer time/tokens intentionally не заявляются без live V4. Выполнение блоков 11–12 (репрезентативный eval corpus и live cycle) не входило в текущую команду.

## Критическая оценка

- Основное дублирование устранено без сокращения QA quality floor.
- `artifact-graph.json` является derived view; если начать редактировать его вручную, появится второй источник истины — это запрещено.
- Structured standard может вернуть `blocked-input` для действительно недостаточного inline evidence. Переход в assisted требует перекомпиляции нового cycle и не гарантирует успех.
- Производительность reviewer подтверждена contract/unit tests и меньшим allowlist, но абсолютное улучшение времени/tokens требует отдельного live V4.
