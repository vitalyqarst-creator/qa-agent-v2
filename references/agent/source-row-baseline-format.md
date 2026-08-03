# Детерминированный baseline полноты строк XHTML

Этот контракт не позволяет `source-row-inventory.md` и source-assertion manifest совместно пропустить строку внутри уже выбранных XHTML-регионов. Baseline всегда проверяется повторным извлечением из текущего hash-bound XHTML до compiler/writer этапов.

Контракт не определяет смысловые границы scope и не подтверждает корректность atomic assertions. Полноту выбранных регионов и их `source_context_class` независимо подтверждает source reviewer через digest-bound source-assertion manifest v4 и receipt v6.

## Артефакты

В source-first handoff используются два JSON-артефакта:

- `source-row-extraction-spec.json` — проверяемая спецификация выбранного XHTML и целых регионов извлечения;
- `source-row-baseline.json` — детерминированный полный список requirement candidates, повторно строящийся из спецификации и текущего XHTML.

В extraction spec нет поля `accepted` или другого self-approval. Source-assertion manifest связывает канонические digest-ы spec и baseline, а независимый accepted receipt связывает точный digest manifest-а.

## Extraction spec v1

Верхнеуровневые поля:

| Поле | Правило |
| --- | --- |
| `version` | Равно `1`. |
| `scope_slug` | Стабильный slug выбранного внешнего scope. |
| `selected_xhtml.relative_path` | Нормализованный repository-relative POSIX path к mandatory XHTML. |
| `selected_xhtml.sha256` | SHA-256 текущих байтов XHTML. |
| `namespaces` | Необязательный объект `prefix -> URI`; при извлечении также доступен стандартный prefix `xhtml`. |
| `regions` | Непустой список целых регионов без per-row allowlist. |

Каждый region содержит `region_id`, `source_context_class` и один selector:

- `container`: `container_xpath` выбирает ровно один контейнер; сам контейнер тоже рассматривается как candidate, если это `tr`, `li`, standalone `p` или `h1`–`h6`;
- `contiguous-sibling-range`: `start_xpath` и `end_xpath` выбирают двух детей одного parent; `include_start` и `include_end` явно задают включение границ, а все siblings между ними входят автоматически.

Технически `container` может указать на один candidate. Extractor не способен отличить законный узкий scope от выборочного чтения источника, поэтому он не доказывает полноту scope boundary автоматически: независимый reviewer обязан проверить, что spec включает целые применимые containers/ranges, включая header и N/A-контекст.

Пример:

```json
{
  "version": 1,
  "scope_slug": "applications-menu-search",
  "selected_xhtml": {
    "relative_path": "fts/AutoFin/source/PostFinal-v2/PostFinal-v2.xhtml",
    "sha256": "<lowercase-sha256>"
  },
  "namespaces": {
    "xhtml": "http://www.w3.org/1999/xhtml"
  },
  "regions": [
    {
      "region_id": "REGION-SCOPE",
      "source_context_class": "scope-local",
      "selector": {
        "kind": "contiguous-sibling-range",
        "start_xpath": "/*/*[2]/*[68]",
        "end_xpath": "/*/*[2]/*[90]",
        "include_start": true,
        "include_end": true
      }
    }
  ]
}
```

### XPath subset

Selectors используют только абсолютную child-axis форму:

- каждый step — `*`, QName или QName с namespace prefix;
- единственный predicate — положительная числовая позиция `[n]`;
- descendant axis, union, text/attribute/function predicates и относительные пути запрещены;
- selector обязан выбрать ровно один элемент;
- canonical candidate locator использует element-sibling positions, например `/*/*[2]/*[45]/*[5]`.

Такой subset сохраняет повторяемость, поддерживает XHTML namespaces и не превращает extraction spec в скрытый перечень выбранных строк.

## Правила enumeration

Из каждого региона candidates перечисляются в document order:

- до text ownership целиком исключается annotation metadata subtree, если его неименованный XHTML-атрибут `title` exact равен `annotation` **или** `class` содержит exact case-sensitive ASCII-whitespace token `annotation_style_by_filter`;
- substring, другой регистр и обычные значения `title`/`class` не исключаются; semantic tail/sibling text за закрывающим тегом metadata subtree сохраняется;
- это DOM-level исключение применяется одинаково к enumeration и exact-locator resolver до нормализации и hashing; candidate внутри annotation subtree отсутствует и не может быть восстановлен regex-очисткой готового текста;
- `tr` образует один candidate со всем текстом строки; вложенные в него `p`, `li` и `tr` отдельно не считаются;
- `li` образует candidate из собственного текста без текста вложенных `li`/`tr`; каждый вложенный `li` перечисляется отдельно;
- непустые `p` и `h1`–`h6` образуют candidates только вне `tr` и `li`;
- пустые transport-элементы не образуют candidates;
- один DOM-элемент не может входить в два региона;
- повторяющийся текст не объединяется: разные canonical XPath дают разные candidates;
- пробельные символы и NBSP нормализуются, но регистр, написание и пунктуация источника сохраняются.

