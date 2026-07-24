# Source-qualified iteration

Этот reference задаёт короткий production-маршрут `ft-test-case-iteration` для
уже квалифицированного bounded scope. Историческое имя instruction scenario —
`iteration.lean_v2`; публичная точка запуска — `ft-agent run`.

Маршрут не является benchmark. Он не передаёт reviewer старые тест-кейсы,
benchmark configs, результаты прошлых попыток и произвольные пути из командной
строки.

## Граница ответственности

До запуска должны существовать:

- package-local `scope-registry.json` с выбранным scope, структурной XHTML-
  границей, полным набором источников и стабильным `tc_prefix`;
- DOCX как source of truth, XHTML как обязательный машиночитаемый источник и
  PDF, если он объявлен;
- source evidence со source-assertion manifest v4 и независимым accepted review
  receipt на точный digest, а также immutable semantic-design compiler
  projection со ссылками и хэшами исходных semantic artifacts;
- compiler-v3 obligations;
- accepted semantic projection, из которой runner сам строит маленький design
  context.

Если любого входа нет или он stale, заверши попытку как `blocked-input`. Повторная
квалификация выполняется вне этого bundle в development/qualification среде;
нельзя заменять её ручным пересказом требований или брать старый TC suite как
источник.

## Единственный публичный запуск

```powershell
ft-agent run `
  --config fts/<ft-slug>/work/<handoff>/run-config.json `
  --output-dir fts/<ft-slug>/work/iterations/<new-attempt-id>
```

`run-config.json` имеет закрытую schema-v2 основу. Базовые обязательные поля:

```json
{
  "schema_version": 2,
  "registry": "fts/example-ft/scope-registry.json",
  "ft_root": "fts/example-ft",
  "scope": "confirmed-scope",
  "source_evidence": "fts/example-ft/work/handoff-001/source-evidence.md",
  "obligations": "fts/example-ft/work/handoff-001/obligations.json"
}
```

Schema v1 с явным `derivations` остаётся только compatibility API для старых
внутренних handoff. Новые production-конфиги используют schema v2.

Для новых production попыток добавляй `writer_mode: model-runtime-prose`.
Допустимые route-поля: `writer_mode`, `mockup_label_aliases`,
`revision_findings`. Если `writer_mode` отсутствует, runner использует
compatibility default `deterministic-first`. Он не принимает `ft_slug`, design
context, `tc_prefix`, source/canonical allowlists, output status, promotion
target или готовый файл derivations. Slug и prefix выводятся из `ft_root` и
registry; защищаемые sources — из accepted manifest и registry; canonical
baseline — из всех `test-cases/**/*.md` выбранного FT-пакета. Typed derivations
и design context автоматически строятся из принятого manifest, obligations и
hash-bound semantic projection и сохраняются внутри immutable attempt.

## Последовательность

Runner в одном процессе и одном immutable attempt:

1. загружает закрытый config и фиксирует хэши всех run inputs;
2. резолвит только выбранный scope, чтобы дефект другого scope не блокировал
   текущий;
3. заново компилирует XHTML boundary и candidate set;
4. требует точного равенства registry и manifest по path, bucket, role и
   актуальному SHA-256, включая DOCX/XHTML/PDF/support/mockups;
5. проверяет accepted source-review receipt и obligations, затем автоматически
   строит и hash-bind-ит typed derivations из semantic projection;
6. строит и полностью валидирует coverage graph;
7. строит source-bound deterministic seed cases;
8. в `model-runtime-prose` вызывает writer ровно один раз для runtime prose:
   writer не может менять `TC-ID`, traceability, priority, package или lifecycle;
9. детерминированно собирает весь Markdown и запускает production gate;
10. детерминированно собирает полный `ReviewerEvidencePack` v2 из буквальных
   элементов подтверждённого scope, verified DOCX/XHTML/PDF parity, полного
   зарегистрированного coverage-gap artifact, supporting cross-row bindings,
   role-tagged design-support chains для sibling obligations в setup/action/cleanup,
   релевантных справочников, normalized projection, полного draft и
   зарегистрированных mockup attachments, затем
   вызывает ровно одного независимого reviewer;
11. повторно проверяет run inputs, source/canonical hashes и пишет terminal
    summary.

Scopes выполняются последовательно. Внутреннего retry и продолжения испорченной
попытки нет; повтор всегда получает новый output directory.

## Model boundary

В `deterministic-first` единственный model stage — reviewer. В рекомендуемом
`model-runtime-prose` есть два model stage: writer для runtime prose и reviewer.
Writer запускается до suite gate и получает только source-bound seed cases,
локальный source/obligation projection, mockup label aliases и optional
`revision_findings`; старые TC и benchmark/history ему недоступны. Runner
валидирует, что writer вернул ровно все case keys, не изменил runner-owned поля
и не использовал stale FT label вместо точного visible mockup label.

