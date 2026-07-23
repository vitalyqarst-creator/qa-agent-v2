from __future__ import annotations

import unittest

from test_case_agent.source_constraint_taxonomy import restricted_symbol_classes


class RestrictedSymbolClassTaxonomyTests(unittest.TestCase):
    def test_exact_numeric_rule_splits_boundaries_and_character_classes(self) -> None:
        rules = restricted_symbol_classes(
            "BSR 182. Ограничение на формат: только 10 числовых символов."
        )

        self.assertEqual(
            [
                "length-n-minus-one",
                "length-n-plus-one",
                "letters",
                "spaces",
                "special-characters",
                "decimal-separator",
                "sign",
            ],
            [item.negative_class for item in rules],
        )
        self.assertEqual(
            [9, 11, 10, 10, 10, 10, 10],
            [len(item.representative_invalid_value) for item in rules],
        )
        self.assertEqual(7, len(set(item.representative_invalid_value for item in rules)))
        self.assertTrue(
            all(
                item.representative_invalid_value.startswith("12345")
                for item in rules[:2]
            )
        )

    def test_one_digit_rule_does_not_infer_empty_value_invalidity(self) -> None:
        rules = restricted_symbol_classes("Ровно 1 цифра.")

        self.assertNotIn(
            "length-n-minus-one",
            [item.negative_class for item in rules],
        )
        self.assertEqual("length-n-plus-one", rules[0].negative_class)

    def test_text_and_hyphen_rule_splits_disallowed_symbol_classes(self) -> None:
        rules = restricted_symbol_classes(
            "BSR 174. Возможен ввод только текстовых символов и специальный "
            "символ «-»."
        )

        self.assertEqual(
            [
                "digits",
                "special-characters-other-than-hyphen",
            ],
            [item.negative_class for item in rules],
        )
        self.assertTrue(all(item.restriction_type == "format" for item in rules))
        self.assertEqual(
            ["Иванов1", "Иванов@"],
            [item.representative_invalid_value for item in rules],
        )

    def test_nonexclusive_numeric_description_is_not_reclassified(self) -> None:
        self.assertEqual(
            (),
            restricted_symbol_classes("Поле имеет числовой формат."),
        )


if __name__ == "__main__":
    unittest.main()
