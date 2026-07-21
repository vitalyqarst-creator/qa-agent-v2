# Lean Production Workflow

Этот профиль сокращает полное пользовательское время от начала работы с уже
выбранным FT-пакетом до опубликованных тест-кейсов. Он не является ослабленным
quality mode: source-first lineage, независимые semantic reviews и все
детерминированные gates остаются обязательными.

## Eligibility

Профиль `lean-production` разрешён, когда одновременно выполнены условия:

- FT-пакет выбран, main DOCX и XHTML доступны, scope локализуется одним разделом
  или непрерывным bounded-фрагментом;
- не более 12 source rows, 10 testable assertions и 14 ожидаемых TC;
- один внутренний package достаточен;
- нет нескольких разнородных интеграций, больших справочников или неразрешённого
  blocking gap, который требует ответа пользователя;
- все нужные mockup-файлы можно открыть до фиксации UI hints.

Если хотя бы одно условие не выполнено, используй обычный полный маршрут. Не
разбивай большой scope искусственно ради попадания в лимиты.

До detailed scope call выполни детерминированный `scope execution profile`
assessment после dependency preflight. Входные `scope_execution_facts` должны
явно содержать оценки assertions, TC и packages, тип bounded scope, признаки
разнородных интеграций/большого справочника и готовность mockups. Неизвестный
критерий означает `standard-production`, а не optimistic lean. Число уникальных
BSR/GSR-кодов сохраняется только как diagnostic и не заменяет оценку assertions
или TC. `standard-production` не запускается через монолитный detailed v1.
Его production route: один compact boundary-v2 call → один отдельный
semantic-design author call → deterministic materialization → независимый
source review. Boundary-v2 сам по себе не разрешает writer.

Assessment читает только hash-bound prepared context: `source_cache` и
`bounded_context_sha256` обязательны до profile routing. Явно запрошенный, но
неподходящий `lean-production` fail-closed нормализуется в `standard-production`;
сочетание eligible lean с compact contract v2 запрещено как несогласованный
маршрут.

## User-visible critical path

Одна пользовательская задача должна пройти цепочку без ручных пауз между
стадиями:

1. hash-bound source preparation и scope execution profile assessment;
2. scope route: detailed semantic author для eligible lean либо boundary-v2 и
   отдельный semantic-design author для standard;
3. deterministic materialization и один независимый source-assertion review;
4. deterministic compile/preflight;
5. один writer session;
6. один независимый reviewer session;
7. deterministic promotion при accepted review.

Модельные границы между boundary, semantic author, source reviewer, writer и
TC reviewer сохраняются. В standard route boundary авторитетен для
semantic author: scope summary, include/exclude, row order/dispositions, requirement
codes, dependencies, gaps и mockup locators должны совпасть точно. Текущий
bridge fail-closed отклоняет boundary с gaps или unresolved/blocking
dependencies. Нельзя синтезировать assertions/ATOM/OBL из одних row
dispositions.

Каждая модельная стадия standard route вызывается один раз; failure даёт
terminal result без retry, монолитного-v1 fallback или optimistic lean. Этот
контракт не доказывает live quality или ускорение; live-run и benchmark в этой
итерации не выполнялись.
Отдельные пользовательские задачи, просьбы «продолжить» и ожидание подтверждения
между уже разрешёнными стадиями не требуются.

Канонический one-command entrypoint полного standard route —
`scripts/run_standard_production_iteration.py`: он последовательно запускает
bridge и существующий source-review → compile → writer → reviewer → promotion
runner. `scripts/run_standard_scope_bridge.py` является узким диагностическим
entrypoint только до atomic handoff; его успешное завершение само по себе не
означает выпуск тест-кейсов.

```powershell
python scripts/run_standard_production_iteration.py `
  --repo-root . `
  --context <prepared-bounded-context.json> `
  --runtime-dir <fresh-runtime-dir> `
  --handoff-dir <fresh-stage-handoff-dir> `
  --cycle-dir <fresh-review-cycle-dir> `
  --final-artifact <canonical-test-case-file> `
  --timer <caller-owned-performance.json> `
  --measurement-mode observational
```

`package_id` не переопределяется CLI: wrapper берёт его из immutable prepared
context, сверяет с materialized semantic design и только затем передаёт
downstream compiler.

## Production targets and observational baseline

