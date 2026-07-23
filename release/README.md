# Release Profiles

Проект использует один исходный commit и два детерминированных профиля сборки.

## Qualification

`qualification-manifest.json` включает runtime, инструкции, тесты и curated
benchmark configs. Сырые прогоны, diagnostics, stage/review work и оригинальные
AutoFin DOCX/XHTML/PDF/mockups исключены. Активный `PostFinal-v2` и используемые
макеты связаны с профилем только путями и SHA-256; сами файлы остаются локальными.
Небольшие воспроизводимые DaData-fixtures входят в qualification-профиль.
Проверка локальных входов выполняется с `--require-local-inputs`.
Для запуска offline quality proof используй обычную репозиторную dev-среду после
`uv sync`; production installation может исключить dev group.
Live-доказательство downstream-маршрута и последующая детерминированная правка
зафиксированы в `release/qualification-contact-persons-v28-live.json`. Receipt
явно отделяет инфраструктурно корректный v28 от найденного после review дефекта
кейса и офлайн-подтверждения исправления v32. Локальные attempts и AutoFin inputs
в release не включаются.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/qualification-manifest.json `
  --check-only `
  --require-local-inputs
```

## Production

`production-manifest.json` — точный allowlist import closure для публичного
`ft-agent run`. Это намеренно узкий downstream runtime: он принимает уже
независимо принятый, hash-bound source package и выполняет только
детерминированную schema-v2 iteration с одним reviewer. Discovery исходного ФТ,
выбор scope, построение source evidence и independent source review в bundle не
входят. Эти prerequisite-этапы пока остаются в qualification/development среде.

В bundle входит только `ft-test-case-iteration`, его компактные runtime
references, environment probe и instruction resolver. Единственный instruction
entrypoint — `references/agent/production-instruction-loading.md`; он загружает
самодостаточную `production-global-rules.md`, поэтому development-only корневой
`AGENTS.md` и legacy control plane в production не копируются.

`ReviewerEvidencePack` v2 строится самим runtime из отдельно квалифицированного
scope package. Зарегистрированные mockups могут входить во внешние runtime inputs
этого package; их изображения и hash-bound metadata передаются независимому
reviewer через evidence pack после проверки hash, размера, decoded format,
структуры и полной декодируемости. Pack содержит вычисленный bounded semantic
parity proof для каждого XHTML-backed literal элемента с DOCX и PDF (для
DOCX — с сохранением document order, section region и one-to-one table identity;
для разбитых табличных строк PDF — по упорядоченным cell anchors и точным
непересекающимся prefix/suffix-continuations соседних страниц в минимальном
code-bounded page span; склеенная короткая ячейка допускается только как точное
заполнение промежутка между двумя доказанными соседними fragments, без общего
ослабления token boundaries и без заявления о геометрии таблицы), а также
отдельную точную сверку PDF requirement codes, полный зарегистрированный
coverage-gap artifact, supporting cross-row
bindings, отдельные role-tagged design-support chains для sibling obligations в
setup/action/cleanup и честную provenance-классификацию справочников. Для явных exclusive
allowed-set правил pack также
передаёт детерминированную проекцию отдельных недопустимых классов, не выводя из
ограничения неизвестный UI-отклик. Сами FT-файлы, изображения и mockups в
production bundle не копируются.

Branch fixtures закрытого справочника принимаются только как exact-token
подмножество полного qualified value set с per-value source-row bindings.
External-dynamic/DaData fixtures сохраняют реальные hash-bound response,
verification receipt и lifecycle catalog row; pack передаёт reviewer точные
request/expected response и не запускает routine live revalidation.

Promotion принимает только v2 request и не доверяет self-declared pack:
adapter повторно загружает typed evidence basis, квалифицирует текущие
зарегистрированные файлы и перестраивает весь pack перед выдачей eligibility.

Профиль не содержит `evals/`, tests, FT inputs, work/history, benchmarks,
overnight/incremental/standard controllers, dispatcher/cycle-state compatibility,
UI automation, source qualification skills, legacy writer/reviewer skills и offline quality proof. Эти
инструменты остаются только в qualification-профиле. Публичный production CLI
содержит только `ft-agent run`; evidence pack является частью этого существующего
маршрута и не добавляет promotion или новый entrypoint.

```powershell
python scripts/build_release_bundle.py `
  --manifest release/production-manifest.json `
  --output dist/ft-test-case-agent-production
```

Output directory обязан быть новым. В корне bundle создаётся
`release-manifest.json` с SHA-256 каждого файла и общим `tree_sha256`.

Benchmark profile не превращается в отдельную кодовую ветку. Production bundle
строится из того же commit/tag, поэтому исправления runtime и quality gates не
расходятся между qualification и production.
