# Lean-v2 Iteration

`lean-v2` — условный deterministic-first режим `ft-test-case-iteration` для уже
выбранного FT-пакета и подтверждённого bounded scope. Он сокращает критический
путь до:

1. проверки hash-bound source packet;
2. детерминированных evidence cards;
3. детерминированных test intents для простых свойств;
4. одного writer-вызова только для сложных карточек;
5. одного независимого reviewer-вызова;
6. production gate и shadow release без изменения canonical.

Это production-маршрут, а не benchmark. Он не читает benchmark configs, старые
test cases, review-cycle history или generated work другого запуска.

## Граница режима

Режим разрешён, когда:

- FT-пакет и внешний scope уже выбраны;
- DOCX и XHTML зарегистрированы с SHA-256; XHTML обязателен;
- source packet содержит атомарные `OBL-*` / `ATOM-*` с точным source row;
- blocking gaps уже разрешены либо их карточки не выдаются за исполнимые кейсы;
- общее число evidence cards не превышает 64, сложных writer cards — 32;
- один writer и один reviewer достаточны.

Если атомаризация ещё не выполнена, scope размыт, source rows не hash-bound или
лимиты превышены, не подгоняй вход под `lean-v2`: вернись в `ft-scope-analyzer`
либо используй standard route.

`lean-v2` сознательно не извлекает весь DOCX заново. Подготовка source packet —
upstream responsibility подтверждённого scope. Это не разрешает вручную
пересказывать ФТ: каждая карточка обязана иметь exact bounded source text,
locator, source row, requirement codes при наличии, `ATOM-*` и `OBL-*`.

## Source packet v1

Минимальная структура:

```json
{
  "schema_version": 1,
  "ft_slug": "example-ft",
  "scope_slug": "client-addresses",
  "section_id": "4.2",
  "package_id": "WP-01",
  "tc_prefix": "ADDR",
  "base_preconditions": [
    "Открыть карточку заявки и блок «Адреса клиента»."
  ],
  "source_files": [
    {
      "role": "docx",
      "path": "fts/example-ft/source/requirements.docx",
      "sha256": "<64 lowercase hex>"
    },
    {
      "role": "xhtml",
      "path": "fts/example-ft/source/requirements.xhtml",
      "sha256": "<64 lowercase hex>"
    }
  ],
  "dictionaries": [
    {
      "dictionary_id": "DICT-001",
      "closed": true,
      "values": ["Значение 1", "Значение 2"]
    }
  ],
  "source_rows": [
    {
      "source_row_id": "SRC-001",
      "field_or_action": "Регион",
      "source_ref": "requirements.xhtml /table[1]/tr[2]",
      "source_locator": "/table[1]/tr[2]",
      "bounded_source_text": "<точный ограниченный текст строки>",
      "requirement_codes": ["BSR 125"],
      "obligations": [
        {
          "obligation_id": "OBL-001",
          "atom_id": "ATOM-001",
          "template": "visibility",
          "priority": "высокий",
          "inputs": {}
        }
      ]
    }
  ]
}
```

Все `source_files` должны находиться внутри `repo_root`. Runner проверяет SHA-256
до работы и повторно при final reconciliation. Отсутствующий XHTML, hash drift,
дублирующиеся `SRC/ATOM/OBL` или неизвестный справочник блокируют run до модели.

## Шаблоны

| `template` | Обязательные inputs | Исполнение |
| --- | --- | --- |
| `visibility` | нет; optional `steps`, `expected_result` | deterministic |
| `default` | `value` | deterministic |
| `editability` | distinct `initial_value`, `new_value` | deterministic |
| `dictionary` | `dictionary_id` закрытого справочника | deterministic |
| `positive-input` | concrete `value` | deterministic |
| `requiredness` | `trigger_step`; exact `expected_result` либо `missing_oracle_question` | deterministic executable или calibration candidate |
| `optionalness` | `trigger_step`, `missing_oracle_question`; optional exact `expected_result` | deterministic calibration candidate для source-backed `required = no` |
| `calibration-negative` | concrete `invalid_value`, `missing_oracle_question` | deterministic calibration candidate |
| `behavior` | `title`, concrete `steps`, observable `expected_result` | deterministic explicit behavior |
| `complex` | bounded `writer_context` | один writer call |

