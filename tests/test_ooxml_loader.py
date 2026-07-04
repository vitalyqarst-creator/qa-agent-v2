from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from test_case_agent import (
    extract_ooxml_source_nodes,
    inspect_ooxml_coverage,
    load_ooxml_source,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class OoxmlLoaderTests(unittest.TestCase):
    def test_ooxml_loader_extracts_required_parts_and_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_docx = Path(temp_dir) / "sample.docx"
            build_docx_fixture(source_docx)

            source = load_ooxml_source(source_docx)
            audit = source.coverage
            nodes = source.nodes

            self.assertIn("[Content_Types].xml", audit.zip_entries_seen)
            self.assertIn("word/media/image1.png", audit.zip_entries_seen)
            self.assertIn("docProps/thumbnail.jpeg", audit.zip_entries_seen)
            self.assertIn("word/document.xml", audit.xml_parts_seen)
            self.assertIn("word/document.xml", audit.xml_parts_extracted)
            self.assertIn("word/_rels/document.xml.rels", audit.rels_parts_extracted)
            self.assertIn("customXml/_rels/item1.xml.rels", audit.rels_parts_extracted)

            self.assertIn("word/media/image1.png", audit.binary_parts_seen)
            self.assertIn("docProps/thumbnail.jpeg", audit.binary_parts_seen)
            self.assertIn(
                "Binary part seen but not content-extracted: word/media/image1.png",
                audit.extraction_warnings,
            )
            self.assertIn(
                "Binary part seen but not content-extracted: docProps/thumbnail.jpeg",
                audit.extraction_warnings,
            )
            self.assertEqual([], audit.binary_parts_extracted)

            self.assertGreaterEqual(audit.hidden_text_count, 1)
            self.assertGreaterEqual(audit.tracked_insert_count, 1)
            self.assertGreaterEqual(audit.tracked_delete_count, 1)
            self.assertEqual(1, audit.headers_count)
            self.assertEqual(1, audit.footers_count)
            self.assertEqual(1, audit.footnotes_count)
            self.assertEqual(1, audit.endnotes_count)
            self.assertEqual(1, audit.comments_count)
            self.assertEqual(1, audit.hyperlinks_count)
            self.assertEqual(1, audit.images_count)
            self.assertEqual(1, audit.textboxes_count)
            self.assertEqual(1, audit.custom_xml_parts_count)
            self.assertEqual("strict", audit.parser_mode)
            self.assertEqual("native_ooxml_zip_lxml", audit.extraction_method)

            self.assertTrue(has_node(nodes, "Hidden marker", "hidden_text"))
            self.assertTrue(has_node(nodes, "Inserted text", "tracked_insert"))
            self.assertTrue(has_node(nodes, "Deleted text", "tracked_delete"))
            self.assertTrue(has_node(nodes, "Header text", "header"))
            self.assertTrue(has_node(nodes, "Footer text", "footer"))
            self.assertTrue(has_node(nodes, "Footnote text", "footnote"))
            self.assertTrue(has_node(nodes, "Endnote text", "endnote"))
            self.assertTrue(has_node(nodes, "Comment text", "comment"))
            self.assertTrue(has_node(nodes, "Textbox text", "textbox"))
            self.assertTrue(has_node(nodes, "List item", "list"))
            self.assertTrue(has_node(nodes, "Core title", "docprop"))
            self.assertTrue(has_node(nodes, "Custom XML marker", "custom_xml"))

            self.assertTrue(
                any(
                    "LXML_SPLIT_RUN__ABCD1234" in node.value
                    and node.value_type == "aggregate"
                    and node.node_type == "paragraph"
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    "Example link" in node.value
                    and "hyperlink" in node.flags
                    and node.target_url == "https://example.com/details"
                    and node.value_type in {"aggregate", "text"}
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    node.attribute_name == "descr"
                    and node.value == "Image description"
                    and "image_alt_or_title" in node.flags
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    node.attribute_name == "title"
                    and node.value == "Image title"
                    and "image_alt_or_title" in node.flags
                    for node in nodes
                )
            )

    def test_public_ooxml_api_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_docx = Path(temp_dir) / "sample.docx"
            build_docx_fixture(source_docx)

            coverage = inspect_ooxml_coverage(source_docx)
            nodes = extract_ooxml_source_nodes(source_docx)

            self.assertIn("word/document.xml", coverage.xml_parts_extracted)
            self.assertTrue(nodes)

    def test_cli_outputs_json_markers_and_files_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_docx = Path(temp_dir) / "sample.docx"
            build_docx_fixture(source_docx)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "inspect_ooxml_source.py"),
                    str(source_docx),
                    "--json",
                    "--find-markers",
                    "--marker-regex",
                    r"\bLXML_[A-Z0-9_]+__[A-F0-9]{8}\b",
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual([str(source_docx)], payload["files_read"])
            self.assertTrue(
                any(marker["marker"] == "LXML_SPLIT_RUN__ABCD1234" for marker in payload["markers"])
            )
            self.assertIn("coverage_audit", payload)


