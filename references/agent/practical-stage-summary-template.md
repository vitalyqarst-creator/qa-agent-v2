# Шаблон сводки практического этапа

Используй этот шаблон для `practical-stage-summary.md` в practical route v0.8.5.
Это пользовательский handoff и одновременно проверяемый gate. Технические ключи
и значения перечислений не переводи: их читает валидатор.

## Сводка

| Поле | Значение |
| --- | --- |
| route_profile | `practical route v0.8.5` |
| summary_stage | `<short-stage-id>` |
| code_root | `<absolute path>` |
| execution_working_directory | `<absolute path; must equal code_root>` |
| ft_package_root | `<absolute path>` |
| artifact_write_root | `<absolute path>` |
| root_split_allowed | `yes / no` |
| root_split_authority | `<user/controller approval or not-applicable>` |
| next_stage_transition | `matrix-review allowed / matrix-review conditional / matrix-review blocked / writer allowed / writer conditional / writer blocked / tc-review allowed / tc-review conditional / tc-review blocked / not-applicable` |
| next_safe_step | `<одно предложение на русском>` |
| review_launch_preflight_status | `not-run / check-only-allowed / allowed / blocked / not-applicable` |
| review_launch_preflight_evidence | `<команда --check-only и result=allowed / путь к receipt / not-applicable>` |
| review_launch_preflight_receipt | `<FT-relative review-launch-preflight-rN.json or not-applicable>` |
| per_scope_next_stage_transitions | `yes / not-applicable` |
| production_tc_clean | `yes / no / mixed / not-applicable` |
| git_persistence | `tracked / ignored-by-git / mixed / not-applicable` |
| validator_primary_command | `python scripts/validate_agent_artifacts.py --root <FT package root> --json / not-run` |
| validator_primary_root | `<absolute FT package root or not-applicable>` |
| validator_supplementary_command | `<repo-root validator command or not-run>` |
| validator_findings_breakdown | `tc_quality=<n>; process_artifact=<n>; validator_path_resolution=<n>; unrelated_repo=<n>` |
| validator_raw_errors_count | `<integer: все ошибки package-root validator, включая self-check других stage summary>` |
| validator_errors_count | `<integer: ошибки, влияющие на маршрутизацию; без practical-stage-summary self-check>` |
| validator_summary_self_check_errors_count | `<integer: исключенный технический слой self-check>` |
| validator_summary_self_check_errors_evidence | `<finding id и путь или not-applicable>` |
| validator_scope_errors_count | `<integer for active_scope_ids, or not-applicable>` |
| validator_scope_errors_evidence | `<finding ids or not-applicable>` |
| validator_external_errors_count | `<integer for other scopes, or not-applicable>` |
| validator_external_errors_evidence | `<finding ids or not-applicable>` |
| validator_errors_classification | `none / next-stage-blocker / pre-existing-unrelated / validator-false-positive / mixed / not-applicable` |
| validator_errors_evidence | `<finding ids or not-applicable>` |
| validator_warnings_count | `<integer>` |
| validator_warnings_classification | `none / blocking-for-scope / expected-pre-writer / nonblocking-info / mixed / not-applicable` |
| validator_warnings_evidence | `<finding ids or not-applicable>` |
| validator_info_count | `<integer>` |
| validator_info_evidence | `<finding ids or not-applicable>` |
| source_row_counts | `<scope-id>=<count> через ;, например 05=27>` |
| source_restore_provenance | `<source path/checkpoint or not-applicable>` |
| source_restore_sha256 | `<SHA-256 or not-applicable>` |
| active_scope_ids | `<обязательный allowlist: один id или список через запятую, например 02, 05>` |

## Снимок TC-review

Заполняй раздел только после `tc_review`. Он фиксирует текущий review и не
заменяет полные `review-findings.md` / `review-independence.md`.

| Область | Вердикт | Число блокирующих замечаний | Задача или сессия ревьюера | Среда выполнения ревьюера |
| --- | --- | --- | --- | --- |
| `<scope-slug>` | `tc-accepted / tc-changes-required` | `<integer>` | `<separate Codex session id>` | `codex-thread` |

## Переходы по областям

| Область | Вердикт | Следующий переход | Противоречие источнику | Решение по TC со статусами | Причина |
| --- | --- | --- | --- | --- | --- |
| `<scope-slug>` | `matrix-not-created / matrix-created-pending-review / matrix-accepted / matrix-changes-required / round-cap-reached / blocked` | `<enum from Summary>` | `yes / no / not-applicable` | `write-with-statuses / block-source-contradiction / not-applicable` | `<причина на русском>` |

## Действия текущего этапа

- `<Только действия текущего этапа. Не повторяй здесь предыдущую историю.>`

## Контекст предыдущих этапов

- `<Факты предыдущих этапов, которые объясняют текущее состояние.>`

## Контроль версии кода

| Поле | Фактическое значение |
| --- | --- |
| code_branch | `<current branch>` |
| code_commit | `<40-char SHA>` |
| version_gate_status | `passed` |

## Правила

- Поля перечислений содержат только значение перечисления, без поясняющего текста.
- До создания матрицы используй `matrix-not-created`; после создания и до независимого review — `matrix-created-pending-review`. После исчерпания лимита review при `source_contradiction = no` используй `write-with-statuses`; при `yes` — `block-source-contradiction`.
- Перед созданием отдельной сессии ревьюера выполни `python scripts/practical_review_preflight.py` с выбранными scope, mode и `--check-only`. При `allowed: true` немедленно укажи `review_launch_preflight_status = check-only-allowed`, `review_launch_preflight_receipt = not-applicable` и краткое `review_launch_preflight_evidence`. Этот результат не является receipt и не разрешает менять controller-owned state.
- Только после успешного check-only один раз запусти ту же команду с `--output` и получи `review-launch-preflight.json`. Тогда укажи `review_launch_preflight_status = allowed`, ссылку на receipt и направь отдельную Codex-сессию reviewer. Между этими командами controller-owned state не меняй.
- Если `--check-only` или materialized preflight заблокирован, не сохраняй blocked `review-launch-preflight*.json`, не создавай reviewer artifacts и не запускай reviewer. Сохрани причину в этой сводке и `workflow-state.yaml`.
- `execution_working_directory` совпадает с `code_root`. Все ссылки на активные артефакты текущего scope из `work/practical/` должны вести только в `work/practical/<scope_slug>/`; прошлые результаты храни в `history/` и не используй как активный вход.
- После каждого controller-state repair обновляй generated validator fields командой `scripts/refresh_practical_stage_summary.py`; затем выполняй package-root validation. Ошибки текущего scope блокируют следующий этап, внешние ошибки классифицируй отдельно.
- `next_safe_step`, причина перехода и оба narrative-раздела пиши по-русски. Английскими остаются только технические идентификаторы, пути и согласованные enum-значения.