Общие `preconditions` и `postconditions` можно переопределить внутри `inputs`.
Закрытый dictionary-кейс проверяет все и только перечисленные значения. Для
requiredness/negative restriction с неизвестной UI-реакцией кандидат остаётся в
общем наборе с canonical calibration markers; он не называется execution-ready.
То же правило применяется к `optionalness`: отсутствие обязательности является
отдельным source-backed свойством и не считается покрытым одним лишь отсутствием
requiredness-кейса.

## Model boundary

Writer получает только `complex` cards. Старые тест-кейсы ему не передаются.
Writer возвращает один intent на карточку либо явный `unresolved_cards`; он не
владеет `TC-ID`, `ATOM`, `OBL`, `SRC`, requirement codes, traceability,
приоритетом, предусловиями или постусловиями. Runner переносит source-owned
setup/lifecycle из packet, назначает `TC-ID` и добавляет трассировку сам. Любой
пропуск карточки, повторное владение, traceability identifier или попытка
переопределить runner-owned поле в writer output блокирует run.
`prepare-only` применяет к runner-owned предусловиям тот же production-runtime
preflight, что и полный gate, поэтому невоспроизводимый setup останавливается до
первого model-вызова.

Reviewer запускается свежим tool-free process после полного production gate.
Он получает все evidence cards, нормализованные intents, точный draft и его
SHA-256. `accepted` допустим только при одном результате для каждой карточки,
статусе `covered` и отсутствии error findings. Reviewer не редактирует draft.

Codex backend работает с `sandbox=read-only`, отключёнными model-tool surfaces и
strict JSON schema. Каждая стадия — fresh ephemeral process. По умолчанию нет
application-level model timeout; deadline включается только явным
`--model-timeout-seconds`.

## Shadow release и граница publication

Результат всегда выпускается как shadow output в immutable run directory.
Canonical не меняется. Прямая publication намеренно отсутствует: по общему
контракту проекта promotion-capable workflow обязан пройти compiler contract v3,
полный source assertion manifest и независимый exact-digest source receipt.
Подключение к этому promotion boundary выполняется отдельной квалификационной
итерацией и не имитируется упрощённым publisher-ом.

Новый retry всегда использует новый `output-dir`. Непустой каталог повторно не
используется.

## Артефакты

- `source-packet.normalized.json`;
- `source-files.receipt.json`;
- `evidence-cards.jsonl`;
- `coverage-plan.json`;
- `evidence-access-report.json`;
- `writer-request.json` и, если writer вызван, `writer-response.json`;
- `test-intents.json`;
- `shadow-test-cases.md`;
- `production-gate.json`;
- `reviewer-request.json`;
- `review-result.json`;
- `iteration-summary.json`;
- `failure-diagnostic.json` при terminal failure.

Terminal statuses: `prepared`, `accepted-shadow`,
`blocked-writer-unresolved`, `blocked-production-gate`, `review-*`,
`blocked-contract`, `failed-infrastructure`.

`iteration-summary.json` фиксирует полное wall time, последовательные phases,
явный interphase remainder, attempts и tokens. Недоступные токены записываются
как `unavailable`, а не `0`.

## Запуск

Подготовить cards и запросы без модели:

```powershell
python scripts/run_lean_v2_iteration.py `
  --repo-root . `
  --source-packet <source-packet.json> `
  --output-dir <fresh-run-dir> `
  --prepare-only
```

Shadow writer/reviewer run без model timeout:

```powershell
python scripts/run_lean_v2_iteration.py `
  --repo-root . `
  --source-packet <source-packet.json> `
  --output-dir <fresh-run-dir>
```

`--writer-response` и `--reviewer-response` предназначены для offline
qualification строгих контрактов. Они не доказывают live model quality.
