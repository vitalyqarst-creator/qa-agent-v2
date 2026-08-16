from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.capture_dadata_fixture import capture_fixture
from scripts.create_ft_package import PACKAGE_DIRS, create_package
from scripts.validate_fixture_catalog import validate as validate_catalog
from scripts.validate_runtime_tc import validate as validate_tc
from scripts.validate_runtime_tree import validate as validate_tree


VALID_TC = """## TC-9.3.2-001

**Сквозной номер:** `TC-001`

**Название:** Сохранение карточки партнёра с уникальным наименованием

**Цель:** Проверить сохранение карточки с уникальным наименованием.

**Тип:** Positive

**Приоритет:** High

**Трассировка:** `AS.38`; Таблица 7.

**Предусловия:**

1. Открыть карточку добавления партнёра.

**Тестовые данные:**

- `Наименование партнёра` = `ПАО СБЕРБАНК`.

**Шаги:**

1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.
2. Нажать `СОХРАНИТЬ`.

**Итоговый ожидаемый результат:** Карточка партнёра сохранена.

**Постусловия:**

- Не требуются.
"""


class RuntimeContractTests(unittest.TestCase):
    def test_valid_runtime_test_case_passes(self) -> None:
        self.assertEqual([], validate_tc(VALID_TC))

    def test_internal_gap_and_fixture_request_are_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- Требуется fixture DaData (`GAP-005`).",
        )
        errors = validate_tc(invalid)
        self.assertTrue(any("internal marker" in error for error in errors))
        self.assertTrue(any("dependency note" in error for error in errors))

    def test_descriptive_data_instead_of_literal_are_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- Требуется фиксированный запрос и организация из снимка DaData.",
        )
        errors = validate_tc(invalid)
        self.assertTrue(any("dependency note" in error for error in errors))
        self.assertTrue(any("concrete" in error for error in errors))

    def test_duplicate_setup_action_is_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Открыть карточку добавления партнёра.",
        )
        self.assertTrue(any("duplicated" in error for error in validate_tc(invalid)))

    def test_provider_fixture_requires_existing_snapshot_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            snapshot = fixtures / "FX-DADATA-PARTNER-001.response.json"
            snapshot.write_text('{"suggestions":[{"value":"ПАО СБЕРБАНК"}]}', encoding="utf-8")
            catalog = {
                "fixtures": [
                    {
                        "fixture_id": "FX-DADATA-PARTNER-001",
                        "purpose": "Подсказка организации",
                        "source_type": "provider",
                        "provider": "DaData",
                        "request": {"query": "СБЕРБАНК"},
                        "runtime_data": {"suggestion": "ПАО СБЕРБАНК"},
                        "snapshot_path": "fixtures/FX-DADATA-PARTNER-001.response.json",
                        "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                    }
                ]
            }
            catalog_path = root / "fixture-catalog.json"
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_catalog(catalog_path))
            catalog["fixtures"][0]["snapshot_sha256"] = "0" * 64
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("SHA-256 mismatch" in error for error in validate_catalog(catalog_path)))

    def test_dadata_capture_creates_concrete_fixture_without_token(self) -> None:
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def getcode(self):
                return 200

            def read(self):
                return json.dumps(
                    {
                        "suggestions": [
                            {
                                "value": "ПАО СБЕРБАНК",
                                "data": {"inn": "7707083893", "ogrn": "1027700132195"},
                            }
                        ]
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "fixtures"
            with patch("scripts.capture_dadata_fixture.urlopen", side_effect=[Response(), Response()]):
                entry = capture_fixture(
                    kind="party",
                    query="СБЕРБАНК",
                    fixture_id="FX-DADATA-PARTNER-001",
                    purpose="Подсказка партнёра",
                    fixture_root=fixture_root,
                    token="not-written",
                )
            self.assertEqual("ПАО СБЕРБАНК", entry["runtime_data"]["suggestion"])
            self.assertEqual([], validate_catalog(fixture_root / "fixture-catalog.json"))
            snapshot = fixture_root / "FX-DADATA-PARTNER-001" / "response.json"
            self.assertNotIn("not-written", snapshot.read_text(encoding="utf-8"))

    def test_package_creator_does_not_copy_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "Partners-v1"
            create_package(package)
            self.assertEqual(set(PACKAGE_DIRS) | {"AGENT-NOTES.md"}, {item.name for item in package.iterdir()})
            self.assertFalse((package / "evals").exists())
            self.assertFalse((package / "references").exists())
            self.assertFalse((package / "scripts").exists())

    def test_runtime_tree_has_no_evals_or_legacy_skills(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], validate_tree(root))
        self.assertFalse((root / "evals").exists())
        self.assertFalse((root / "release").exists())
        self.assertFalse((root / "references" / "agent").exists())
        self.assertFalse((root / "test_case_agent").exists())
        self.assertFalse((root / "skills" / "ft-test-case-iteration").exists())
        self.assertFalse((root / "skills" / "ft-ui-automation-prep").exists())


if __name__ == "__main__":
    unittest.main()