Table header и строки, признанные позднее `not-applicable`, не удаляются из baseline. Для них создаются явные SourceRows и последующее review-решение. Это не позволяет подменить полноту выборочным чтением только нужных data rows.

## Baseline v1

Верхнеуровневые поля:

| Поле | Правило |
| --- | --- |
| `version` | Равно `1`. |
| `scope_slug` | Exact match extraction spec. |
| `selected_xhtml` | Exact match extraction spec. |
| `extraction_spec_sha256` | Канонический JSON SHA-256 нормализованного extraction spec. |
| `candidate_set_sha256` | Канонический JSON SHA-256 полного ordered списка candidates. |
| `candidates` | Непустой полный список candidates. |

Candidate содержит:

- `candidate_id` — стабильный `SRC-CAND-<24 hex>`;
- `candidate_hash` — полный SHA-256 identity payload;
- `region_id`;
- `element_kind`;
- `canonical_xpath`;
- `bounded_source_text`;
- `source_context_class`.

Identity payload связывает scope, source path, region, kind, locator, нормализованный текст и context class. SHA всего XHTML не входит в candidate identity, поэтому добавление независимого элемента после существующего candidate не переименовывает этот candidate; актуальность всего source отдельно и строго связывают `selected_xhtml.sha256`, spec digest и baseline digest.

Stored baseline считается валидным только при exact equality с повторной extraction из текущего XHTML. Ручное изменение списка, digest-а, candidate hash или порядка не проходит проверку.

## SourceRow mapping v1

Compiler передает последовательность `SourceRowCandidateMapping` со следующими полями:

- `source_row_id`;
- `source_path`;
- `source_locator`;
- `bounded_source_text`;
- `source_context_class`;
- `candidate_id`.

Для SourceRow из выбранного XHTML `candidate_id` обязателен и в v1 является единственным. Его `source_locator`, `bounded_source_text` и `source_context_class` должны exact совпасть с candidate. Для строки другого source-файла `candidate_id` равен JSON `null`.

Проверка завершается ошибкой при любом из условий:

- baseline candidate не связан ни с одним XHTML SourceRow;
- SourceRow ссылается на неизвестный candidate;
- один candidate связан повторно;
- повторяется `source_row_id`;
- XHTML SourceRow не имеет candidate;
- non-XHTML SourceRow заявляет candidate;
- locator, текст или context class различаются.

Таким образом, каждый candidate связан ровно с одним SourceRow, а каждый XHTML SourceRow — ровно с одним candidate.

## Public Python API

Каноническая реализация находится в `test_case_agent/review_cycle/source_row_baseline.py`:

- `load_extraction_spec(path)`;
- `build_source_row_baseline(repo_root=..., spec=...)`;
- `load_source_row_baseline(path)`;
- `write_source_row_baseline(path, baseline)`;
- `validate_source_row_baseline(repo_root=..., spec=..., baseline=...)`;
- `validate_candidate_coverage(baseline=..., source_row_mappings=...)`;
- `validate_source_row_completeness(repo_root=..., extraction_spec_path=..., baseline_path=..., source_row_mappings=...)`.

Последняя функция возвращает `SourceRowCompletenessResult` с полями:

- `source_row_extraction_spec_digest`;
- `source_row_baseline_digest`;
- `candidate_set_digest`;
- `candidate_count`;
- `mapped_xhtml_source_row_count`;
- `non_xhtml_source_row_count`.

Compiler exact сравнивает первые, вторые и `candidate_count` с полями manifest-а `source_row_extraction_spec_digest`, `source_row_baseline_digest` и `source_row_candidate_count`. Любое нарушение вызывает `SourceRowBaselineValidationError` с устойчивым `code`; warning/waiver fallback отсутствует.

## Границы гарантии

Baseline доказывает полноту только внутри регионов extraction spec. Он не может сам определить, что reviewer ошибочно исключил ancestor, global или cross-referenced region. Поэтому source review отдельно проверяет:

- boundary completeness выбранных регионов;
- соответствие `source_context_class`;
- наличие всех applicable и explicit N/A SourceRows;
- semantic assertions, gap routing и execution readiness.

Изменение XHTML, extraction spec, baseline или SourceRow mapping требует повторной проверки до prepared compiler. Legacy inventory без candidate binding не является доказательством source-row completeness.
