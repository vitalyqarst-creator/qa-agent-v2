# Prepared Source Assertion Reviewer Runtime Profile

Этот профиль используется только каноническим runner-ом независимого
`source_assertion_review`. Он не заменяет доменные правила
`source-assertion-semantic-rule-card.md` и не разрешает reviewer-у изменять
source model.

## Входной контракт

Runner до запуска модели обязан:

- получить один уже прошедший source-gate receipt для точного digest manifest-а,
  созданный одной фактической validation invocation через
  `scripts/validate_source_assertion_gate.py`; consumer exact-проверяет schema,
  пять canonical checks и все counts;
- разрешить и проверить `codex exec` через общий backend dispatcher;
- exact-сверить четыре mandatory scope artifact: typed
  `source-row-inventory.md` с `manifest.source_rows`, semantic digests
  extraction spec/baseline с manifest и path/SHA coverage gaps с manifest;
- сформировать полный evidence registry: каждый path из `sources`,
  `evidence_sources`, `mockups` представлен ровно один раз, без extras;
- hash-bind каждый вход и сохранить context report;
- создать строгую JSON Schema receipt v6.

`sources` передаются как runner-owned bounded source rows после канонической
проверки manifest-а. Небольшой UTF-8 `evidence_source` передаётся напрямую.
DOCX/PDF или большой UTF-8 source допускается только через один typed bounded
extract: descriptor связывает exact source path/SHA, extractor method, locator,
literal fragment и SHA fragment-а; runner повторно извлекает registered bytes и
проверяет literal membership. Arbitrary prose extract, unknown subject,
duplicate subject/mode, missing registered path и незарегистрированный extra
терминально блокируют запуск модели. Mockups передаются как прямые hash-bound
`--image` attachments; если capability probe не подтверждает `--image`, model
call не начинается.

Descriptor строится детерминированно через
`scripts/build_bounded_source_evidence_extract.py` из selection spec v1:

```json
{
  "version": 1,
  "source_path": "fts/pkg/source/main.pdf",
  "extraction_method": "pdf-page-literal-fragments-v1",
  "selections": [
    {"source_locator": "page:32", "exact_source_text": "<literal pypdf fragment>"}
  ]
}
```

Разрешённые methods: `pdf-page-literal-fragments-v1`,
`docx-xml-literal-fragments-v1` (`source_locator` описывает место, literal
проверяется по `word/document.xml`) и `utf8-literal-fragments-v1`. Один output
descriptor описывает один registered `evidence_source`; combined extract для
нескольких source paths запрещён.

Если у одной из трёх boundary classes нет manifest row, для registered UTF-8
`source` дополнительно требуется source-verified bounded extract с уникальным
literal fragment на каждую пустую class. Runner сам materialize-ит готовый
canonical exclusion locator `path#text-sha256=...`; модель не вычисляет hash и
не использует baseline candidate hash вместо него. Такой source extract
запрещён, когда все boundary classes уже представлены rows.

Canonical reviewer CLI принимает `--source-row-inventory`,
`--source-row-extraction-spec`, `--source-row-baseline` и по одному
`--bounded-extract` на каждый DOCX/PDF/oversize UTF-8 evidence source. Старый
универсальный `--evidence-file` не поддерживается: arbitrary extras запрещены.

Модель получает только inline basis. Ей запрещены shell, MCP, web, чтение
репозитория, повторный запуск extractor-а, validator-а или source gate. Любой
tool/command event делает попытку терминально невалидной; retry внутри того же
запуска запрещён.

## Проверка

Reviewer независимо оценивает все assertions и все три boundary context class
по тринадцати dimensions из semantic rule card. Производные ledger, design plan
и test cases не входят в basis и не могут служить доказательством.

Approved clarification допустим только при одновременной проверке:

- hash-bound evidence source с ролью `approved-clarification`;
- typed записи `clarifications[]`;
- resolved gap с точным `approved-clarification:CLR-*` resolution;
- clause-level binding к точному answer digest.

`accepted` допустим только при полностью verified assertion set, source
inventory и scope boundary. Иначе решение — `changes-required` с конкретным
`required_change`; reviewer не исправляет manifest.

Все механические invariants receipt v6 reviewer получает из компактной
`source-assertion-review-receipt-v6-rule-card.md`; schema-valid JSON, который
нарушает aggregate/equality/boundary правила канонического post-validator-а, не
считается допустимым ответом.

## Выходной контракт

Runner принимает только один JSON receipt version 6, валидирует его один раз
каноническим validator-ом относительно точного manifest digest и завершает
stage без повторного model call. `changes-required` является корректным
терминальным результатом, а не основанием для скрытого R2.