Таблица ниже задаёт production targets, но не ограничивает диагностический
baseline. Для фиксации фактического текущего времени запускай scope stage с
`--measurement-mode observational` либо `--no-timeout`: `timeout_seconds = null`,
runner и capability resolver не создают model/probe deadline и ждут естественного
terminal result. В этом режиме нет hard stop по полному пользовательскому времени.
Отдельный bounded cleanup deadline начинается только после завершения или
прерывания дочернего процесса и ограничивает ожидание drain-потоков; он не
ограничивает model call даже в observational mode. Cleanup deadline и его исход
фиксируются в lifecycle evidence. Порядок model lifecycle проверяется по
порядковым номерам JSONL-событий, а timestamps используются только для времени.
Явный `--timeout-seconds` с observational mode является ошибкой конфигурации.

Перед каждым model-only scope/source-review вызовом resolver проверяет абсолютный
путь и версию Codex, наличие каждого имени отключаемой feature в локальном
registry и передаёт прямые `--disable` для plugin/app, shell, browser/computer,
image-generation, multi-agent и других model-tool surfaces. Runtime event guard
с единым canonical перечнем tool-item types остаётся вторым fail-closed рубежом
для scope analyzer, source reviewer и schema canary.

Целевой budget для eligible scope:

| phase | target | hard stop |
| --- | ---: | ---: |
| scope materialization + gates | 90 s | 180 s |
| source assertion review | 90 s | 900 s safety limit |
| writer | 90 s | 600 s safety limit |
| TC reviewer | 90 s | 600 s safety limit |
| promotion/reporting | 15 s | 30 s |
| full user wall-clock | 5 min | 8 min |

`full_user_wall_ms` измеряется от `request_started_epoch_ms`, зафиксированного
orchestrator-ом до маршрутизации и первого чтения, до terminal result, включая
preflight, ожидание model calls, валидацию, запись файлов, promotion и recovery.
`instrumented_wall_ms` отдельно показывает интервал после фактического запуска
таймера, а `pre_timer_wall_ms` — задержку между получением запроса и таймером.
Если `request_started_epoch_ms` недоступен, record обязан иметь
`measurement_coverage: timer-start`; такое значение нельзя называть полным
пользовательским временем. Сумма только model durations также не считается
полным временем пользователя.

Один deterministic repair разрешён только для локального format/schema defect и
только внутри оставшегося hard budget. Transport/schema failure до model start не
запускает повторный live canary в production-задаче: верни конкретный terminal
result. Архитектурная отладка и широкие regression suites выполняются отдельно от
production critical path.

## Persistent artifacts

В успешном production-run сохраняй только артефакты, которые доказывают source lineage,
semantic decisions или terminal result:

- `workflow-state.yaml`;
- `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`;
- `source-parity-check.md` при DOCX+PDF;
- `source-row-extraction-spec.json`, `source-row-baseline.json`,
  `source-row-inventory.md` для row-level scope;
- `mockup-visual-inventory.md` только при реально использованных mockups;
- boundary-v2 decision и `semantic-design-bridge-receipt.json` для standard route;
- `source-assertions.json`, source-gate receipt и accepted/rejected independent
  source-review receipt;
- compiler-required atomic/obligation/design projections;
- prepared package, draft, normalized reviewer result, compact performance record,
  promotion receipt и final TC.

Следующее сокращение audit-артефактов действует только для выбранного
`lean-production` route. В `standard-production` обязательные session/decision
logs создаются и связываются из `workflow-state.yaml` по общим каноническим
форматам. В успешном lean-run не создавай:

- `scope-execution-options.md` при однозначном downstream route;
- `*-session-log.md`, `agent-decision-log*.md` и `scope-agent-final.md`;
- `artifact-write/*` fragments для артефактов ниже обычных size/count thresholds;
- N/A-only negative/requiredness inventories;
- сохранённые dispatcher/CLI configs, schema probes и canary folders;
- raw stdout/stderr/events/schema/context после успешной нормализации receipt;
- дубликаты failed-cycle evidence в `workflow-state.required_inputs`.

При failure сохрани один компактный `failure-diagnostic.json` с phase, command,
elapsed time, error category и безопасным recovery action. Raw runtime evidence
может находиться во временной runtime-папке и не становится canonical handoff.

## Scope materialization rules

- Перед scope model call используй
  `scripts/prepare_bounded_scope_context.py`. Он выпускает один immutable
  content-addressed snapshot: prepared bounded context и XHTML baseline.
  Cache key зависит от canonical template и SHA-256 всех зарегистрированных
  DOCX/XHTML/PDF, package notes, support evidence, mockups и extraction spec, а
  также от версий source/parity/mockup declaration profiles. `mtime` не является
  доказательством актуальности.
