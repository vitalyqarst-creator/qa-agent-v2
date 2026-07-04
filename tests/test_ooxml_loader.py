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
EXPECTED_MARKERS = {
    "body_paragraph": "LXML_BODY_PARAGRAPH__A1B2C3D4",
    "split_run": "LXML_SPLIT_RUN__ABCD1234",
    "hidden_text": "LXML_HIDDEN_TEXT__29DA903C",
    "table_cell": "LXML_TABLE_CELL__C1FD64FA",
    "list_item": "LXML_LIST_ITEM__AE729DFF",
    "hyperlink_text": "LXML_HYPERLINK_TEXT__9C9B4FFD",
    "hyperlink_target": "LXML_HYPERLINK_TARGET__69775CAE",
    "header": "LXML_HEADER_TEXT__5AAF6E83",
    "footer": "LXML_FOOTER_TEXT__6AE6B316",
    "footnote": "LXML_FOOTNOTE_TEXT__B7650085",
    "endnote": "LXML_ENDNOTE_TEXT__4815F23D",
    "comment": "LXML_COMMENT_BODY__6F85E7E1",
    "image_alt": "LXML_IMAGE_ALT__31695ED4",
    "image_title": "LXML_IMAGE_TITLE__BC11F310",
    "textbox": "LXML_TEXTBOX_TEXT__1AC78EA4",
    "tracked_insert": "LXML_TRACKED_INSERT__320D248F",
    "tracked_delete": "LXML_TRACKED_DELETE__DBAA24A4",
    "docprop_core": "LXML_DOC_PROP_TITLE__AFDF6C87",
    "docprop_custom": "LXML_CUSTOM_DOC_PROP__1C2F7F94",
    "custom_xml": "LXML_CUSTOMXML_VALUE__AB5D4362",
}


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
            self.assertEqual(1, audit.tracked_insert_count)
            self.assertEqual(1, audit.tracked_delete_count)
            self.assertGreater(
                sum(1 for node in nodes if "tracked_insert" in node.flags),
                audit.tracked_insert_count,
            )
            self.assertGreater(
                sum(1 for node in nodes if "tracked_delete" in node.flags),
                audit.tracked_delete_count,
            )
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

            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["hidden_text"], "hidden_text"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["tracked_insert"], "tracked_insert"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["tracked_delete"], "tracked_delete"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["header"], "header"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["footer"], "footer"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["footnote"], "footnote"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["endnote"], "endnote"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["comment"], "comment"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["textbox"], "textbox"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["list_item"], "list"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["docprop_core"], "docprop"))
            self.assertTrue(has_node(nodes, EXPECTED_MARKERS["custom_xml"], "custom_xml"))

            self.assertTrue(
                any(
                    EXPECTED_MARKERS["split_run"] in node.value
                    and node.value_type == "aggregate"
                    and node.node_type == "paragraph"
                    and node.aggregate_kind == "paragraph"
                    and node.aggregate_confidence == "derived"
                    and node.aggregate_warning
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    EXPECTED_MARKERS["hyperlink_text"] in node.value
                    and "hyperlink" in node.flags
                    and EXPECTED_MARKERS["hyperlink_target"] in str(node.target_url)
                    and node.value_type in {"aggregate", "text"}
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    node.attribute_name == "descr"
                    and EXPECTED_MARKERS["image_alt"] in node.value
                    and "image_alt_or_title" in node.flags
                    for node in nodes
                )
            )
            self.assertTrue(
                any(
                    node.attribute_name == "title"
                    and EXPECTED_MARKERS["image_title"] in node.value
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
            self.assertEqual([str(source_docx)], payload["clean_run_audit"]["files_read"])
            self.assertTrue(payload["clean_run_audit"]["clean_run_claim"])
            marker_values = {marker["marker"] for marker in payload["markers"]}
            self.assertFalse(set(EXPECTED_MARKERS.values()) - marker_values)
            self.assertTrue(
                any(
                    marker["marker"] == EXPECTED_MARKERS["split_run"]
                    and marker["aggregate_confidence"] == "derived"
                    for marker in payload["markers"]
                )
            )
            self.assertIn("coverage_audit", payload)
            self.assertIn("clean_run_audit", payload)

    def test_cli_reports_forbidden_files_nearby_without_reading_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_docx = Path(temp_dir) / "sample.docx"
            forbidden_file = Path(temp_dir) / "expected_answer.txt"
            build_docx_fixture(source_docx)
            forbidden_file.write_text("do not read this", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "scripts" / "inspect_ooxml_source.py"),
                    str(source_docx),
                    "--json",
                    "--find-markers",
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            clean_run_audit = payload["clean_run_audit"]
            self.assertEqual([str(source_docx)], clean_run_audit["files_read"])
            self.assertEqual([], clean_run_audit["forbidden_files_read"])
            self.assertFalse(clean_run_audit["clean_run_claim"])
            self.assertEqual("contaminated-risk", clean_run_audit["clean_run_status"])
            self.assertEqual([str(forbidden_file)], clean_run_audit["forbidden_files_detected_nearby"])


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
        "word/document.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:v="urn:schemas-microsoft-com:vml">
  <w:body>
    <w:p><w:r><w:t>{EXPECTED_MARKERS["body_paragraph"]}</w:t></w:r></w:p>
    <w:p><w:r><w:t>LXML_SPLIT_</w:t></w:r><w:r><w:t>RUN__ABCD1234</w:t></w:r></w:p>
    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/></w:numPr></w:pPr><w:r><w:t>{EXPECTED_MARKERS["list_item"]}</w:t></w:r></w:p>
    <w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>{EXPECTED_MARKERS["hidden_text"]}</w:t></w:r></w:p>
    <w:p><w:ins w:id="1"><w:r><w:t>{EXPECTED_MARKERS["tracked_insert"]}</w:t></w:r></w:ins><w:del w:id="2"><w:r><w:delText>{EXPECTED_MARKERS["tracked_delete"]}</w:delText></w:r></w:del></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>{EXPECTED_MARKERS["table_cell"]}</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    <w:p><w:hyperlink r:id="rIdHyper"><w:r><w:t>{EXPECTED_MARKERS["hyperlink_text"]}</w:t></w:r></w:hyperlink></w:p>
    <w:p><w:r><w:drawing><wp:inline><wp:docPr id="1" name="Picture 1" descr="{EXPECTED_MARKERS["image_alt"]}" title="{EXPECTED_MARKERS["image_title"]}"/></wp:inline></w:drawing></w:r></w:p>
    <w:p><w:r><w:pict><v:shape><v:textbox><w:txbxContent><w:p><w:r><w:t>{EXPECTED_MARKERS["textbox"]}</w:t></w:r></w:p></w:txbxContent></v:textbox></v:shape></w:pict></w:r></w:p>
    <w:p><w:commentRangeStart w:id="0"/><w:r><w:t>Commented text</w:t></w:r><w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>
    <w:sectPr><w:headerReference r:id="rIdHeader"/><w:footerReference r:id="rIdFooter"/></w:sectPr>
  </w:body>
</w:document>""",
        "word/_rels/document.xml.rels": f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdHyper" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com/details?marker={EXPECTED_MARKERS["hyperlink_target"]}" TargetMode="External"/>
  <Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
</Relationships>""",
        "word/header1.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>{EXPECTED_MARKERS["header"]}</w:t></w:r></w:p></w:hdr>""",
        "word/footer1.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>{EXPECTED_MARKERS["footer"]}</w:t></w:r></w:p></w:ftr>""",
        "word/footnotes.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>{EXPECTED_MARKERS["footnote"]}</w:t></w:r></w:p></w:footnote></w:footnotes>""",
        "word/endnotes.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:endnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:endnote w:id="1"><w:p><w:r><w:t>{EXPECTED_MARKERS["endnote"]}</w:t></w:r></w:p></w:endnote></w:endnotes>""",
        "word/comments.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:comment w:id="0"><w:p><w:r><w:t>{EXPECTED_MARKERS["comment"]}</w:t></w:r></w:p></w:comment></w:comments>""",
        "word/styles.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:styleId="Normal"/></w:styles>""",
        "word/numbering.xml": """<?xml version="1.0" encoding="UTF-8"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:num w:numId="1"/></w:numbering>""",
        "docProps/core.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{EXPECTED_MARKERS["docprop_core"]}</dc:title></cp:coreProperties>""",
        "docProps/app.xml": """<?xml version="1.0" encoding="UTF-8"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Test</Application></Properties>""",
        "docProps/custom.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"><property name="CustomProp"><vt:lpwstr xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">{EXPECTED_MARKERS["docprop_custom"]}</vt:lpwstr></property></Properties>""",
        "customXml/item1.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<root><value>{EXPECTED_MARKERS["custom_xml"]}</value></root>""",
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
