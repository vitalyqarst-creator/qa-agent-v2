# OOXML Source Coverage Audit Format

Этот формат описывает audit native DOCX/OOXML ingestion слоя. Он нужен, чтобы явно отделять:

- ZIP entries, которые были увидены в `.docx`;
- XML и `.rels` части, которые были распарсены через `lxml.etree`;
- binary parts, содержимое которых не извлекалось без OCR или специализированного парсинга.

## Назначение

Coverage audit не является трассировкой требований и не заменяет `source-parity-check.md`.
Его задача - показать полноту технического чтения DOCX-контейнера перед дальнейшим анализом ФТ.

## Обязательные поля

```json
{
  "source_path": "fts/package/source/file.docx",
  "zip_entries_seen": ["[Content_Types].xml", "word/document.xml"],
  "xml_parts_seen": ["[Content_Types].xml", "word/document.xml"],
  "xml_parts_extracted": ["[Content_Types].xml", "word/document.xml"],
  "rels_parts_extracted": ["_rels/.rels", "word/_rels/document.xml.rels"],
  "binary_parts_seen": ["word/media/image1.png"],
  "binary_parts_extracted": [],
  "extraction_warnings": [
    "Binary part seen but not content-extracted: word/media/image1.png"
  ],
  "comments_count": 0,
  "footnotes_count": 0,
  "endnotes_count": 0,
  "headers_count": 0,
  "footers_count": 0,
  "hyperlinks_count": 0,
  "images_count": 1,
  "hidden_text_count": 0,
  "tracked_insert_count": 0,
  "tracked_delete_count": 0,
  "textboxes_count": 0,
  "custom_xml_parts_count": 0,
  "parser_mode": "strict",
  "extraction_method": "native_ooxml_zip_lxml"
}
```

CLI JSON должен дополнительно содержать `clean_run_audit`:

```json
{
  "clean_run_audit": {
    "files_read": ["fts/package/source/file.docx"],
    "forbidden_name_patterns": [
      "expected",
      "private",
      "golden",
      "answer",
      "solution",
      "bundle"
    ],
    "forbidden_files_detected_nearby": [],
    "forbidden_files_read": [],
    "clean_run_claim": true,
    "clean_run_status": "clean"
  }
}
```

## Rules

- `zip_entries_seen` должен включать все entries из ZIP, включая `word/media/*`, embedded objects и `docProps/thumbnail.*`.
- `xml_parts_extracted` содержит только успешно распарсенные `.xml` parts.
- `rels_parts_extracted` содержит успешно распарсенные `.rels` parts.
- `binary_parts_extracted` остается пустым, пока нет отдельного OCR/content extraction слоя.
- Для каждого binary part без content extraction должен быть warning вида:
  `Binary part seen but not content-extracted: <path>`.
- `parser_mode="strict"` означает `resolve_entities=False`, `no_network=True`, `recover=False`.
- `parser_mode="tolerant"` допустим только явно и должен добавлять warning.
- `tracked_insert_count` считает элементы `w:ins`, а не количество производных `SourceNode`.
- `tracked_delete_count` считает элементы `w:del`, а не количество производных `SourceNode`.
- CLI не должен читать файлы, чьи имена содержат `expected`, `private`, `golden`, `answer`, `solution` или `bundle`.
- CLI может проверять имена соседних файлов. Если такие файлы найдены рядом с DOCX, они указываются в `forbidden_files_detected_nearby`, `forbidden_files_read` остается пустым, а `clean_run_claim` должен быть `false` или `clean_run_status` должен быть `contaminated-risk`.

## SourceNode Minimum

Каждый extracted source node должен хранить:

- `node_id`;
- `source_path`;
- `part`;
- `xpath`;
- `node_type`;
- `value_type`: `text`, `tail`, `attribute` или `aggregate`;
- `text`/`value`;
- `attribute_name`, если применимо;
- `relationship_id`, если применимо;
- `target_part` или `target_url`, если применимо;
- `flags`: `hidden_text`, `tracked_insert`, `tracked_delete`, `comment`, `footnote`, `endnote`, `header`, `footer`, `table`, `list`, `hyperlink`, `image_alt_or_title`, `textbox`, `docprop`, `custom_xml`;
- `aggregate_kind`: `paragraph`, `table_cell`, `textbox`, `hyperlink` или `null`;
- `aggregate_confidence`: `derived` для aggregate nodes или `null`;
- `aggregate_warning`: предупреждение для aggregate nodes или `null`.

## Aggregate Nodes

Aggregate nodes are derived convenience nodes. Они нужны для случаев, где полезный текст разбит между несколькими `w:r`/`w:t`, например split-run маркеры или визуально единый абзац.

Downstream requirements extraction should prefer direct `text`, `tail` and `attribute` nodes when possible. Aggregate nodes may join distinct runs, field fragments, hidden text and tracked insertion/deletion text. Их нельзя считать более точным source-of-truth, чем direct OOXML nodes.

## Interpretation

Audit с binary warnings может быть корректным: это честная фиксация того, что binary content не извлекался.
Такой warning нельзя автоматически считать дефектом loader-а. Дефектом является ситуация, когда binary part есть в ZIP, но отсутствует в `binary_parts_seen` или warning скрыт.
Downstream должен учитывать, что OCR/content extraction для binary parts не выполнялся.
