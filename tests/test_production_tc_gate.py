from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.production_tc_gate import (
    validate_production_tc_content,
    validate_production_tc_draft,
)


class ProductionTcGateTests(unittest.TestCase):
    def _case(
        self,
        *,
        tc_id: str = "TC-AMS-001",
        preconditions: str = (
            "1. Авторизоваться в системе.\n"
            "2. Открыть основную форму."
        ),
        test_data: str = "- VIN: `XTA210990Y1234567`.",
        steps: str = (
            "1. Ввести `XTA210990Y1234567` в поле «VIN».\n"
            "2. Нажать «Найти»."
        ),
        expected_result: str = (
            "Таблица результатов обновлена и содержит строки, "
            "соответствующие введённому VIN."
        ),
        postconditions: str = "- Не требуются.",
        metadata: str = (
            "**Название:** Поиск по VIN\n"
            "**Тип:** позитивный\n"
            "**Приоритет:** средний\n"
            "**package_id:** applications-menu-search-postfinal-v2-test\n"
            "**Трассировка:** OBL-001; ATOM-001; SRC-001; BSR 16"
        ),
    ) -> str:
        return (
            f"## {tc_id}\n\n"
            f"{metadata}\n\n"
            "### Предусловия\n\n"
            f"{preconditions}\n\n"
            "### Тестовые данные\n\n"
            f"{test_data}\n\n"
            "### Шаги\n\n"
            f"{steps}\n\n"
            "### Итоговый ожидаемый результат\n\n"
            f"{expected_result}\n\n"
            "### Постусловия\n\n"
            f"{postconditions}\n"
        )

    def _finding_ids(self, content: str) -> set[str]:
        result = validate_production_tc_content(content)
        return {finding["id"] for finding in result.findings}

    def test_good_action_oriented_runtime_case_passes(self) -> None:
        result = validate_production_tc_content(self._case())

        self.assertTrue(result.passed, result.findings)
        self.assertEqual(1, result.test_case_count)
        self.assertEqual(
            "production-tc-runtime-gate-v2",
            result.as_dict()["validator"],
        )

    def test_unbalanced_russian_quotes_in_title_are_blocked(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                metadata=(
                    "**Название:** Ограничение «BSR 182. Только 10 символов\n"
                    "**Тип:** позитивный\n"
                    "**Приоритет:** средний\n"
                    "**package_id:** applications-menu-search-postfinal-v2-test\n"
                    "**Трассировка:** OBL-001; ATOM-001; SRC-001; BSR 182"
                )
            )
        )

        self.assertIn("production-unbalanced-title-quotes", finding_ids)

    def test_exact_no_setup_sentinel_with_bullet_punctuation_passes(self) -> None:
        result = validate_production_tc_content(
            self._case(preconditions="— Не требуются.")
        )

        self.assertTrue(result.passed, result.findings)

    def test_action_setup_can_be_followed_by_observation_items(self) -> None:
        result = validate_production_tc_content(
            self._case(
                preconditions=(
                    "1. Авторизоваться в системе.\n"
                    "2. Открыть форму поиска.\n"
                    "3. Убедиться, что форма открыта.\n"
                    "4. Проверить, что кнопка «Найти» доступна.\n"
                    "5. Дождаться завершения загрузки формы.\n"
                    "6. Зафиксировать наличие поля «VIN»."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_setup_can_capture_a_value_and_preserve_a_displayed_default(self) -> None:
        examples = (
            (
                "1. Установить признак различия адресов в значение «Нет».\n"
                "2. Не изменять отображаемое значение «Нет» переключателя "
                "«Ввести вручную»."
            ),
            (
                "1. Открыть блок адреса регистрации.\n"
                "2. Не изменять состояние появившегося флажка."
            ),
            (
                "1. Установить признак различия адресов в значение «Нет».\n"
                "2. В блоке фактического адреса установить признак «Ввести "
                "вручную» в значение «Да» и убедиться, что поле «Район» видимо."
            ),
        )
        for preconditions in examples:
            with self.subTest(preconditions=preconditions):
                result = validate_production_tc_content(
                    self._case(preconditions=preconditions)
                )
                self.assertTrue(result.passed, result.findings)

    def test_no_change_constraint_without_state_producing_setup_is_blocked(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Не изменять исходное значение «Нет» переключателя "
                    "«Ввести вручную»."
                )
            )
        )

        self.assertIn("production-non-reproducible-precondition", finding_ids)

    def test_default_value_observation_after_fresh_form_setup_passes(self) -> None:
        result = validate_production_tc_content(
            self._case(
                preconditions=(
                    "1. Открыть новую анкету.\n"
                    "2. Открыть блок адреса регистрации.\n"
                    "3. Просмотреть переключатель «Ввести вручную» и убедиться, "
                    "что он отображает значение по умолчанию «Нет»."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_default_value_observation_without_setup_is_blocked(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Просмотреть переключатель «Ввести вручную» и убедиться, "
                    "что он отображает значение по умолчанию «Нет»."
                )
            )
        )

        self.assertIn("production-non-reproducible-precondition", finding_ids)

    def test_locative_field_setup_action_is_executable(self) -> None:
        result = validate_production_tc_content(
            self._case(
                preconditions=(
                    "1. Открыть основную форму.\n"
                    "2. В поле «Социальный статус» выбрать значение «работа по найму»."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_locative_setup_can_include_an_explicit_followup_observation(self) -> None:
        result = validate_production_tc_content(
            self._case(
                preconditions=(
                    "1. В поле «Социальный статус» выбрать значение «работа по найму» "
                    "и убедиться, что в поле отображается значение «работа по найму»."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_action_oriented_address_setup_variants_are_reproducible(self) -> None:
        examples = (
            (
                "1. Установить переключатель «Ввести вручную» в значение «Нет», "
                "чтобы открыть автоматический режим заполнения."
            ),
            (
                "1. Открыть заполнение адреса, позволяющее оставить поле "
                "номера дома пустым."
            ),
            "1. Оставить поле «Город» пустым.",
            "1. Получить одно актуальное значение региона по контракту DEP-005.",
            "1. Найти в поле «Регион» полученное значение.",
            "1. Включить ручное заполнение фактического адреса.",
            "1. Указать фактический адрес без квартиры.",
        )
        for preconditions in examples:
            with self.subTest(preconditions=preconditions):
                result = validate_production_tc_content(
                    self._case(preconditions=preconditions)
                )
                self.assertTrue(result.passed, result.findings)

    def test_runtime_dadata_discovery_is_blocked(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Получить значение региона по контракту DaData.\n"
                    "2. Сохранить точное значение региона из полученного ответа."
                )
            )
        )

        self.assertIn("production-dadata-dynamic-fixture", finding_ids)
        self.assertIn("production-dadata-fixture-binding-missing", finding_ids)

    def test_action_does_not_hide_unproduced_passive_mutable_state(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Открыть форму с полем «VIN», заполненным валидным "
                    "значением."
                )
            )
        )

        self.assertIn("production-non-reproducible-precondition", finding_ids)

    def test_numbered_observation_can_start_with_a_gerund_clause(self) -> None:
        result = validate_production_tc_content(
            self._case(
                steps=(
                    "1. Не вводя значение в поле «Рабочий телефон», "
                    "просмотреть его исходный шаблон."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_preconditions_reject_unnumbered_passive_and_mixed_setup(self) -> None:
        examples = (
            "Авторизоваться в системе.\nОткрыть форму.",
            "1. Создан блок «Дополнительный доход».",
            "1. Открыть форму.\n2. Кнопка «Добавить» доступна.",
            "1. Поле «Сумма» отображается и пусто.",
            "1. Фикстура для заявки подготовлена.",
            "1. Проверить, что форма открыта.\n2. Открыть форму.",
            "1. Сеть доступна.",
            (
                "1. Открыть форму.\n"
                "2. Проверить, что поле «Сумма» заполнено значением `1000`."
            ),
        )
        for preconditions in examples:
            with self.subTest(preconditions=preconditions):
                self.assertIn(
                    "production-non-reproducible-precondition",
                    self._finding_ids(self._case(preconditions=preconditions)),
                )

    def test_r10_runtime_credentials_uuid_and_passive_setup_are_blocked(self) -> None:
        content = self._case(
            tc_id="TC-AMS-048",
            preconditions=(
                "1. Пользователь вошел штатным способом с runtime credentials "
                "и открыл форму поиска заявок через меню по видимой метке.\n"
                "2. Тест выполняется на заново открытой форме."
            ),
            test_data=(
                "- VIN: непосредственно перед проверкой сформировать 17 символов — "
                "`XTA` + первые 14 цифр десятичного представления сгенерированного UUID."
            ),
            expected_result=(
                "Поиск выполняется без ошибки обязательности для "
                "незаполненного поля «Номер заявки»."
            ),
        )

        finding_ids = self._finding_ids(content)

        self.assertIn("production-magic-credential-setup", finding_ids)
        self.assertIn("production-non-reproducible-precondition", finding_ids)
        self.assertIn("production-generic-fixture", finding_ids)
        self.assertIn("production-forbidden-process-wording", finding_ids)
        self.assertIn(
            "production-optional-filter-result-oracle-missing",
            finding_ids,
        )

    def test_test_account_magic_setup_is_blocked(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Авторизоваться под тестовой учётной записью.\n"
                    "2. Открыть основную форму."
                )
            )
        )

        self.assertIn("production-magic-credential-setup", finding_ids)

    def test_setup_profile_environment_and_package_leaks_are_blocked(self) -> None:
        examples = (
            (
                "1. Выполнить setup profile `SETUP-AUTOFIN-SEARCH`.\n"
                "2. Открыть форму.",
                "production-setup-profile-reference",
            ),
            (
                "1. Создать заявку на тестовом стенде.\n"
                "2. Открыть форму.",
                "production-environment-specific-precondition",
            ),
            (
                "1. Авторизоваться.\n"
                "2. Открыть форму AutoFin PostFinal-v2.",
                "production-package-name-leak",
            ),
        )
        for preconditions, finding_id in examples:
            with self.subTest(finding_id=finding_id):
                self.assertIn(
                    finding_id,
                    self._finding_ids(self._case(preconditions=preconditions)),
                )

    def test_passive_mutable_state_is_blocked_even_after_generic_open_action(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Открыть основную форму.\n"
                    "2. Поле «VIN» заполнено валидным значением."
                )
            )
        )

        self.assertIn("production-non-reproducible-precondition", finding_ids)

    def test_passive_login_is_blocked_even_with_a_later_open_action(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                preconditions=(
                    "1. Пользователь авторизован.\n"
                    "2. Открыть основную форму."
                )
            )
        )

        self.assertIn("production-non-reproducible-precondition", finding_ids)

    def test_generic_and_unobservable_oracles_are_blocked(self) -> None:
        examples = (
            ("Функция работает корректно.", "production-generic-oracle"),
            ("The visible result matches the requirement.", "production-generic-oracle"),
            (
                "Сформирована evidence-запись; конкретная UI-реакция не определена.",
                "production-unobservable-oracle",
            ),
        )
        for expected_result, finding_id in examples:
            with self.subTest(finding_id=finding_id):
                self.assertIn(
                    finding_id,
                    self._finding_ids(
                        self._case(expected_result=expected_result)
                    ),
                )

    def test_complete_calibration_candidate_with_concrete_value_passes(self) -> None:
        content = self._case(
            metadata=(
                "**Название:** Проверка недопустимой буквы в VIN\n"
                "**Тип:** негативный\n"
                "**Приоритет:** высокий\n"
                "**package_id:** applications-menu-search-postfinal-v2-test\n"
                "**Трассировка:** OBL-001; ATOM-001; BSR 18\n"
                "**Статус oracle:** ui-calibration-required\n"
                "**Статус тест-кейса:** candidate-ui-calibration\n"
                "**Требуется подтверждение:** Как UI отклоняет букву I в VIN?"
            ),
            test_data="- VIN с запрещённой буквой: `XTAI2345678901234`.",
            steps=(
                "1. Вставить `XTAI2345678901234` в поле «VIN».\n"
                "2. Зафиксировать фактическую видимую реакцию поля."
            ),
            expected_result=(
                "Недопустимое значение не должно быть принято как валидное. "
                "Конкретный наблюдаемый механизм отклонения требуется "
                "зафиксировать при UI calibration."
            ),
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)
        self.assertEqual(1, result.calibration_candidate_count)
        self.assertEqual(0, result.execution_ready_count)
        self.assertEqual(
            "ft-first-reviewed-with-calibration-pending",
            result.as_dict()["suite_readiness"],
        )

    def test_process_marker_in_title_is_blocked_but_body_marker_is_allowed(self) -> None:
        title_finding_ids = self._finding_ids(
            self._case(
                metadata=(
                    "**Название:** UI-калибровка обязательности VIN\n"
                    "**Тип:** негативный\n"
                    "**Приоритет:** высокий\n"
                    "**package_id:** client-addresses\n"
                    "**Трассировка:** OBL-001; ATOM-001; BSR 1\n"
                    "**Статус oracle:** ui-calibration-required\n"
                    "**Статус тест-кейса:** candidate-ui-calibration\n"
                    "**Требуется подтверждение:** Как UI сообщает об обязательности поля?"
                )
            )
        )
        self.assertIn("production-process-marker-in-title", title_finding_ids)

    def test_calibration_candidate_cardinality_oracle_is_not_phrase_gated(self) -> None:
        content = self._case(
            metadata=(
                "**Название:** Попытка добавить шестой блок\n"
                "**Тип:** негативный\n"
                "**Приоритет:** высокий\n"
                "**package_id:** additional-income-postfinal-v2-test\n"
                "**Трассировка:** OBL-006; ATOM-006; GSR 31\n"
                "**Статус oracle:** ui-calibration-required\n"
                "**Статус тест-кейса:** candidate-ui-calibration\n"
                "**Требуется подтверждение:** Как UI объясняет отказ добавить шестой блок?"
            ),
            test_data="- Порядковый номер добавляемого блока: `6`.",
            steps="1. Нажать «Добавить доход» после добавления пяти блоков.",
            expected_result=(
                "Шестой блок не добавлен; на форме остаются ровно "
                "пять блоков «Дополнительный доход»."
            ),
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)
        self.assertNotIn(
            "production-calibration-invariant-missing",
            {finding["id"] for finding in result.findings},
        )

    def test_calibration_candidate_requires_question_and_concrete_value(self) -> None:
        base_metadata = (
            "**Название:** Попытка добавить шестой блок\n"
            "**Тип:** негативный\n"
            "**Приоритет:** высокий\n"
            "**package_id:** additional-income-postfinal-v2-test\n"
            "**Трассировка:** OBL-006; ATOM-006; GSR 31\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration"
        )
        expected_result = (
            "Шестой блок не добавлен; на форме остаются ровно пять блоков."
        )
        examples = (
            (
                "missing-question",
                base_metadata,
                "- Порядковый номер: `6`.",
                "1. Нажать «Добавить доход».",
                "production-calibration-question-missing",
            ),
            (
                "missing-value",
                base_metadata
                + "\n**Требуется подтверждение:** Как UI объясняет отказ?",
                "- Данные для пяти существующих блоков.",
                "1. Нажать «Добавить доход».",
                "production-calibration-value-missing",
            ),
            (
                "meaningless-question",
                base_metadata + "\n**Требуется подтверждение:** ??",
                "- Порядковый номер: `6`.",
                "1. Нажать «Добавить доход».",
                "production-calibration-question-missing",
            ),
        )
        for label, metadata, test_data, steps, finding_id in examples:
            with self.subTest(label=label):
                self.assertIn(
                    finding_id,
                    self._finding_ids(
                        self._case(
                            metadata=metadata,
                            test_data=test_data,
                            steps=steps,
                            expected_result=expected_result,
                        )
                    ),
                )

    def test_calibration_candidate_accepts_explicit_empty_value(self) -> None:
        metadata = (
            "**Название:** Проверка обязательности поля\n"
            "**Тип:** негативный\n"
            "**Приоритет:** высокий\n"
            "**package_id:** employment-main-work\n"
            "**Трассировка:** OBL-001; ATOM-001; BSR 1\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration\n"
            "**Требуется подтверждение:** Как UI сообщает об обязательности поля?"
        )
        result = validate_production_tc_content(
            self._case(
                metadata=metadata,
                test_data="- Поле «Статус»: пустое значение.",
                steps=(
                    "1. Оставить поле «Статус» пустым.\n"
                    "2. Нажать «Далее»."
                ),
                expected_result="Переход на следующий шаг не выполнен.",
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_default_value_calibration_accepts_concrete_named_value(self) -> None:
        metadata = (
            "**Название:** Необязательность переключателя\n"
            "**Тип:** позитивный\n"
            "**Приоритет:** средний\n"
            "**package_id:** client-addresses\n"
            "**Трассировка:** OBL-014; ATOM-031; SRC-020\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration\n"
            "**Требуется подтверждение:** Какое действие подтверждает "
            "необязательность переключателя?"
        )
        result = validate_production_tc_content(
            self._case(
                metadata=metadata,
                test_data="- Логическое значение по умолчанию: «Нет».",
                steps=(
                    "1. Не изменять значение «Нет» и выполнить доступное "
                    "действие подтверждения."
                ),
                expected_result=(
                    "Переключатель сохраняет значение по умолчанию «Нет» без "
                    "обязательной активации."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_action_control_calibration_accepts_explicit_no_action(self) -> None:
        metadata = (
            "**Название:** Необязательность нажатия кнопки\n"
            "**Тип:** позитивный\n"
            "**Приоритет:** средний\n"
            "**package_id:** passport\n"
            "**Трассировка:** OBL-053; ATOM-071; SRC-030\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration\n"
            "**Требуется подтверждение:** Какой видимый исход наблюдается без "
            "нажатия кнопки?"
        )
        result = validate_production_tc_content(
            self._case(
                metadata=metadata,
                test_data="- Действие с кнопкой «Добавить паспорт»: не нажимать.",
                steps=(
                    "1. Не нажимать кнопку «Добавить паспорт».\n"
                    "2. Выполнить действие подтверждения формы."
                ),
                expected_result=(
                    "Нажатие кнопки «Добавить паспорт» не требуется. "
                    "Точный UI-отклик требует калибровки."
                ),
            )
        )

        self.assertNotIn(
            "production-calibration-value-missing",
            {finding["id"] for finding in result.findings},
        )

    def test_calibration_candidate_rejects_unconfirmed_transition_semantics(self) -> None:
        metadata = (
            "**Название:** Калибровка пустого поля\n"
            "**Тип:** негативный\n"
            "**Приоритет:** высокий\n"
            "**package_id:** client-addresses\n"
            "**Трассировка:** OBL-078; ATOM-095; SRC-035\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration\n"
            "**Требуется подтверждение:** Какое действие и какой UI-отклик "
            "возникают для пустого поля?"
        )
        examples = (
            {
                "expected_result": (
                    "Пустое значение допускается и не препятствует продолжению."
                ),
                "postconditions": "- Поле остаётся пустым.",
            },
            {
                "expected_result": (
                    "Пустое обязательное значение не подтверждается как валидное; "
                    "точный UI-отклик требует калибровки."
                ),
                "postconditions": (
                    "- Продолжение допускается только после ввода валидного значения."
                ),
            },
            {
                "expected_result": (
                    "Пустое необязательное поле допускается при продолжении; "
                    "точный UI-отклик требует калибровки."
                ),
                "postconditions": "- Поле остаётся пустым.",
            },
            {
                "expected_result": (
                    "Невалидное значение не принимается как валидное; "
                    "точный UI-отклик требует калибровки."
                ),
                "postconditions": "- Невалидное значение не сохраняется.",
            },
            {
                "expected_result": (
                    "Пустое обязательное значение не подтверждается как валидное; "
                    "точный UI-отклик требует калибровки."
                ),
                "postconditions": "- Карточка не должна быть продолжена.",
            },
            {
                "expected_result": (
                    "Невалидное значение не подтверждается как валидное; "
                    "точный UI-отклик требует калибровки."
                ),
                "postconditions": "- Поле «Регион» остаётся пустым.",
            },
        )
        for example in examples:
            with self.subTest(example=example):
                finding_ids = self._finding_ids(
                    self._case(
                        metadata=metadata,
                        test_data="- Поле «Регион»: пустое значение.",
                        steps="1. Оставить поле «Регион» пустым.",
                        **example,
                    )
                )
                self.assertIn(
                    "production-calibration-transition-overclaim",
                    finding_ids,
                )

    def test_calibration_candidate_accepts_neutral_continuation_invariant(self) -> None:
        metadata = (
            "**Название:** Проверка обязательности поля «Регион»\n"
            "**Тип:** негативный\n"
            "**Приоритет:** высокий\n"
            "**package_id:** client-addresses\n"
            "**Трассировка:** OBL-078; ATOM-095; SRC-035\n"
            "**Статус oracle:** ui-calibration-required\n"
            "**Статус тест-кейса:** candidate-ui-calibration\n"
            "**Требуется подтверждение:** Какое действие и какой UI-отклик "
            "возникают для пустого поля?"
        )
        result = validate_production_tc_content(
            self._case(
                metadata=metadata,
                test_data="- Поле «Регион»: пустое значение.",
                steps="1. Оставить поле «Регион» пустым.",
                expected_result=(
                    "Пустое обязательное поле не принимается как валидное для "
                    "продолжения; точный UI-триггер и отклик требуют калибровки."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_incomplete_calibration_candidate_is_blocked(self) -> None:
        content = self._case(
            metadata=(
                "**Название:** Проверка недопустимой буквы в VIN\n"
                "**Тип:** негативный\n"
                "**Приоритет:** высокий\n"
                "**package_id:** applications-menu-search-postfinal-v2-test\n"
                "**Трассировка:** OBL-001; ATOM-001; BSR 18\n"
                "**Статус oracle:** ui-calibration-required"
            ),
            test_data="- Значение отсутствует.",
            expected_result="Требуется UI calibration.",
        )

        finding_ids = self._finding_ids(content)

        self.assertIn("production-incomplete-calibration-lifecycle", finding_ids)

    def test_forbidden_process_wording_is_blocked(self) -> None:
        examples = (
            "1. Открыть форму по видимой метке.",
            "1. Ввести VIN согласно ФТ.",
            "1. Выполнить дальнейший сценарий.",
            "1. Использовать source-backed значение VIN.",
            "1. Подтвердить hash-bound runtime receipt.",
            "1. Выполнить fixture-blocked проверку.",
        )
        for steps in examples:
            with self.subTest(steps=steps):
                self.assertIn(
                    "production-forbidden-process-wording",
                    self._finding_ids(self._case(steps=steps)),
                )

    def test_visible_text_normalization_prevents_markup_unicode_bypasses(self) -> None:
        result = validate_production_tc_content(
            self._case(
                preconditions=(
                    "1. Войти с runtime\u200b **credentials**.\n"
                    "2. Открыть основную форму."
                ),
                test_data="- Сгенерировать <strong>UUID</strong> для VIN.",
                steps=(
                    "1. Ввести VIN по видимой **метке**.\n"
                    "2. Нажать «Найти»."
                ),
                postconditions=(
                    "- Передать source\u2011backed runtime\u2011receipt reviewer."
                ),
            )
        )
        finding_ids = {finding["id"] for finding in result.findings}

        self.assertIn("production-magic-credential-setup", finding_ids)
        self.assertIn("production-generic-fixture", finding_ids)
        self.assertIn("production-forbidden-process-wording", finding_ids)
        self.assertTrue(
            any(
                finding["id"] == "production-forbidden-process-wording"
                and finding["section"] == "Постусловия"
                for finding in result.findings
            ),
            result.findings,
        )

    def test_steps_require_numbering_and_an_executable_action(self) -> None:
        examples = (
            "- Ввести VIN.\n- Нажать «Найти».",
            "1. Поле VIN открыто.",
            "",
        )
        for steps in examples:
            with self.subTest(steps=steps):
                self.assertIn(
                    "production-missing-numbered-action-step",
                    self._finding_ids(self._case(steps=steps)),
                )

    def test_compound_negative_step_with_later_action_is_executable(self) -> None:
        result = validate_production_tc_content(
            self._case(
                steps=(
                    "1. Не изменять значение по умолчанию «Нет» и выполнить "
                    "доступный триггер подтверждения."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_dadata_address_decomposition_requires_observable_manual_fields(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                test_data=(
                    "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                    "- Запрос: `самара авроры 7 12`.\n"
                    "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`."
                ),
                steps=(
                    "1. Ввести адрес в поле фактического адреса.\n"
                    "2. Выбрать совпадающую подсказку DaData."
                ),
                expected_result=(
                    "Выбранный адрес разложен по соответствующим полям ручного "
                    "ввода."
                ),
            )
        )

        self.assertIn(
            "production-unobservable-address-decomposition",
            finding_ids,
        )

    def test_dadata_component_list_still_requires_revealing_manual_fields(self) -> None:
        finding_ids = self._finding_ids(
            self._case(
                test_data=(
                    "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                    "- Запрос: `самара авроры 7 12`.\n"
                    "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.\n"
                    "- Почтовый индекс: `443017`.\n"
                    "- Регион: `Самарская обл`.\n"
                    "- Город: `г Самара`."
                ),
                steps=(
                    "1. Ввести запрос в поле фактического адреса.\n"
                    "2. Выбрать предложение `г Самара, ул Авроры, д 7, кв 12`."
                ),
                expected_result=(
                    "В блоке ручного ввода отображаются компоненты выбранного "
                    "адреса: «Почтовый индекс» — `443017`, «Регион» — "
                    "`Самарская обл`, «Город» — `г Самара`."
                ),
            )
        )

        self.assertIn(
            "production-unobservable-address-decomposition",
            finding_ids,
        )

    def test_duplicate_dadata_path_requires_an_exact_address_branch(self) -> None:
        common = {
            "test_data": (
                "- Fixture DaData: `FX-DADATA-REGION-001`.\n"
                "- Запрос: `Саратов`.\n"
                "- Точное предложение: `Саратовская обл`."
            ),
            "steps": (
                "1. Ввести в поле «Регион» запрос `Саратов`.\n"
                "2. Выбрать предложение `Саратовская обл`."
            ),
            "expected_result": (
                "Интерфейс предлагает значение `Саратовская обл`, а после "
                "выбора поле «Регион» отображает значение `Саратовская обл`."
            ),
        }
        content = "\n".join(
            (
                self._case(
                    tc_id="TC-AMS-001",
                    preconditions=(
                        "1. Открыть блок адреса регистрации.\n"
                        "2. Установить переключатель «Ввести вручную» в значение «Да»."
                    ),
                    **common,
                ),
                self._case(
                    tc_id="TC-AMS-002",
                    preconditions=(
                        "1. Открыть адресный блок с переключателем «Ввести вручную».\n"
                        "2. Установить переключатель «Ввести вручную» в значение «Да»."
                    ),
                    **common,
                ),
            )
        )

        result = validate_production_tc_content(content)

        ambiguous = [
            finding
            for finding in result.findings
            if finding["id"] == "production-ambiguous-duplicate-execution-path"
        ]
        self.assertEqual(["TC-AMS-002"], [item["tc_id"] for item in ambiguous])

    def test_duplicate_dadata_path_with_two_explicit_branches_passes(self) -> None:
        common = {
            "test_data": (
                "- Fixture DaData: `FX-DADATA-REGION-001`.\n"
                "- Запрос: `Саратов`.\n"
                "- Точное предложение: `Саратовская обл`."
            ),
            "steps": (
                "1. Ввести в поле «Регион» запрос `Саратов`.\n"
                "2. Выбрать предложение `Саратовская обл`."
            ),
            "expected_result": (
                "Интерфейс предлагает значение `Саратовская обл`, а после "
                "выбора поле «Регион» отображает значение `Саратовская обл`."
            ),
        }
        content = "\n".join(
            (
                self._case(
                    tc_id="TC-AMS-001",
                    preconditions=(
                        "1. Открыть блок адреса регистрации.\n"
                        "2. Установить переключатель «Ввести вручную» в значение «Да»."
                    ),
                    **common,
                ),
                self._case(
                    tc_id="TC-AMS-002",
                    preconditions=(
                        "1. Открыть блок фактического адреса.\n"
                        "2. Установить переключатель «Ввести вручную» в значение «Да»."
                    ),
                    **common,
                ),
            )
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)

    def test_dadata_address_decomposition_with_component_comparison_passes(self) -> None:
        result = validate_production_tc_content(
            self._case(
                test_data=(
                    "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                    "- Запрос: `самара авроры 7 12`.\n"
                    "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.\n"
                    "- Компоненты: регион `Самарская обл`, город `Самара`, "
                    "улица `Авроры`, дом `7`, квартира `12`."
                ),
                steps=(
                    "1. Ввести адрес в поле «Адрес регистрации».\n"
                    "2. Выбрать совпадающую подсказку DaData.\n"
                    "3. Установить переключатель «Ввести вручную» в значение «Да» "
                    "и просмотреть поля ручного ввода.\n"
                    "4. Сравнить видимые поля с зафиксированными компонентами."
                ),
                expected_result=(
                    "Компоненты выбранного адреса отображены в соответствующих "
                    "полях ручного ввода адреса регистрации."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_dadata_decomposition_can_reveal_the_manual_input_block(self) -> None:
        result = validate_production_tc_content(
            self._case(
                test_data=(
                    "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                    "- Запрос: `самара авроры 7 12`.\n"
                    "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.\n"
                    "- Компоненты: регион `Самарская обл`, город `Самара`, "
                    "улица `Авроры`, дом `7`, квартира `12`."
                ),
                steps=(
                    "1. Ввести адрес в поле «Адрес регистрации».\n"
                    "2. Зафиксировать компоненты предложения DaData.\n"
                    "3. Выбрать предложение DaData.\n"
                    "4. Открыть блок ручного ввода адреса.\n"
                    "5. Сравнить видимые поля с зафиксированными компонентами."
                ),
                expected_result=(
                    "Компоненты выбранного адреса отображены в соответствующих "
                    "полях блока ручного ввода."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_dadata_decomposition_accepts_exact_proposal_without_repeated_vendor_name(self) -> None:
        result = validate_production_tc_content(
            self._case(
                test_data=(
                    "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                    "- Запрос: `самара авроры 7 12`.\n"
                    "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.\n"
                    "- Регион: `Самарская обл`.\n"
                    "- Город: `Самара`.\n"
                    "- Улица: `Авроры`.\n"
                    "- Дом: `7`.\n"
                    "- Квартира: `12`."
                ),
                steps=(
                    "1. Ввести запрос в поле «Адрес регистрации».\n"
                    "2. Выбрать предложение `г Самара, ул Авроры, д 7, кв 12`.\n"
                    "3. Зафиксировать возвращённые компоненты адреса.\n"
                    "4. Установить переключатель «Ввести вручную» в значение «Да», "
                    "чтобы открыть поля ручного ввода.\n"
                    "5. Сравнить видимые поля с зафиксированными компонентами."
                ),
                expected_result=(
                    "Компоненты выбранного адреса отображены в соответствующих "
                    "полях ручного ввода адреса регистрации."
                ),
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_dadata_positive_fixture_requires_id_query_and_exact_suggestion(self) -> None:
        base = self._case(
            test_data="- DaData используется для поиска адреса.",
            steps="1. Ввести `самара авроры 7 12` в поле адреса.",
            expected_result="Отображается адресная подсказка DaData.",
        )

        finding_ids = self._finding_ids(base)

        self.assertIn("production-dadata-fixture-binding-missing", finding_ids)
        self.assertIn("production-dadata-query-literal-missing", finding_ids)
        self.assertIn("production-dadata-suggestion-literal-missing", finding_ids)

    def test_dadata_negative_fixture_requires_verified_empty_response(self) -> None:
        content = self._case(
            test_data=(
                "- Fixture DaData: `FX-DADATA-ADDR-NEG-001`.\n"
                "- Запрос: `проверенный отрицательный адрес`.\n"
                "- Результат DaData отсутствует."
            ),
            steps="1. Ввести `проверенный отрицательный адрес` в поле адреса.",
            expected_result="Отображается сообщение «Некорректно указан адрес».",
        )

        self.assertIn(
            "production-dadata-negative-verification-missing",
            self._finding_ids(content),
        )

    def test_preverified_negative_dadata_fixture_passes(self) -> None:
        content = self._case(
            test_data=(
                "- Fixture DaData: `FX-DADATA-ADDR-NEG-001`.\n"
                "- Запрос: `проверенный отрицательный адрес`.\n"
                "- Результат DaData: `suggestions=[]`."
            ),
            steps="1. Ввести `проверенный отрицательный адрес` в поле адреса.",
            expected_result="Отображается сообщение «Некорректно указан адрес».",
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)

    def test_dadata_runtime_get_fixture_wording_is_blocked(self) -> None:
        content = self._case(
            preconditions=(
                "1. Получить fixture `FX-DADATA-ADDR-001` через HTTPS DaData.\n"
                "2. Открыть блок адресов."
            ),
            test_data=(
                "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                "- Запрос: `самара авроры 7 12`.\n"
                "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`."
            ),
            steps="1. Ввести запрос и выбрать предложение DaData.",
            expected_result="Выбранное предложение отображается в поле адреса.",
        )

        self.assertIn(
            "production-dadata-dynamic-fixture",
            self._finding_ids(content),
        )

    def test_dadata_semantic_suggestion_labels_are_accepted(self) -> None:
        for label in ("Выбираемое предложение", "Ожидаемое точное предложение"):
            with self.subTest(label=label):
                content = self._case(
                    test_data=(
                        "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                        "- Запрос: `самара авроры 7 12`.\n"
                        f"- {label}: `г Самара, ул Авроры, д 7, кв 12`."
                    ),
                    steps="1. Ввести запрос и выбрать предложение DaData.",
                    expected_result="Выбранное предложение отображается в поле адреса.",
                )
                self.assertNotIn(
                    "production-dadata-suggestion-literal-missing",
                    self._finding_ids(content),
                )

    def test_nonconcrete_current_dictionary_value_is_blocked(self) -> None:
        content = self._case(
            test_data="- Любое значение из актуального списка регионов.",
            steps="1. Выбрать указанное значение в поле «Регион».",
            expected_result="Выбранное значение отображается в поле «Регион».",
        )

        self.assertIn(
            "production-nonconcrete-runtime-value",
            self._finding_ids(content),
        )

    def test_runtime_selected_available_date_is_blocked(self) -> None:
        content = self._case(
            test_data=(
                "- Дата выдачи: выбранное при выполнении доступное значение."
            ),
            steps="1. Выбрать доступное значение даты и удалить блок.",
            expected_result="Заполненный блок удалён.",
        )

        self.assertIn(
            "production-nonconcrete-runtime-value",
            self._finding_ids(content),
        )

    def test_runtime_selected_birth_date_is_blocked(self) -> None:
        content = self._case(
            test_data="- Дата рождения: дата, выбранная во время выполнения теста.",
            steps="1. Рассчитать дату 14-летия и ввести предыдущий день.",
            expected_result="Сохранение блокируется.",
        )

        self.assertIn(
            "production-nonconcrete-runtime-value",
            self._finding_ids(content),
        )

    def test_explicit_runtime_lookup_prohibition_is_not_a_placeholder(self) -> None:
        content = self._case(
            test_data=(
                "- Fixture DaData: `FX-DADATA-FMS-POS-001`.\n"
                "- Запрос: `772-053`.\n"
                "- Точное предложение: `ОВД ЗЮЗИНО Г. МОСКВЫ`.\n"
                "- Поиск актуального значения во время выполнения тест-кейса запрещён."
            ),
            steps=(
                "1. Ввести запрос `772-053`.\n"
                "2. Выбрать предложение `ОВД ЗЮЗИНО Г. МОСКВЫ`."
            ),
            expected_result=(
                "В поле отображается выбранное значение "
                "«ОВД ЗЮЗИНО Г. МОСКВЫ»."
            ),
        )

        self.assertNotIn(
            "production-nonconcrete-runtime-value",
            self._finding_ids(content),
        )

    def test_internal_fixture_paths_and_snapshots_are_blocked(self) -> None:
        content = self._case(
            test_data=(
                "- Fixture DaData: `FX-DADATA-ADDR-001`.\n"
                "- Запрос: `самара авроры 7 12`.\n"
                "- Точное предложение: `г Самара, ул Авроры, д 7, кв 12`.\n"
                "- Значение взять из `fts/AutoFin/work/vendor-references/"
                "dadata-fixture-catalog.md` и response snapshot."
            ),
            steps="1. Ввести запрос и выбрать предложение DaData.",
            expected_result="Выбранное предложение отображается в поле адреса.",
        )

        self.assertIn(
            "production-internal-fixture-artifact-leak",
            self._finding_ids(content),
        )

    def test_out_of_scope_kladr_diagnostic_is_blocked(self) -> None:
        content = self._case(
            postconditions=(
                "- Проверка внутреннего заполнения KLADR в рамках этого кейса "
                "не выполняется."
            )
        )

        self.assertIn(
            "production-out-of-scope-diagnostic-leak",
            self._finding_ids(content),
        )

    def test_approved_alias_is_rejected_in_runtime_sections(self) -> None:
        content = self._case(
            steps=(
                "1. Ввести `самара авроры 7 12` в поле "
                "«Адрес постоянной регистрации»."
            ),
            expected_result=(
                "В поле «Адрес постоянной регистрации» отображается введённое "
                "значение."
            ),
        )

        result = validate_production_tc_content(
            content,
            approved_runtime_aliases={
                "Адрес постоянной регистрации": "Адрес регистрации",
            },
        )

        self.assertIn(
            "production-noncanonical-approved-alias",
            {finding["id"] for finding in result.findings},
        )

    def test_single_address_field_visibility_is_not_decomposition(self) -> None:
        result = validate_production_tc_content(
            self._case(
                steps=(
                    "1. Проверить поле при значении переключателя «Нет».\n"
                    "2. Переключить адрес регистрации на ручной ввод.\n"
                    "3. Проверить то же поле при значении «Да»."
                ),
                expected_result=(
                    "Поле «Адрес регистрации» отображается при автоматическом "
                    "вводе и продолжает отображаться при ручном вводе."
                ),
            )
        )

        self.assertNotIn(
            "production-unobservable-address-decomposition",
            {finding["id"] for finding in result.findings},
        )

    def test_optionality_absence_without_target_and_control_is_blocked(self) -> None:
        content = self._case(
            preconditions=(
                "1. Авторизоваться в системе.\n"
                "2. Открыть основную форму."
            ),
            test_data="- Фамилия клиента: `Иванов`.",
            steps=(
                "1. Ввести `Иванов` в поле «Фамилия клиента».\n"
                "2. Оставить остальные фильтры пустыми.\n"
                "3. Нажать «Найти»."
            ),
            expected_result=(
                "Ошибка обязательности для незаполненных фильтров не отображается; "
                "таблица результатов обновлена."
            ),
        )

        self.assertIn(
            "production-optional-filter-result-oracle-missing",
            self._finding_ids(content),
        )

    def test_optionality_paraphrase_and_search_synonym_are_blocked(self) -> None:
        content = self._case(
            test_data="- Фамилия клиента: `Иванов`.",
            steps=(
                "1. Ввести `Иванов` в поле «Фамилия клиента».\n"
                "2. Выполнить поиск."
            ),
            expected_result=(
                "Валидация обязательности не срабатывает; "
                "таблица результатов обновлена."
            ),
        )

        self.assertIn(
            "production-optional-filter-result-oracle-missing",
            self._finding_ids(content),
        )

    def test_optionality_with_target_and_control_result_oracle_passes(self) -> None:
        content = self._case(
            preconditions=(
                "1. Авторизоваться в системе.\n"
                "2. Открыть основную форму."
            ),
            test_data=(
                "- Номер целевой заявки: `APP-101`; фамилия: `Иванов`.\n"
                "- Номер контрольной заявки: `APP-202`; фамилия: `Петров`."
            ),
            steps=(
                "1. Оставить поле «Имя клиента» пустым.\n"
                "2. Ввести `Иванов` в поле «Фамилия клиента».\n"
                "3. Нажать «Найти»."
            ),
            expected_result=(
                "Ошибка обязательности для пустого поля «Имя клиента» не "
                "отображается; номер целевой заявки `APP-101` отображается в "
                "таблице результатов, а номер контрольной заявки `APP-202` не "
                "отображается в таблице результатов."
            ),
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)

    def test_optionality_structured_oracle_rejects_adversarial_variants(self) -> None:
        steps = (
            "1. Оставить поле «Имя клиента» пустым.\n"
            "2. Ввести `Иванов` в поле «Фамилия клиента».\n"
            "3. Нажать «Найти»."
        )
        prefix = (
            "Ошибка обязательности для пустого поля «Имя клиента» "
            "не отображается; "
        )
        valid_data = (
            "- Номер целевой заявки: `APP-101`; фамилия: `Иванов`.\n"
            "- Номер контрольной заявки: `APP-202`; фамилия: `Петров`."
        )
        invalid_variants = (
            (
                "generic-labels",
                (
                    "- Целевая заявка: `APP-101`; фамилия: `Иванов`.\n"
                    "- Контрольная заявка: `APP-202`; фамилия: `Петров`."
                ),
                (
                    prefix
                    + "целевая заявка найдена, контрольная заявка исключена."
                ),
            ),
            (
                "same-id",
                (
                    "- Номер целевой заявки: `APP-101`; фамилия: `Иванов`.\n"
                    "- Номер контрольной заявки: `APP-101`; фамилия: `Петров`."
                ),
                (
                    prefix
                    + "номер целевой заявки `APP-101` отображается в таблице "
                    "результатов, а номер контрольной заявки `APP-101` не "
                    "отображается в таблице результатов."
                ),
            ),
            (
                "mismatched-id",
                valid_data,
                (
                    prefix
                    + "номер целевой заявки `APP-999` отображается в таблице "
                    "результатов, а номер контрольной заявки `APP-202` не "
                    "отображается в таблице результатов."
                ),
            ),
            (
                "inverted-target",
                valid_data,
                (
                    prefix
                    + "номер целевой заявки `APP-101` не отображается в таблице "
                    "результатов, а номер контрольной заявки `APP-202` не "
                    "отображается в таблице результатов."
                ),
            ),
            (
                "positive-control",
                valid_data,
                (
                    prefix
                    + "номер целевой заявки `APP-101` отображается в таблице "
                    "результатов, а номер контрольной заявки `APP-202` "
                    "отображается в таблице результатов."
                ),
            ),
            (
                "double-negative-control",
                valid_data,
                (
                    prefix
                    + "номер целевой заявки `APP-101` отображается в таблице "
                    "результатов, а номер контрольной заявки `APP-202` не "
                    "отсутствует в таблице результатов."
                ),
            ),
        )

        for label, test_data, expected_result in invalid_variants:
            with self.subTest(label=label):
                self.assertIn(
                    "production-optional-filter-result-oracle-missing",
                    self._finding_ids(
                        self._case(
                            test_data=test_data,
                            steps=steps,
                            expected_result=expected_result,
                        )
                    ),
                )

    def test_pure_validation_no_result_and_action_only_cases_pass(self) -> None:
        cases = (
            self._case(
                expected_result=(
                    "Отображается сообщение "
                    "«Некорректный формат телефона»."
                )
            ),
            self._case(
                expected_result=(
                    "Отображается сообщение "
                    "«Не найдено ни одного результата»."
                )
            ),
            self._case(
                test_data="- Не требуются.",
                steps="1. Нажать «Создать заявку».",
                expected_result="Открыта форма создания новой заявки.",
            ),
        )

        for content in cases:
            with self.subTest(content=content[:80]):
                result = validate_production_tc_content(content)
                self.assertTrue(result.passed, result.findings)

    def test_concrete_valid_application_fixture_is_not_generic(self) -> None:
        result = validate_production_tc_content(
            self._case(
                test_data=(
                    "- Целевая валидная заявка `APP-101`, "
                    "VIN `XTA210990Y1234567`."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_required_metadata_and_runtime_sections_must_be_nonempty(self) -> None:
        result = validate_production_tc_content(
            self._case(
                metadata=(
                    "**Название:** Поиск по VIN\n"
                    "**Тип:** позитивный\n"
                    "**Трассировка:** OBL-001; ATOM-001; BSR 16"
                ),
                expected_result="",
                postconditions="",
            )
        )
        finding_ids = {finding["id"] for finding in result.findings}

        self.assertIn("production-required-metadata-missing", finding_ids)
        self.assertIn(
            "production-runtime-section-missing-or-empty", finding_ids
        )

    def test_numbered_drag_and_drop_step_is_an_executable_action(self) -> None:
        result = validate_production_tc_content(
            self._case(
                steps=(
                    "1. Перетащить `questionnaire-valid.pdf` в поле «Анкета клиента».\n"
                    "2. Проверить отображение имени файла."
                )
            )
        )

        self.assertTrue(result.passed, result.findings)

    def test_fan_in_type_persist_and_contact_heuristics_are_not_part_of_gate(self) -> None:
        metadata = (
            "**Название:** Поиск по фамилии клиента\n"
            "**Тип:** негативный\n"
            "**Приоритет:** средний\n"
            "**package_id:** applications-menu-search-postfinal-v2-test\n"
            "**Трассировка:** OBL-001; OBL-002; OBL-003; OBL-004; "
            "ATOM-001; ATOM-002; BSR 1; BSR 2; BSR 3; SRC-001\n"
            "**Примечание:** application-card persist contact-person"
        )

        result = validate_production_tc_content(self._case(metadata=metadata))

        self.assertTrue(result.passed, result.findings)

    def test_bad_wording_inside_fenced_example_is_ignored(self) -> None:
        content = self._case() + (
            "\n```markdown\n"
            "### Тестовые данные\n"
            "- Сгенерировать UUID.\n"
            "### Итоговый ожидаемый результат\n"
            "Функция работает корректно.\n```\n"
        )

        result = validate_production_tc_content(content)

        self.assertTrue(result.passed, result.findings)

    def test_path_api_and_no_canonical_blocks(self) -> None:
        no_blocks = validate_production_tc_content("# Empty draft\n")
        self.assertFalse(no_blocks.passed)
        self.assertEqual(
            "production-tc-no-canonical-blocks",
            no_blocks.findings[0]["id"],
        )

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "draft.md"
            path.write_text(self._case(), encoding="utf-8")
            from_path = validate_production_tc_draft(draft_path=path)

        self.assertTrue(from_path.passed, from_path.findings)
        self.assertEqual((str(path),), from_path.checked_paths)


if __name__ == "__main__":
    unittest.main()