- Manifest snapshot хранит отдельные digests source selection, XHTML baseline,
  parity, объявленных mockup metadata/locators и полного bounded context. Digest
  mockup-компонента сам по себе не доказывает визуальную инспекцию. Cache hit разрешён только
  после строгой проверки manifest, artifact hashes, extraction-spec binding и
  baseline contract. Повреждённая запись блокирует этап; она не принимается как
  miss. Изменение source при старом `candidate_id`, exact text или context class
  также блокирует этап и требует повторной фиксации scope.
- Cache builder не принимает semantic inputs из `test-cases/`,
  `work/stage-handoffs/` и `work/review-cycles/`. Bounded DOCX/PDF JSON evidence
  проверяется по registered source SHA и fragment SHA, затем встраивается в
  prepared context. Это hash-bound declared extract, а не повторная бинарная
  верификация самого извлечения из DOCX/PDF.
- До первого scope model call выполни deterministic dependency gap gate. Он
  проверяет неразрешённые ссылки на поля и справочники. Открытый blocking
  dependency завершает run как `blocked-input`:
  model call, writer и reviewer не запускаются. Не выводи alias из похожести
  названий или пересечения значений.
- Generic-примеры вида `поле "Дата"` внутри hash-bound rows с
  `source_context_class = document-global-constraints` и
  `field_or_action = Ограничение типа ...` не являются ссылками на отдельное
  UI-поле. Если такое глобальное правило применимо к выбранным полям, source-only
  template обязан пометить row как `context_relation_required = true` и объявить
  exact `expected_dependencies` relation с `resolution`, непустыми точными
  `target_source_row_ids` и literal `exact_source_fragments`. Prepared-context
  preflight блокирует model call, если обязательная context relation отсутствует.
  Boundary-v2 обязан оставить такую row в `context` и точно скопировать relation;
  произвольная подмена resolution/targets запрещена. `kind = field` не может
  использовать `source-provided`: concrete field обязан пройти exact `declared`
  или утверждённый `approved-alias` binding.
- Сразу после успешного dependency gate выполни scope execution profile
  assessment. Detailed v1 разрешён только для доказанно eligible
  `lean-production`; `>12` source rows или любой неизвестный eligibility-критерий
  маршрутизируют scope в `standard-production` без монолитного detailed-v1 call.
- При model timeout сохраняй stdout/stderr events потоково, фиксируй доступный
  usage и выпускай terminal receipt. Partial model output не является scope
  decision и не разрешает writer/reviewer routing.
- Загружай только prepared bounded source evidence и компактный instruction
  scenario `scope.bounded_production`; не перечитывай все references проекта.
- `scripts/codex_exec_bounded_scope_analyzer.py` сохраняет end-to-end совместимый
  detailed contract `v1` только после успешного lean eligibility gate; production
  default timeout равен `150 s`, а observational baseline не имеет timeout.
  Compact `v2` запускается только явно через `--contract-version 2`; его default
  timeout `120 s`. V2 сохраняет authoritative pre-fixed boundary/dispositions,
  exact expected dependency inventory, gaps и объявленные mockup locators, но не
  создаёт assertions, ATOM/OBL, planned TC или applicability matrix.
- V2 decision не передаётся materializer напрямую. В standard route отдельный
  semantic-design author создаёт строгий semantic-design contract v3, а
  deterministic bridge validator проверяет его exact binding к prepared context
  и v2 boundary. Только после этой проверки materializer строит совместимую
  deterministic projection и выпускает compiler-v3 handoff и bridge
  receipt. Нельзя синтезировать ASSERT/ATOM/OBL из row dispositions или считать
  ускорение одного v2-call доказательством ускорения end-to-end.
- Перед semantic-design author стандартный observation route выполняет
  capacity preflight. При `>10` included rows или `>16` всех source rows он
  строит complete/disjoint ownership shards. Field/approved-alias dependencies,
  source-context clarifications и gap evidence не разрываются; широкие
  integration/dictionary dependencies разрешено проецировать только с literal
  evidence и затем восстанавливать полностью. Каждый shard — отдельный strict
  mini-scope и одна fresh tool-free session без retry. После последовательных
  вызовов deterministic merge перенумеровывает локальные ASSERT/ATOM/OBL/TC,
  восстанавливает registries и проходит полный исходный semantic validator.
  Ошибка одного shard запрещает merge/materialization, но сохраняет plan,
  shard outputs, usage и wall time для нового immutable run.