def has_node(nodes: list[object], value: str, flag: str) -> bool:
    return any(value in node.value and flag in node.flags for node in nodes)


def build_docx_fixture(path: Path) -> None:
    entries = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdOfficeDocument" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rIdCore" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>""",
        "word/document.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:document
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:v="urn:schemas-microsoft-com:vml">
  <w:body>
    <w:p><w:r><w:t>LXML_SPLIT_</w:t></w:r><w:r><w:t>RUN__ABCD1234</w:t></w:r></w:p>
    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/></w:numPr></w:pPr><w:r><w:t>List item</w:t></w:r></w:p>
    <w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>Hidden marker</w:t></w:r></w:p>
    <w:p><w:ins w:id="1"><w:r><w:t>Inserted text</w:t></w:r></w:ins><w:del w:id="2"><w:r><w:delText>Deleted text</w:delText></w:r></w:del></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell text</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    <w:p><w:hyperlink r:id="rIdHyper"><w:r><w:t>Example link</w:t></w:r></w:hyperlink></w:p>
    <w:p><w:r><w:drawing><wp:inline><wp:docPr id="1" name="Picture 1" descr="Image description" title="Image title"/></wp:inline></w:drawing></w:r></w:p>
    <w:p><w:r><w:pict><v:shape><v:textbox><w:txbxContent><w:p><w:r><w:t>Textbox text</w:t></w:r></w:p></w:txbxContent></v:textbox></v:shape></w:pict></w:r></w:p>
    <w:p><w:commentRangeStart w:id="0"/><w:r><w:t>Commented text</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>
    <w:sectPr><w:headerReference r:id="rIdHeader"/><w:footerReference r:id="rIdFooter"/></w:sectPr>
  </w:body>
</w:document>""",
        "word/_rels/document.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdHyper" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com/details" TargetMode="External"/>
  <Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
</Relationships>""",
        "word/header1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Header text</w:t></w:r></w:p></w:hdr>""",
        "word/footer1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Footer text</w:t></w:r></w:p></w:ftr>""",
        "word/footnotes.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>Footnote text</w:t></w:r></w:p></w:footnote></w:footnotes>""",
        "word/endnotes.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:endnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:endnote w:id="1"><w:p><w:r><w:t>Endnote text</w:t></w:r></w:p></w:endnote></w:endnotes>""",
        "word/comments.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:comment w:id="0"><w:p><w:r><w:t>Comment text</w:t></w:r></w:p></w:comment></w:comments>""",
        "word/styles.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:styleId="Normal"/></w:styles>""",
        "word/numbering.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:num w:numId="1"/></w:numbering>""",
        "docProps/core.xml": """<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Core title</dc:title></cp:coreProperties>""",
        "docProps/app.xml": """<?xml version="1.0" encoding="UTF-8"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Test</Application></Properties>""",
        "docProps/custom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"><property name="CustomProp"><vt:lpwstr xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">Custom value</vt:lpwstr></property></Properties>""",
        "customXml/item1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<root><value>Custom XML marker</value></root>""",
        "customXml/_rels/item1.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdCustom" Type="http://example.com/custom" Target="../itemProps1.xml"/></Relationships>""",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, value)
        archive.writestr("word/media/image1.png", b"\x89PNG\r\n\x1a\n")
        archive.writestr("docProps/thumbnail.jpeg", b"\xff\xd8\xff\xd9")


if __name__ == "__main__":
    unittest.main()