Reviewer запускается в свежем tool-free process после полного suite gate и
получает hash-bound `ReviewerEvidencePack` v2:
буквальный текст всех элементов scope, включая строки без obligations,
структурный контекст, полный релевантный срез справочников, normalized
projection, полный coverage-gap artifact, supporting bindings, весь draft и
только зарегистрированные scope mockups. Файлы изображений проходят повторную
проверку hash/size, соответствия suffix/decoded format, структуры и полной
декодируемости каждого frame до `--image`. Буквальный
source имеет приоритет над projection; pack не содержит старые TC,
benchmark/history. Reviewer не редактирует результат и не может принять warning
или finding как `accepted`. Runner обязан зафиксировать ровно один reviewer
request/receipt; отсутствие или повторный вызов блокирует acceptance.
Closed-dictionary branch fixtures подтверждаются per-value qualified source
bindings; external-dynamic fixtures используют зарегистрированные response,
verification receipt и lifecycle catalog evidence без routine live revalidation.

Acceptance policy внутри `ReviewerEvidencePack` v2 имеет отдельную версию
`reviewer_policy_version = 2`. Она требует falsification checks для false pass,
false fail, ошибочной failure attribution и пропущенного source-backed trigger,
с typed per-case receipt для всех четырёх probes. Каждый probe фиксирует точные
`binding_role`, `obligation_id` и `binding_item_index` (`-1` для primary); support
receipt обязан ссылаться на конкретный materialized item. Для outcome `passed` trigger/step и oracle
берутся из фактического TC, а не только из source obligation; source-only basis
может обосновывать `finding`, но не sign-off. Probe с outcome `finding` требует
concrete witness и `test_case_finding` на той же evidence chain; live reviewer не
может использовать legacy-only outcome `not-recorded`. Прямые source/TC-design/digest/
binding-integrity дефекты, доказанные артефактами, не требуют гипотетического
контрпримера. V2 request/receipt,
созданный без этой policy version или с другим acceptance contract, несовместим
с текущим promotion: его нельзя дополнять задним числом или replay-ить, нужен
новый immutable attempt.

Один probe может иметь несколько `test_case_findings` по разным точным chains:
receipt anchor-ит хотя бы одну, а каждый дополнительный finding сохраняет тот же
`falsification_probe` и свою полную зарегистрированную chain.

Offline legacy-adapter сохраняет расширенную instance schema вместе с
адаптированным response, поэтому `schema_sha256` в stage receipt воспроизводимо
проверяет именно schema, допускающую legacy-only `not-recorded`. Live schema
остаётся закрытой и такого outcome не допускает.

Для promotion допустим только v2 request. Adapter повторно загружает отдельный
`reviewer-evidence-basis.json`, квалифицирует зарегистрированные файлы и
детерминированно перестраивает весь pack и test-case mappings. Совместно
перехэшированный, но не выводимый из basis пакет promotion не проходит.

Если полный pack превышает reviewer context limit, runner ничего не усекает и
завершает attempt как `blocked-reviewer-context-too-large` с рекомендацией
декомпозиции внешнего scope. Reviewer sharding и retry не выполняются.

Reviewer проверяет только переданные condition/action/fixture/state axes и не
требует гипотетических состояний. Если before/after states явно присутствуют в
проекции, пропущенное состояние остаётся finding. Исполнимый кейс получает
`covered`; честно помеченный calibration-кандидат — `calibration-pending` после
проверки трассировки, calibration question и отсутствия придуманного oracle.
Одна лишь неисполняемость calibration-кандидата не является finding.

Недоступный UI oracle не превращается в догадку. Calibration candidate остаётся
в том же suite, но явно помечается как неисполняемый до UI-калибровки.

## Immutable и publication boundary

- `output-dir` обязан быть новым child path под `fts/<ft-slug>/work/`;
- модель работает без hard application timeout по умолчанию;
- canonical, workflow state и source files не изменяются;
- успешный terminal status — `accepted-shadow` либо
  `accepted-with-calibration-pending`, не `signed-off`;
- `accepted-with-calibration-pending` всегда имеет `promotion_eligible=false`
  и `non_promotable_reason=calibration-pending`;
- promotion не входит в `ft-agent run`.

Promotion выполняется вне этого downstream bundle отдельной development-
транзакцией только для неизменившегося
`accepted-shadow` без pending calibration: повторно проверяются graph, production gate, reviewer receipt,
полный canonical baseline и source hashes. Ручная правка lifecycle или прямая
запись в canonical запрещены.

## Результаты и измерение

В корне attempt сохраняются:

- `scope-compilation/`;
- `bindings/accepted-coverage-contract.json`;
- `run-input-receipt.json`;
- `graph/coverage-graph.json`;
- `context/design-context.json`;
- `iteration/` с prompts, receipts, shadow draft, gate и review;
- `iteration/reviewer-evidence-pack.json` с полным bounded evidence;
- `terminal-summary.json`;
- отдельный diagnostic для terminal failure.

Summary охватывает загрузку config, scope compilation, source binding, graph,
design context, единственный reviewer stage и final reconciliation. Для reviewer
указывай wall time, attempts, input/output artifact count и bytes, а токены —
только как неотрицательные целые либо `unavailable`. Токены root orchestration
всегда `unavailable`, никогда не `0`.