- Semantic-design binding для dependency, исходящей из
  `context_relation_required` row, обязан покрыть executable assertion chain для
  каждого authoritative `target_source_row_id`, сохранив global row как exact
  supporting evidence. Одной цепочки для произвольного подмножества targets
  недостаточно; это предотвращает тихую потерю общих type/default правил.
- Atomic publication standard route имеет отдельный operational ownership
  contract: root wrapper создаёт один lowercase UUIDv4, bridge передаёт его
  materializer-у, а receipt сохраняет
  `publication_ownership_contract_version = 1` и точный
  `publication_owner_token`. Standalone bridge создаёт собственный UUIDv4.
  Recovery допустим только при совпадении token текущего invocation, context
  digest, SHA boundary/design и канонического digest фактически опубликованного
  `source-assertions.json`. Появление handoff-каталога само по себе ownership не
  доказывает. Legacy receipt без versioned ownership не восстанавливается как
  результат текущего запуска и требует rematerialization.
- Один correction patch допустим после aggregate validation. Повторные циклы
  «записать один файл → валидировать → исправить» запрещены.
- `scripts/write_artifact_sections.py` нужен только если ожидается более 30 atoms,
  более 20 TC или Markdown больше 20 000 символов. Сам факт наличия `WP-*` или
  `source-row-inventory.md` не включает chunked writing.
- Oracle inventories создаются только при source-backed restriction/requiredness
  signals. Нулевая applicability фиксируется в scope/design model без отдельного
  N/A-only файла.
- Один active transition prompt допустим до source reviewer. После accepted
  receipt runner строит writer/reviewer prompts из prepared package; отдельный
  prose prompt и dispatcher config не являются production evidence.
- До source-review model call runner выполняет `source-model-adequacy` preflight.
  Для каждого source-backed правила точной длины он требует раздельное evidence
  `N`, `N-1`, `N+1`: testable assertion с конкретным значением либо узкий
  class-specific `GAP-*`. Общий invalid-length assertion, буквенно-цифровой
  пример или один gap за обе границы не проходят gate. Отчёт сохраняется как
  `source-model-adequacy.json`; failure блокирует model stages, а не расходует
  ещё один source-review/writer/reviewer attempt.
- Жёсткий transport limit одного source-review prompt равен `320 KiB`, а soft
  shard target — `160 KiB` и не более `64` assertions. Эти limits source reviewer
  не изменяют instruction budget других стадий. До model call runner строит
  точный prompt-capacity plan. При превышении soft target или assertion cap
  assertions делятся на complete/disjoint shards по целым
  `source_row_id`: sibling assertions одной строки не разрываются, каждый shard
  получает тот же hash-bound evidence registry, а итоговый receipt v6 собирается
  и полностью валидируется только runner-ом. Каждый shard использует fresh
  tool-free session; это несколько attempts с `retry_count = 0`, а не retry
  испорченного review. Если одна строка не помещается в лимит или число shards
  превышает runner cap, source review завершается fail-closed до model call.
- Structured writer shards выполняются последовательно (`max_concurrency = 1`),
  чтобы измерение, evidence ownership и failure attribution оставались
  однозначными. Изменение concurrency требует отдельной квалификации runner-а.
- Обычный prepared writer сохраняет context ceiling `128 KiB`. Hash-bound
  targeted repair может использовать до `192 KiB`, только если набор ремонта
  помещается в single-session limit `14` TC. Это не ослабляет splice/hash checks:
  все неизменяемые секции защищены, а полный merged-набор проходит обычные gates
  и новый независимый review.

## Quality invariants

Lean-run не может быть `signed-off`, если отсутствует хотя бы один из invariants:

- DOCX остаётся source of truth, XHTML — mandatory extraction source, PDF — parity;
- baseline/source-row bijection и exact manifest freshness прошли;
- standard semantic design точно связан с prepared context и authoritative
  boundary-v2; scope drift отсутствует;
- каждый testable assertion имеет exact `ASSERT -> ATOM -> OBL -> TC` lineage;
- source reviewer независим от scope author;
- writer не выставляет sign-off;
- TC reviewer работает в отдельной read-only session и покрывает все obligations
  и routed dimensions;
- deterministic writer/reviewer/production-TC gates прошли;
- promotion выполняется только из accepted, digest-bound artifacts.

## Terminal report

Пользователю возвращаются final TC path, terminal status, количество TC, full user
wall-clock, durations и token usage каждой модельной стадии, а также краткое
сравнение с последним baseline. Количество созданных файлов указывается отдельно,
чтобы повторное разрастание процесса было заметно.
