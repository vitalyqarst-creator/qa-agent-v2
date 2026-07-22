from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any

from test_case_agent.review_cycle.obligation_gate import (
    test_case_sections,
    without_fenced_blocks,
)
from test_case_agent.persistence_safety import (
    has_commit_or_transition_after_mutation,
    persistence_claim,
)


VALIDATOR_NAME = "production-tc-runtime-gate-v2"

HTML_COMMENT = re.compile(r"(?s)<!--.*?-->")
MARKDOWN_HEADING = re.compile(
    r"(?m)^#{1,6}[^\S\r\n]+(.+?)[^\S\r\n]*#*"
    r"[^\S\r\n]*(?:\r?\n|$)"
)
BOLD_FIELD = re.compile(
    r"(?im)^\*\*(Предусловия|Тестовые данные|Шаги|"
    r"Итоговый ожидаемый результат|Постусловия|Preconditions|Test Data|Steps|"
    r"Expected Result|Postconditions):\*\*[^\S\r\n]*(.*)$"
)
SECTION_ALIASES = {
    "предусловия": "preconditions",
    "preconditions": "preconditions",
    "тестовые данные": "test_data",
    "test data": "test_data",
    "шаги": "steps",
    "steps": "steps",
    "итоговый ожидаемый результат": "expected_result",
    "expected result": "expected_result",
    "постусловия": "postconditions",
    "postconditions": "postconditions",
}
SECTION_NAMES = {
    "preconditions": "Предусловия",
    "test_data": "Тестовые данные",
    "steps": "Шаги",
    "expected_result": "Итоговый ожидаемый результат",
    "postconditions": "Постусловия",
}
REQUIRED_METADATA = {
    "Название": re.compile(r"(?im)^\*\*Название:\*\*[^\S\r\n]*\S.+$"),
    "Тип": re.compile(r"(?im)^\*\*Тип:\*\*[^\S\r\n]*\S.+$"),
    "Приоритет": re.compile(r"(?im)^\*\*Приоритет:\*\*[^\S\r\n]*\S.+$"),
    "package_id": re.compile(r"(?im)^\*\*package_id:\*\*[^\S\r\n]*\S.+$"),
    "Трассировка": re.compile(r"(?im)^\*\*Трассировка:\*\*[^\S\r\n]*\S.+$"),
}

INLINE_LINK = re.compile(r"!?\[([^\]]+)]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
INLINE_MARKDOWN = re.compile(r"(?<!\\)[*_~]+")
CODE_SPAN = re.compile(r"`([^`\r\n]+)`")
UNICODE_HYPHENS = str.maketrans(
    {character: "-" for character in "\u2010\u2011\u2012\u2013\u2014\u2212"}
)

SETUP_PROFILE_RE = re.compile(
    r"(?:\bsetup[- ]profile\b|\bSETUP-[A-Z0-9_-]+\b|"
    r"профил\w*\s+подготовк\w*|"
    r"выполнить\s+setup\s+profile)",
    re.IGNORECASE,
)
ENVIRONMENT_RE = re.compile(
    r"(?:из\s+тестов\w*\s+стенд\w*|"
    r"на\s+тестов\w*\s+стенд\w*|"
    r"в\s+тестов\w*\s+сред\w*|"
    r"\btest\s+(?:stand|environment)\b)",
    re.IGNORECASE,
)
PACKAGE_LEAK_RE = re.compile(
    r"(?:\bAutoFin\b|\bPostFinal-v\d+\b|\bqa-agent(?:-v\d+)?\b)",
    re.IGNORECASE,
)
MAGIC_CREDENTIAL_RE = re.compile(
    r"(?:\bruntime[-_ ]*(?:credentials?|account|user)\b|"
    r"\btest[-_ ]*(?:account|credentials?|user)\b|"
    r"\bqa[-_ ]*(?:account|user)\b|"
    r"\bтестов\w*\s+(?:уч[её]тн\w*\s+запис\w*|логин\w*|"
    r"аккаунт\w*|пользовател\w*|УЗ)\b)",
    re.IGNORECASE,
)
PASSIVE_SETUP_RE = re.compile(
    r"(?:выполнен\w*\s+(?:штатн\w*\s+)?вход|"
    r"пользователь\s+вош[её]л|пользователь\s+авторизован|"
    r"(?:форма|карточка|раздел|экран)\b[^.\n;]{0,100}\b"
    r"открыт[аоы]?|"
    r"(?:пол(?:е|я|ю|ем)|переключател(?:ь|я|ю|ем|е)|"
    r"строк(?:а|и|у|ой|е)|запис(?:ь|и|ью)|"
    r"блок(?:а|у|ом|е|и|ов|ам|ами|ах)?)\b[^.\n;]{0,100}\b"
    r"(?:заполнен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"выбран(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"установлен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"включен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"создан(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"добавлен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"отображается|пуст(?:а|о|ы|ым|ой)?)\b|"
    r"кнопка\b[^.\n;]{0,100}\bдоступн[аоы]?|"
    r"(?:фикстура|набор\s+данных|fixture)\b[^.\n;]{0,100}\b"
    r"(?:подготовлен[аоы]?|prepared))",
    re.IGNORECASE,
)
MUTABLE_PASSIVE_STATE_RE = re.compile(
    r"(?:пол(?:е|я|ю|ем)|переключател(?:ь|я|ю|ем|е)|"
    r"строк(?:а|и|у|ой|е)|запис(?:ь|и|ью))\b[^.\n;]{0,100}\b"
    r"(?:заполнен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"выбран(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"установлен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"включен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"создан(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?|"
    r"добавлен(?:а|о|ы|ным|ной|ную|ного|ному|ном|ные|ных|ными)?)\b",
    re.IGNORECASE,
)
GENERIC_FIXTURE_RE = re.compile(
    r"(?:минимальн\w*\s+валидн\w*\s+набор|"
    r"данн\w*\s*,?\s*необходим\w*\s+для|"
    r"допустим\w*\s+значени[ея]\s+из\s+(?:формы|справочника)|"
    r"сгенерир\w*\s+UUID|UUID[^.\n]{0,120}(?:сгенерир\w*|десятичн)|"
    r"случайн\w*\s+значени[ея]|\b(?:runtime|test)\s+fixture\b)",
    re.IGNORECASE,
)
DADATA_REFERENCE_RE = re.compile(r"\bDaData\b", re.IGNORECASE)
DADATA_FIXTURE_ID_RE = re.compile(r"\bFX-DADATA-[A-Z0-9_-]+\b")
DADATA_DYNAMIC_FIXTURE_RE = re.compile(
    r"(?:получ\w*\s+(?:тестов\w*\s+)?значени\w*\s+[^.\n]{0,100}"
    r"(?:контракт\w*|ответ\w*)\s+DaData|"
    r"получ\w*\s+fixture\b[^.\n]{0,160}\bDaData\b|"
    r"значени\w*\s*,?\s*полученн\w*\s+(?:во\s+время|при)\s+выполнени\w*|"
    r"адрес\w*\s*,?\s*для\s+котор\w*\s+DaData\s+[^.\n]{0,100}"
    r"(?:возвращ\w*|наход\w*)|"
    r"точн\w*\s+текст\w*\s+[^.\n]{0,100}зафиксир\w*\s+перед\s+выбор\w*|"
    r"по\s+(?:указанн\w*\s+)?динамическ\w*\s+контракт\w*\s+DaData|"
    r"одно\s+актуальн\w*\s+[^.\n]{0,80}(?:DaData|адрес\w*))",
    re.IGNORECASE,
)
DADATA_QUERY_LITERAL_RE = re.compile(
    r"(?im)(?:^|[-*]\s*)(?:Запрос|query)\s*(?:DaData)?\s*:\s*`[^`\r\n]+`"
)
DADATA_SUGGESTION_LITERAL_RE = re.compile(
    r"(?im)(?:^|[-*]\s*)(?:(?:Выбираем\w*|Ожидаем\w*)\s+)?"
    r"(?:Точн\w*\s+)?(?:предложени\w*|suggestion)"
    r"\s*(?:DaData)?\s*:\s*`[^`\r\n]+`"
)
DADATA_EMPTY_SUGGESTIONS_RE = re.compile(
    r"(?i)\bsuggestions\s*=\s*\[\s*\]"
)
DADATA_RESPONSE_HASH_RE = re.compile(
    r"(?i)\b(?:SHA-?256|response_sha256)\s*:\s*`?[a-f0-9]{64}`?"
)
DADATA_NEGATIVE_ORACLE_RE = re.compile(
    r"(?:suggestions\s*=\s*\[\s*\]|"
    r"Некорректно\s+указан\s+адрес|"
    r"(?:не\s+отображ\w*|отсутств\w*)[^.\n]{0,80}подсказ\w*)",
    re.IGNORECASE,
)
TITLE_METADATA_RE = re.compile(r"(?im)^\*\*Название:\*\*[^\S\r\n]*(\S.+)$")
PROCESS_TITLE_RE = re.compile(
    r"(?:\bUI[-_ ]*calibration\b|калибровк\w*|evidence[-_ ]*запис\w*|"
    r"\bfixture[-_ ]*(?:validation|blocked)\b|\b(?:writer|reviewer|runner)\b)",
    re.IGNORECASE,
)
GENERIC_ORACLE_RE = re.compile(
    r"(?:работает\s+корректно|выполняется\s+корректно|"
    r"соответствует\s+(?:функциональн\w*\s+)?требовани\w*|"
    r"ожидаем\w*\s+результат\s+достигнут|проверка\s+пройдена|"
    r"значени[ея]\s+обработан[ао]?|результат\s+успешен|"
    r"\bworks?\s+correctly\b|\b(?:matches|meets|conforms\s+to)\s+"
    r"(?:the\s+)?requirements?\b|\bexpected\s+result\s+(?:is\s+)?achieved\b|"
    r"\btest\s+pass(?:es|ed)?\b|\bprocessed\s+successfully\b)",
    re.IGNORECASE,
)
UNOBSERVABLE_ORACLE_RE = re.compile(
    r"(?:evidence[- ]запис\w*|конкретн\w*\s+UI[- ]реакц\w*\s+"
    r"(?:не\s+определен\w*|подлежит\s+калибровк\w*)|"
    r"подлежит\s+UI[- ]калибровк\w*|требуется\s+уточнить|"
    r"предназначен\w*\s+для\s+ввод\w*|"
    r"сам\w*\s+по\s+себе\s+не\s+нарушает\s+требовани\w*)",
    re.IGNORECASE,
)
CANDIDATE_ORACLE_STATUS_RE = re.compile(
    r"(?im)^\*\*Статус oracle:\*\*[^\S\r\n]*"
    r"ui-calibration-required[^\S\r\n]*$"
)
CANDIDATE_TEST_CASE_STATUS_RE = re.compile(
    r"(?im)^\*\*Статус тест-кейса:\*\*[^\S\r\n]*"
    r"candidate-ui-calibration[^\S\r\n]*$"
)
CANDIDATE_CONFIRMATION_RE = re.compile(
    r"(?im)^\*\*Требуется подтверждение:\*\*[^\S\r\n]*(\S.+)$"
)
CONCRETE_CODE_LITERAL_RE = re.compile(r"`[^`\r\n]{1,200}`")
CONCRETE_EMPTY_VALUE_RE = re.compile(
    r"(?:\bпуст\w*\s+значени\w*\b|"
    r"\bоставить\b[^.\n;]{0,120}\bпуст\w*\b|"
    r"\bempty\s+value\b|\bleave\b[^.\n;]{0,120}\bempty\b)",
    re.IGNORECASE,
)
CONCRETE_NAMED_VALUE_RE = re.compile(
    r"\bзначени\w*(?:\s+[А-ЯЁа-яё-]+){0,5}\s*[:=]?\s*"
    r"[«\"]\s*[^»\"\r\n]{1,100}\s*[»\"]",
    re.IGNORECASE,
)
CALIBRATION_NO_ACTION_CONTROL_RE = re.compile(
    r"(?is)(?=.*\bне\s+(?:нажим\w*|активир\w*|выбира\w*|изменя\w*)\b)"
    r"(?=.*\b(?:кнопк\w*|виджет\w*|переключател\w*|элемент\w*)\b)"
)
CALIBRATION_TRANSITION_OVERCLAIM_RE = re.compile(
    r"(?:\bпродолжени\w*\s+допускается\s+только\s+после\b|"
    r"\bне\s+препятству\w*\s+продолжени\w*\b|"
    r"\bпуст\w*[^.\n;]{0,100}\bдопуска\w*\s+при\s+продолжени\w*\b|"
    r"\bневалидн\w*\s+значени\w*[^.\n;]{0,100}\bне\s+сохраня\w*\b|"
    r"\b(?:карточк\w*|форм\w*|переход\w*)[^.\n;]{0,100}"
    r"\bне\s+(?:долж\w*\s+быть\s+)?"
    r"(?:продолж\w*|выполня\w*|доступ\w*)\b|"
    r"\bпол\w*[^.\n;]{0,100}\bоста[её]тся\s+пуст\w*\b)",
    re.IGNORECASE,
)
ADDRESS_DECOMPOSITION_ORACLE_RE = re.compile(
    r"(?=[^.\n]{0,240}\b(?:компонент\w*|адрес\w*)\b)"
    r"(?=[^.\n]{0,240}\b(?:разлож\w*|отображ\w*)\b)"
    # Decomposition concerns multiple component fields. A singular field
    # visibility oracle must not require DaData component capture.
    r"(?=[^.\n]{0,240}\bпол(?:я|ей|ям|ями|ях)\b)"
    r"[^.\n]{0,240}\bручн\w*\s+ввод\w*\b",
    re.IGNORECASE,
)
ADDRESS_COMPONENT_FIELD_RE = re.compile(
    r"\b(?:Почтовый\s+индекс|Регион|Район|Насел[её]нный\s+пункт|"
    r"Город|Улица|Дом|Корпус|Квартира)\b",
    re.IGNORECASE,
)
MANUAL_INPUT_BLOCK_RE = re.compile(
    r"\b(?:блок\w*\s+)?ручн\w*\s+ввод\w*\b",
    re.IGNORECASE,
)
DADATA_SELECTION_THEN_MANUAL_REVEAL_RE = re.compile(
    r"(?:выбрать\w*[^.\n]{0,120}(?:DaData|подсказк\w*|предложени\w*)|"
    r"(?:DaData|подсказк\w*)[^.\n]{0,120}выбрать\w*)"
    r"[\s\S]{0,600}(?:"
    r"(?:установить|изменить|переключить)\w*[^.\n]{0,120}"
    r"(?:Ввести\s+вручную|ручн\w*\s+ввод\w*)[^.\n]{0,80}(?:Да|включ)|"
    r"(?:открыть|раскрыть|просмотреть)\w*[^.\n]{0,120}(?:"
    r"ручн\w*\s+пол\w*|пол\w*\s+ручн\w*\s+ввод\w*|"
    r"блок\w*\s+ручн\w*\s+ввод\w*))",
    re.IGNORECASE,
)
ADDRESS_COMPONENT_CAPTURE_RE = re.compile(
    r"(?:зафиксир\w*[^.\n]{0,100}компонент\w*|"
    r"значени\w*\s+компонент\w*[^.\n]{0,80}фиксир\w*|"
    r"компонент\w*[^.\n]{0,100}зафиксир\w*)",
    re.IGNORECASE,
)
DADATA_COMPONENT_LABEL_RE = re.compile(
    r"(?im)^\s*[-*]\s*(Почтовый\s+индекс|Регион|Город|Улица|Дом|Квартира)\s*:"
)
AMBIGUOUS_ADDRESS_BRANCH_RE = re.compile(
    r"(?:регистрац\w*[^.\n]{0,100}\bили\b[^.\n]{0,100}жительств\w*|"
    r"жительств\w*[^.\n]{0,100}\bили\b[^.\n]{0,100}регистрац\w*)",
    re.IGNORECASE,
)
GENERIC_ADDRESS_BLOCK_SETUP_RE = re.compile(
    r"\b(?:адресн\w*\s+блок\w*|блок\w*\s+адрес\w*)\b",
    re.IGNORECASE,
)
SPECIFIC_ADDRESS_BRANCH_RE = re.compile(
    r"\b(?:адрес\w*\s+(?:постоянн\w*\s+)?регистрац\w*|"
    r"(?:фактическ\w*\s+адрес\w*|адрес\w*\s+фактическ\w*)|"
    r"адрес\w*\s+фактическ\w*\s+мест\w*\s+жительств\w*)\b",
    re.IGNORECASE,
)
FORBIDDEN_PROCESS_RE = re.compile(
    r"(?:штатн\w*\s+способ\w*|по\s+видим\w*\s+метк\w*|"
    r"согласно\s+(?:ФТ|требовани\w*)|в\s+соответствии\s+с\s+"
    r"(?:ФТ|требовани\w*)|дальнейш\w*\s+сценар\w*|"
    r"evidence[-_ ]*запис\w*|\bUI[-_ ]*calibration\b|"
    r"\bprepared[-_ ]*package\b|\bruntime[-_ ]*receipt\b|"
    r"\bmanifest[-_ ]*digest\b|\bhash[-_ ]*bound\b|"
    r"\bfixture[-_ ]*blocked\b|\bsource[-_ ]*backed\b|"
    r"\b(?:writer|reviewer|runner)\b)",
    re.IGNORECASE,
)
NONCONCRETE_RUNTIME_VALUE_RE = re.compile(
    r"(?:\bлюб\w*\s+значени\w*\b[^.\n]{0,120}\bактуальн\w*\s+списк\w*\b|"
    r"\b(?:значени\w*|дат\w*)\b[^.\n]{0,120}\b"
    r"(?:во\s+время|при)\s+выполнени\w*\b|"
    r"\bвыбрат\w*\b[^.\n]{0,80}\bдоступн\w*\s+(?:значени\w*|дат\w*)\b)",
    re.IGNORECASE,
)
PROHIBITED_RUNTIME_LOOKUP_RE = re.compile(
    r"[^.\n]{0,200}\b(?:значени\w*|fixture)\b[^.\n]{0,120}"
    r"\bво\s+время\s+выполнени\w*\b[^.\n]{0,100}"
    r"\b(?:запрещ\w*|не\s+допуска\w*)\b",
    re.IGNORECASE,
)
INTERNAL_FIXTURE_ARTIFACT_RE = re.compile(
    r"(?:\bwork[\\/]vendor-references[\\/]|"
    r"\bdadata-fixtures[\\/][^\s`]+|"
    r"\bresponse\s+snapshot\b|\bsnapshot\s+ответ\w*\b|"
    r"\bverification(?:\.json)?\b|\bSHA-?256\b)",
    re.IGNORECASE,
)
OUT_OF_SCOPE_KLADR_DIAGNOSTIC_RE = re.compile(
    r"(?:проверк\w*[^.\n]{0,120}\bkladr\b[^.\n]{0,120}"
    r"не\s+выполн\w*|\bkladr\b[^.\n]{0,120}"
    r"(?:вне\s+рамок|не\s+провер\w*|не\s+выполн\w*))",
    re.IGNORECASE,
)
OPTIONALITY_ABSENCE_RE = re.compile(
    r"(?:без\s+(?:ошибк\w*|валидаци\w*|сообщени\w*)[^.\n;]{0,80}"
    r"обязательн\w*|"
    r"(?:ошибк\w*|валидаци\w*|сообщени\w*|признак\w*)"
    r"[^.\n;]{0,100}обязательн\w*[^.\n;]{0,100}"
    r"(?:не\s+(?:отображ\w*|появ\w*|возник\w*|срабатыва\w*)|отсутств\w*)|"
    r"(?:не\s+(?:отображ\w*|появ\w*|возник\w*|срабатыва\w*)|отсутств\w*)"
    r"[^.\n;]{0,100}(?:ошибк\w*|валидаци\w*|сообщени\w*|признак\w*)"
    r"[^.\n;]{0,100}обязательн\w*)",
    re.IGNORECASE,
)
SEARCH_ACTION_RE = re.compile(
    r"(?:нажать[^.\n]{0,80}(?:найти|поиск)|"
    r"(?:выполнить|запустить|инициировать)\s+поиск|"
    r"submit\s+(?:the\s+)?search|\bsearch\b)",
    re.IGNORECASE,
)
TARGET_ID_RE = re.compile(
    r"\bномер\w*\s+целев\w*\s+заявк\w*\b"
    r"[^\S\r\n]*(?::[^\S\r\n]*)?`([^`\r\n]+)`",
    re.IGNORECASE,
)
CONTROL_ID_RE = re.compile(
    r"\bномер\w*\s+контрольн\w*\s+заявк\w*\b"
    r"[^\S\r\n]*(?::[^\S\r\n]*)?`([^`\r\n]+)`",
    re.IGNORECASE,
)
POSITIVE_RESULT_STATE_RE = re.compile(
    r"(?<!не\s)(?:отображ\w*|присутств\w*|найден\w*)\s+"
    r"в\s+таблиц\w*\s+результат\w*",
    re.IGNORECASE,
)
NEGATIVE_RESULT_STATE_RE = re.compile(
    r"(?:не\s+(?:отображ\w*|присутств\w*|найден\w*)|"
    r"(?<!не\s)отсутств\w*)\s+в\s+таблиц\w*\s+результат\w*",
    re.IGNORECASE,
)
NEGATED_POSITIVE_STATE_RE = re.compile(
    r"не\s+(?:отображ\w*|присутств\w*|найден\w*)\s+"
    r"в\s+таблиц\w*\s+результат\w*",
    re.IGNORECASE,
)
DOUBLE_NEGATIVE_STATE_RE = re.compile(
    r"(?:не\s+отсутств\w*|не\s+не\s+)", re.IGNORECASE
)
NO_RESULT_RE = re.compile(
    r"не\s+найдено\s+ни\s+одного\s+результат\w*", re.IGNORECASE
)
NUMBERED_LINE_RE = re.compile(r"(?m)^[^\S\r\n]*\d+[.)][^\S\r\n]+(.+)$")
NUMBERED_PRECONDITION_RE = re.compile(
    r"^[^\S\r\n]*\d+[.)][^\S\r\n]+(.+?)[^\S\r\n]*$"
)
ACTION_STEP_RE = re.compile(
    r"(?:авторизоваться|войти|открыть|перейти|ввести|"
    r"заполнить|выбрать|установить|нажать|очистить|"
    r"оставить|создать|добавить|сформировать|загрузить|выполнить|"
    r"проверить|просмотреть|убедиться|сверить|дождаться|log\s+in|open|"
    r"navigate|enter|fill|select|set|click|clear|leave|create|add|submit|"
    r"upload|verify|check|compare|wait)",
    re.IGNORECASE,
)
RUSSIAN_INFINITIVE_STEP_RE = re.compile(
    r"^[^\S\r\n]*(?:[А-ЯЁ][А-Яа-яЁё-]*"
    r"(?:ть|ти|чь)(?:ся|сь)?)\b",
    re.IGNORECASE,
)
UNSAVED_DIALOG_PRECONDITION_RE = re.compile(
    r"(?:(?:уведомлени\w*|диалог\w*)[^.\n]{0,160}"
    r"(?:`да`|`нет`|«да»|«нет»|\bда\b|\bнет\b)[^.\n]{0,160}"
    r"(?:после\s+изменени\w*|несохраненн\w*)|"
    r"(?:unsaved|after\s+(?:a\s+)?change)[^.\n]{0,160}"
    r"(?:notification|dialog)[^.\n]{0,160}\b(?:yes|no)\b)",
    re.IGNORECASE,
)
OBSERVATION_ONLY_START_RE = re.compile(
    r"^(?:проверить|убедиться|сверить|дождаться|зафиксировать|"
    r"просмотреть|осмотреть|"
    r"verify|check|compare|wait|record)\b",
    re.IGNORECASE,
)
NO_CHANGE_STATE_CONSTRAINT_RE = re.compile(
    r"^не\s+изменять\b[^.\n;]{0,180}\b(?:отображаем\w*|исходн\w*|состояни\w*)\b",
    re.IGNORECASE,
)
OBSERVATION_VERB_RE = re.compile(
    r"\b(?:проверить|убедиться|сверить|дождаться|зафиксировать|"
    r"просмотреть|осмотреть|"
    r"verify|check|compare|wait|record)\b",
    re.IGNORECASE,
)
SETUP_ACTION_START_RE = re.compile(
    r"^(?:авторизоваться|войти|открыть|перейти|нажать|удалить|"
    r"очистить|создать|добавить|выбрать|установить|ввести|заполнить|"
    r"оставить|загрузить|перетащить|вставить|раскрыть|развернуть|"
    r"закрыть|активировать|выделить|прокрутить|получить|сохранить|указать|найти|"
    r"включить|выполнить|"
    r"log\s+in|open|navigate|click|delete|clear|create|add|select|set|"
    r"enter|fill|leave|upload|drag|drop|insert|expand|close|activate|"
    r"scroll)\b",
    re.IGNORECASE,
)
LOCATIVE_SETUP_ACTION_RE = re.compile(
    r"^(?:в|на)\s+(?:[А-ЯЁа-яё-]+\s+){0,3}"
    r"(?:пол(?:е|я|ю|ем)|блок(?:е|а|у|ом)|списк(?:е|а|у|ом)|"
    r"переключател(?:е|ь|я|ю|ем))\b[^.\n;]{0,160}\b"
    r"(?:выбрать|установить|ввести|заполнить|оставить|очистить|нажать|"
    r"выполнить)\b",
    re.IGNORECASE,
)
MUTABLE_VALUE_OBSERVATION_RE = re.compile(
    r"(?:поле|список|переключатель|значени\w*)\b[^.\n;]{0,120}\b"
    r"(?:заполнен\w*|выбран\w*|установлен\w*|введен\w*|введён\w*|"
    r"пуст\w*|empty|filled|selected|set)\b",
    re.IGNORECASE,
)
VALUE_MUTATION_ACTION_RE = re.compile(
    r"^(?:очистить|выбрать|установить|ввести|заполнить|оставить\s+пуст|"
    r"clear|select|set|enter|fill|leave\s+empty)\b",
    re.IGNORECASE,
)
VALUE_MUTATION_VERB_RE = re.compile(
    r"\b(?:очистить|выбрать|установить|ввести|заполнить|оставить|"
    r"clear|select|set|enter|fill|leave)\b",
    re.IGNORECASE,
)
DEFAULT_VALUE_OBSERVATION_RE = re.compile(
    r"\bзначени\w*\s+по\s+умолчанию\b",
    re.IGNORECASE,
)
DEFAULT_STATE_SOURCE_ACTION_RE = re.compile(
    r"^(?:открыть\s+нов\w+\s+(?:анкет\w*|карточк\w*|форм\w*)|"
    r"создать|добавить|установить|включить)\b",
    re.IGNORECASE,
)
QUOTED_LABEL_RE = re.compile(r"«([^»]+)»")


def _normalized_title(text: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", text).casefold().replace("ё", "е").split()
    )


def _clean_block(block: str) -> str:
    return HTML_COMMENT.sub("", without_fenced_blocks(block))


def _visible_text(text: str, *, preserve_code_ticks: bool = False) -> str:
    """Return normalized rendered text while preserving code-span values."""

    normalized = unicodedata.normalize("NFKC", unescape(text))
    normalized = ZERO_WIDTH.sub("", normalized).translate(UNICODE_HYPHENS)
    rendered: list[str] = []
    cursor = 0
    for match in CODE_SPAN.finditer(normalized):
        outside = normalized[cursor : match.start()]
        outside = INLINE_LINK.sub(r"\1", outside)
        outside = HTML_TAG.sub("", outside)
        outside = INLINE_MARKDOWN.sub("", outside)
        rendered.append(outside)
        code_value = match.group(1)
        rendered.append(f"`{code_value}`" if preserve_code_ticks else code_value)
        cursor = match.end()
    outside = normalized[cursor:]
    outside = INLINE_LINK.sub(r"\1", outside)
    outside = HTML_TAG.sub("", outside)
    outside = INLINE_MARKDOWN.sub("", outside)
    rendered.append(outside)
    result = "".join(rendered)
    if not preserve_code_ticks:
        result = result.replace("`", "")
    return re.sub(r"[^\S\r\n]+", " ", result)


def _is_no_setup_precondition(text: str) -> bool:
    """Recognize the exact rendered no-setup sentinel, ignoring edge punctuation."""

    compact = " ".join(text.split())
    compact = re.sub(r"^[\W_]+|[\W_]+$", "", compact, flags=re.UNICODE)
    return _normalized_title(compact) == "не требуются"


def _starts_with_executable_action(text: str) -> bool:
    return (
        SETUP_ACTION_START_RE.match(text) is not None
        or LOCATIVE_SETUP_ACTION_RE.match(text) is not None
    )


def _mutable_observation_has_setup_cause(
    observation: str,
    prior_actions: tuple[str, ...],
) -> bool:
    if MUTABLE_VALUE_OBSERVATION_RE.search(observation) is None:
        return True
    if DEFAULT_VALUE_OBSERVATION_RE.search(observation) is not None and any(
        DEFAULT_STATE_SOURCE_ACTION_RE.match(action) is not None
        for action in prior_actions
    ):
        return True
    relevant_actions = tuple(
        action for action in prior_actions if VALUE_MUTATION_ACTION_RE.match(action)
    )
    if not relevant_actions:
        return False
    observed_labels = {
        _normalized_title(value) for value in QUOTED_LABEL_RE.findall(observation)
    }
    if not observed_labels:
        return True
    action_labels = {
        _normalized_title(value)
        for action in relevant_actions
        for value in QUOTED_LABEL_RE.findall(action)
    }
    return bool(observed_labels.intersection(action_labels))


def _precondition_structure_problem(preconditions: str) -> str | None:
    """Return the first setup line that cannot be executed from the document."""

    if _is_no_setup_precondition(preconditions):
        return None

    lines = tuple(line.strip() for line in preconditions.splitlines() if line.strip())
    if not lines:
        return None

    state_producing_actions: list[str] = []
    for line in lines:
        numbered = NUMBERED_PRECONDITION_RE.fullmatch(line)
        if numbered is None:
            return line

        item = numbered.group(1).strip()
        if NO_CHANGE_STATE_CONSTRAINT_RE.match(item) is not None:
            if not state_producing_actions:
                return item
            continue
        if OBSERVATION_ONLY_START_RE.match(item) is not None:
            if not state_producing_actions or not _mutable_observation_has_setup_cause(
                item, tuple(state_producing_actions)
            ):
                return item
            continue
        if not _starts_with_executable_action(item):
            return item
        state_producing_actions.append(item)
    return None


def _line_safe_passive_setup_problem(preconditions: str) -> str | None:
    """Apply passive-state heuristics per setup item after structural validation."""

    if _is_no_setup_precondition(preconditions):
        return None

    for line in preconditions.splitlines():
        line = line.strip()
        if not line:
            continue
        numbered = NUMBERED_PRECONDITION_RE.fullmatch(line)
        item = numbered.group(1).strip() if numbered is not None else line
        if NO_CHANGE_STATE_CONSTRAINT_RE.match(item) is not None:
            continue
        matches = tuple(
            match
            for pattern in (MUTABLE_PASSIVE_STATE_RE, PASSIVE_SETUP_RE)
            if (match := pattern.search(item)) is not None
        )
        if not matches:
            continue

        passive = min(matches, key=lambda match: match.start())
        if OBSERVATION_ONLY_START_RE.match(item) is not None:
            continue
        if (
            _starts_with_executable_action(item)
            and OBSERVATION_VERB_RE.search(item) is not None
        ):
            continue
        if OBSERVATION_VERB_RE.search(item[: passive.start()]) is not None:
            continue
        if VALUE_MUTATION_VERB_RE.search(item[: passive.start()]) is not None:
            continue
        return passive.group(0)
    return None


def production_precondition_problem(preconditions: str) -> str | None:
    """Return the first production-runtime problem in a rendered setup block."""

    problem = _precondition_structure_problem(preconditions)
    if problem is None:
        problem = _line_safe_passive_setup_problem(preconditions)
    return problem


def _runtime_sections(block: str) -> dict[str, str]:
    clean = _clean_block(block)
    heading_matches = list(MARKDOWN_HEADING.finditer(clean))
    sections: dict[str, list[str]] = {}
    for index, match in enumerate(heading_matches):
        section_id = SECTION_ALIASES.get(_normalized_title(match.group(1)))
        if section_id is None:
            continue
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(clean)
        )
        sections.setdefault(section_id, []).append(clean[match.end() : end].strip())

    if len(sections) == len(SECTION_NAMES):
        return {key: "\n".join(value) for key, value in sections.items()}

    bold_matches = list(BOLD_FIELD.finditer(clean))
    for index, match in enumerate(bold_matches):
        section_id = SECTION_ALIASES[_normalized_title(match.group(1))]
        if section_id in sections:
            continue
        end = (
            bold_matches[index + 1].start()
            if index + 1 < len(bold_matches)
            else len(clean)
        )
        inline = match.group(2).strip()
        following = clean[match.end() : end].strip()
        sections[section_id] = ["\n".join(item for item in (inline, following) if item)]
    return {key: "\n".join(value) for key, value in sections.items()}


def _normalized_identifier(value: str) -> str:
    value = unicodedata.normalize("NFKC", ZERO_WIDTH.sub("", value))
    value = value.translate(UNICODE_HYPHENS)
    return " ".join(value.split())


def _role_id_matches(
    text: str,
    pattern: re.Pattern[str],
) -> tuple[str, tuple[re.Match[str], ...]]:
    normalized = _visible_text(text, preserve_code_ticks=True)
    return normalized, tuple(pattern.finditer(normalized))


def _result_state_segment(
    text: str,
    match: re.Match[str],
    all_role_matches: tuple[re.Match[str], ...],
) -> str:
    next_role_offsets = [
        candidate.start()
        for candidate in all_role_matches
        if candidate.start() > match.start()
    ]
    end = min(next_role_offsets, default=len(text))
    segment = text[match.end() : end]
    return re.split(r"[.;\r\n]", segment, maxsplit=1)[0][:240]


def _optional_filter_oracle_problem(
    *,
    test_data: str,
    expected_result: str,
) -> str | None:
    _, data_targets = _role_id_matches(test_data, TARGET_ID_RE)
    _, data_controls = _role_id_matches(test_data, CONTROL_ID_RE)
    if len(data_targets) != 1 or len(data_controls) != 1:
        return (
            "Test data must contain exactly one `Номер целевой заявки` and "
            "one `Номер контрольной заявки` code literal."
        )

    target_id = _normalized_identifier(data_targets[0].group(1))
    control_id = _normalized_identifier(data_controls[0].group(1))
    if not target_id or not control_id:
        return "Target and control application numbers must be non-empty."
    if target_id.casefold() == control_id.casefold():
        return "Target and control application numbers must be distinct."

    expected_text, expected_targets = _role_id_matches(
        expected_result, TARGET_ID_RE
    )
    _, expected_controls = _role_id_matches(expected_result, CONTROL_ID_RE)
    if len(expected_targets) != 1 or len(expected_controls) != 1:
        return (
            "Expected result must repeat exactly one target and one control "
            "application number using the canonical role labels."
        )

    expected_target_id = _normalized_identifier(expected_targets[0].group(1))
    expected_control_id = _normalized_identifier(expected_controls[0].group(1))
    if expected_target_id != target_id or expected_control_id != control_id:
        return (
            "Expected-result application numbers must exactly match their "
            "target/control test-data bindings."
        )

    all_expected_matches = tuple(
        sorted(
            (*expected_targets, *expected_controls),
            key=lambda item: item.start(),
        )
    )
    target_state = _result_state_segment(
        expected_text, expected_targets[0], all_expected_matches
    )
    control_state = _result_state_segment(
        expected_text, expected_controls[0], all_expected_matches
    )
    if (
        POSITIVE_RESULT_STATE_RE.search(target_state) is None
        or NEGATED_POSITIVE_STATE_RE.search(target_state) is not None
        or DOUBLE_NEGATIVE_STATE_RE.search(target_state) is not None
    ):
        return (
            "The target application must have an unambiguously positive "
            "`отображается в таблице результатов` state."
        )
    if (
        NEGATIVE_RESULT_STATE_RE.search(control_state) is None
        or POSITIVE_RESULT_STATE_RE.search(control_state) is not None
        or DOUBLE_NEGATIVE_STATE_RE.search(control_state) is not None
    ):
        return (
            "The control application must have an unambiguously negative "
            "`не отображается в таблице результатов` state."
        )
    return None


def _compact_evidence(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:280]


@dataclass(frozen=True)
class ProductionTcGateResult:
    passed: bool
    test_case_count: int
    execution_ready_count: int
    calibration_candidate_count: int
    findings: tuple[dict[str, Any], ...]
    checked_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": VALIDATOR_NAME,
            "profile": "production-runtime-high-confidence",
            "test_case_count": self.test_case_count,
            "execution_ready_count": self.execution_ready_count,
            "calibration_candidate_count": self.calibration_candidate_count,
            "suite_readiness": (
                "ft-first-reviewed-with-calibration-pending"
                if self.calibration_candidate_count
                else "execution-ready"
            ),
            "checked_paths": list(self.checked_paths),
            "findings": list(self.findings),
        }


def _finding(
    *,
    finding_id: str,
    tc_id: str,
    section: str,
    evidence: str,
    message: str,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": "error",
        "tc_id": tc_id,
        "section": SECTION_NAMES.get(section, section),
        "evidence": _compact_evidence(evidence),
        "message": message,
    }


def validate_production_tc_content(
    content: str,
    *,
    checked_path: str = "<memory>",
    approved_runtime_aliases: Mapping[str, str] | None = None,
) -> ProductionTcGateResult:
    blocks = test_case_sections(content)
    findings: list[dict[str, Any]] = []
    execution_paths: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    runtime_aliases = tuple((approved_runtime_aliases or {}).items())
    if not blocks:
        findings.append(
            _finding(
                finding_id="production-tc-no-canonical-blocks",
                tc_id="",
                section="document",
                evidence="No TC-* headings found.",
                message="Production runtime validation requires canonical TC-* blocks.",
            )
        )
        return ProductionTcGateResult(
            passed=False,
            test_case_count=0,
            execution_ready_count=0,
            calibration_candidate_count=0,
            findings=tuple(findings),
            checked_paths=(checked_path,),
        )

    calibration_candidate_count = 0
    for tc_id, block in blocks:
        clean_block = _clean_block(block)
        sections = _runtime_sections(block)
        raw_preconditions = sections.get("preconditions", "")
        raw_test_data = sections.get("test_data", "")
        raw_steps = sections.get("steps", "")
        raw_expected_result = sections.get("expected_result", "")
        raw_postconditions = sections.get("postconditions", "")
        preconditions = _visible_text(raw_preconditions)
        test_data = _visible_text(raw_test_data)
        steps = _visible_text(raw_steps)
        expected_result = _visible_text(raw_expected_result)
        postconditions = _visible_text(raw_postconditions)
        execution_path_key = (
            " ".join(steps.casefold().split()),
            " ".join(expected_result.casefold().split()),
        )
        execution_paths.setdefault(execution_path_key, []).append(
            (tc_id, preconditions, "\n".join((test_data, steps, expected_result)))
        )
        candidate_oracle = CANDIDATE_ORACLE_STATUS_RE.search(clean_block) is not None
        candidate_status = CANDIDATE_TEST_CASE_STATUS_RE.search(clean_block) is not None
        is_calibration_candidate = candidate_oracle and candidate_status
        if is_calibration_candidate:
            calibration_candidate_count += 1

        runtime_sections = (
            ("preconditions", preconditions),
            ("test_data", test_data),
            ("steps", steps),
            ("expected_result", expected_result),
            ("postconditions", postconditions),
        )
        for alias, canonical_name in runtime_aliases:
            if not alias or alias.casefold() == canonical_name.casefold():
                continue
            for section, inspected_text in runtime_sections:
                match = re.search(re.escape(alias), inspected_text, re.IGNORECASE)
                if match is None:
                    continue
                findings.append(
                    _finding(
                        finding_id="production-noncanonical-approved-alias",
                        tc_id=tc_id,
                        section=section,
                        evidence=match.group(0),
                        message=(
                            f"Use the approved canonical field name `{canonical_name}` "
                            f"instead of alias `{alias}` in production runtime text."
                        ),
                    )
                )
                break

        title_match = TITLE_METADATA_RE.search(clean_block)
        title = title_match.group(1).strip() if title_match else ""
        if title.count("«") != title.count("»"):
            findings.append(
                _finding(
                    finding_id="production-unbalanced-title-quotes",
                    tc_id=tc_id,
                    section="metadata",
                    evidence=title,
                    message=(
                        "A TC title must not contain an unclosed Russian-style "
                        "quotation mark."
                    ),
                )
            )
        process_title_match = PROCESS_TITLE_RE.search(_visible_text(title))
        if process_title_match is not None:
            findings.append(
                _finding(
                    finding_id="production-process-marker-in-title",
                    tc_id=tc_id,
                    section="metadata",
                    evidence=process_title_match.group(0),
                    message=(
                        "A TC title must describe product behavior. Calibration, "
                        "fixture-validation and agent-process markers belong in "
                        "explicit body metadata."
                    ),
                )
            )

        for metadata_name, pattern in REQUIRED_METADATA.items():
            if pattern.search(clean_block) is not None:
                continue
            findings.append(
                _finding(
                    finding_id="production-required-metadata-missing",
                    tc_id=tc_id,
                    section="metadata",
                    evidence=metadata_name,
                    message=(
                        f"Production TC metadata `{metadata_name}` is missing "
                        "or empty."
                    ),
                )
            )

        for section_id, section_name in SECTION_NAMES.items():
            if sections.get(section_id, "").strip():
                continue
            findings.append(
                _finding(
                    finding_id="production-runtime-section-missing-or-empty",
                    tc_id=tc_id,
                    section=section_id,
                    evidence=section_name,
                    message=(
                        f"Production runtime section `{section_name}` is missing "
                        "or empty."
                    ),
                )
            )

        if candidate_oracle != candidate_status:
            findings.append(
                _finding(
                    finding_id="production-incomplete-calibration-lifecycle",
                    tc_id=tc_id,
                    section="metadata",
                    evidence="candidate calibration marker mismatch",
                    message=(
                        "A calibration candidate must declare both oracle status "
                        "and test-case status markers."
                    ),
                )
            )
        if is_calibration_candidate:
            confirmation = CANDIDATE_CONFIRMATION_RE.search(clean_block)
            confirmation_text = confirmation.group(1).strip() if confirmation else ""
            confirmation_tokens = re.findall(
                r"[A-Za-zА-ЯЁа-яё0-9]+", confirmation_text
            )
            if (
                confirmation is None
                or not confirmation_text.endswith("?")
                or len(confirmation_tokens) < 3
                or sum(map(len, confirmation_tokens)) < 12
            ):
                findings.append(
                    _finding(
                        finding_id="production-calibration-question-missing",
                        tc_id=tc_id,
                        section="metadata",
                        evidence="Требуется подтверждение",
                        message=(
                            "A calibration candidate must name the exact missing "
                            "observable UI reaction."
                        ),
                    )
                )
            transition_overclaim = CALIBRATION_TRANSITION_OVERCLAIM_RE.search(
                "\n".join((expected_result, postconditions))
            )
            if transition_overclaim is not None:
                findings.append(
                    _finding(
                        finding_id="production-calibration-transition-overclaim",
                        tc_id=tc_id,
                        section="expected_result",
                        evidence=transition_overclaim.group(0),
                        message=(
                            "A calibration candidate must preserve the confirmed "
                            "requiredness or optionality invariant without predicting "
                            "a blocked or permitted transition before UI calibration."
                        ),
                    )
                )
            calibration_inputs = "\n".join((raw_test_data, raw_steps))
            if (
                CONCRETE_CODE_LITERAL_RE.search(calibration_inputs) is None
                and CONCRETE_EMPTY_VALUE_RE.search(calibration_inputs) is None
                and CONCRETE_NAMED_VALUE_RE.search(calibration_inputs) is None
                and CALIBRATION_NO_ACTION_CONTROL_RE.search(calibration_inputs)
                is None
            ):
                findings.append(
                    _finding(
                        finding_id="production-calibration-value-missing",
                        tc_id=tc_id,
                        section="test_data",
                        evidence="\n".join((test_data, steps)),
                        message=(
                            "A calibration candidate must contain at least one "
                            "concrete boundary, invalid, empty or named-value "
                            "representative."
                        ),
                    )
                )

        checks = (
            (
                "production-setup-profile-reference",
                "preconditions",
                preconditions,
                SETUP_PROFILE_RE,
                "Production preconditions must be self-contained and must not reference setup profiles.",
            ),
            (
                "production-environment-specific-precondition",
                "preconditions",
                preconditions,
                ENVIRONMENT_RE,
                "Production preconditions must not depend on an unnamed test stand or environment.",
            ),
            (
                "production-package-name-leak",
                "preconditions",
                preconditions,
                PACKAGE_LEAK_RE,
                "Production preconditions must not leak project or FT package names.",
            ),
            (
                "production-magic-credential-setup",
                "preconditions",
                preconditions,
                MAGIC_CREDENTIAL_RE,
                "Credentials and accounts must be described by an executable access condition, not runtime/test-account placeholders.",
            ),
            (
                "production-generic-oracle",
                "expected_result",
                expected_result,
                GENERIC_ORACLE_RE,
                "The final expected result must name a concrete observable system outcome.",
            ),
            *(
                ()
                if is_calibration_candidate
                else (
                    (
                        "production-unobservable-oracle",
                        "expected_result",
                        expected_result,
                        UNOBSERVABLE_ORACLE_RE,
                        "Evidence collection, calibration and unresolved UI behavior are not executable final oracles.",
                    ),
                )
            ),
        )
        for finding_id, section, inspected_text, pattern, message in checks:
            match = pattern.search(inspected_text)
            if match is None:
                continue
            findings.append(
                _finding(
                    finding_id=finding_id,
                    tc_id=tc_id,
                    section=section,
                    evidence=match.group(0),
                    message=message,
                )
            )

        for section, inspected_text in (
            ("preconditions", preconditions),
            ("test_data", test_data),
            ("steps", steps),
        ):
            match = GENERIC_FIXTURE_RE.search(inspected_text)
            if match is None:
                continue
            findings.append(
                _finding(
                    finding_id="production-generic-fixture",
                    tc_id=tc_id,
                    section=section,
                    evidence=match.group(0),
                    message=(
                        "Production TCs require deterministic, concrete fixtures "
                        "rather than generic or generated placeholders."
                    ),
                )
            )

        for finding_id, section, inspected_text, pattern, message in (
            (
                "production-nonconcrete-runtime-value",
                "test_data",
                "\n".join((test_data, steps)),
                NONCONCRETE_RUNTIME_VALUE_RE,
                "Production test data must contain a concrete value, not a value selected from a changing list at runtime.",
            ),
            (
                "production-internal-fixture-artifact-leak",
                "test_data",
                "\n".join((preconditions, test_data, steps, postconditions)),
                INTERNAL_FIXTURE_ARTIFACT_RE,
                "Production runtime text must use projected fixture values and must not direct a tester to runner-owned paths, snapshots or verification artifacts.",
            ),
            (
                "production-out-of-scope-diagnostic-leak",
                "postconditions",
                postconditions,
                OUT_OF_SCOPE_KLADR_DIAGNOSTIC_RE,
                "A production TC must not contain diagnostics for behavior explicitly excluded from this project scope.",
            ),
        ):
            if finding_id == "production-nonconcrete-runtime-value":
                inspected_text = PROHIBITED_RUNTIME_LOOKUP_RE.sub(
                    "", inspected_text
                )
            match = pattern.search(inspected_text)
            if match is None:
                continue
            findings.append(
                _finding(
                    finding_id=finding_id,
                    tc_id=tc_id,
                    section=section,
                    evidence=match.group(0),
                    message=message,
                )
            )

        dadata_runtime = "\n".join(
            (preconditions, test_data, steps, expected_result, postconditions)
        )
        if DADATA_REFERENCE_RE.search(dadata_runtime) is not None:
            dynamic_match = DADATA_DYNAMIC_FIXTURE_RE.search(dadata_runtime)
            if dynamic_match is not None:
                findings.append(
                    _finding(
                        finding_id="production-dadata-dynamic-fixture",
                        tc_id=tc_id,
                        section="test_data",
                        evidence=dynamic_match.group(0),
                        message=(
                            "DaData values must be curated and verified before writer; "
                            "a TC must not discover or capture its fixture at runtime."
                        ),
                    )
                )
            if DADATA_FIXTURE_ID_RE.search(raw_test_data) is None:
                findings.append(
                    _finding(
                        finding_id="production-dadata-fixture-binding-missing",
                        tc_id=tc_id,
                        section="test_data",
                        evidence=test_data,
                        message=(
                            "Every DaData TC must bind a preverified FX-DADATA-* fixture "
                            "in test data."
                        ),
                    )
                )
            if DADATA_QUERY_LITERAL_RE.search(raw_test_data) is None:
                findings.append(
                    _finding(
                        finding_id="production-dadata-query-literal-missing",
                        tc_id=tc_id,
                        section="test_data",
                        evidence=test_data,
                        message="A DaData TC must contain the exact query literal.",
                    )
                )
            is_negative_dadata = DADATA_NEGATIVE_ORACLE_RE.search(
                "\n".join((test_data, expected_result))
            ) is not None
            if is_negative_dadata:
                if DADATA_EMPTY_SUGGESTIONS_RE.search(raw_test_data) is None:
                    findings.append(
                        _finding(
                            finding_id="production-dadata-negative-verification-missing",
                            tc_id=tc_id,
                            section="test_data",
                            evidence=test_data,
                            message=(
                                "A negative DaData fixture requires an exact "
                                "preverified `suggestions=[]` result. The catalog, "
                                "not the runtime TC, owns response hashes."
                            ),
                        )
                    )
            elif DADATA_SUGGESTION_LITERAL_RE.search(raw_test_data) is None:
                findings.append(
                    _finding(
                        finding_id="production-dadata-suggestion-literal-missing",
                        tc_id=tc_id,
                        section="test_data",
                        evidence=test_data,
                        message=(
                            "A positive DaData TC must contain the exact expected "
                            "suggestion literal."
                        ),
                    )
                )

        forbidden_sections = [
            ("preconditions", preconditions),
            ("test_data", test_data),
            ("steps", steps),
            ("postconditions", postconditions),
        ]
        if not is_calibration_candidate:
            forbidden_sections.append(("expected_result", expected_result))
        for section, inspected_text in forbidden_sections:
            match = FORBIDDEN_PROCESS_RE.search(inspected_text)
            if match is None:
                continue
            findings.append(
                _finding(
                    finding_id="production-forbidden-process-wording",
                    tc_id=tc_id,
                    section=section,
                    evidence=match.group(0),
                    message=(
                        "Production runtime sections must not contain workflow, "
                        "calibration or vague process wording."
                    ),
                )
            )

        optional_filter_check = (
            SEARCH_ACTION_RE.search(steps) is not None
            and OPTIONALITY_ABSENCE_RE.search(expected_result) is not None
        )
        oracle_problem = (
            _optional_filter_oracle_problem(
                test_data=raw_test_data,
                expected_result=raw_expected_result,
            )
            if optional_filter_check
            else None
        )
        if oracle_problem is not None:
            no_result_note = (
                " Split the optionality and no-result obligations into separate TCs."
                if NO_RESULT_RE.search(expected_result) is not None
                else ""
            )
            findings.append(
                _finding(
                    finding_id="production-optional-filter-result-oracle-missing",
                    tc_id=tc_id,
                    section="expected_result",
                    evidence="\n".join((test_data, expected_result)),
                    message=(
                        "A search-based optional-filter check requires distinct, "
                        "exact target/control application numbers and role-correct "
                        "result states. "
                        f"{oracle_problem}{no_result_note}"
                    ),
                )
            )

        address_component_fields = {
            match.group(0).casefold()
            for match in ADDRESS_COMPONENT_FIELD_RE.finditer(expected_result)
        }
        address_decomposition_oracle = (
            ADDRESS_DECOMPOSITION_ORACLE_RE.search(expected_result) is not None
            or (
                MANUAL_INPUT_BLOCK_RE.search(expected_result) is not None
                and len(address_component_fields) >= 2
            )
        )
        if address_decomposition_oracle:
            decomposition_findings: list[str] = []
            if DADATA_SELECTION_THEN_MANUAL_REVEAL_RE.search(steps) is None:
                decomposition_findings.append(
                    "manual fields are not revealed after selecting the DaData suggestion"
                )
            component_text = "\n".join((test_data, steps))
            structured_component_labels = {
                match.casefold()
                for match in DADATA_COMPONENT_LABEL_RE.findall(raw_test_data)
            }
            if (
                ADDRESS_COMPONENT_CAPTURE_RE.search(component_text) is None
                and len(structured_component_labels) < 2
            ):
                decomposition_findings.append(
                    "selected DaData components are not captured for field comparison"
                )
            if AMBIGUOUS_ADDRESS_BRANCH_RE.search(
                "\n".join((preconditions, steps))
            ) is not None:
                decomposition_findings.append(
                    "the registration/residence address branch is not selected explicitly"
                )
            if decomposition_findings:
                findings.append(
                    _finding(
                        finding_id="production-unobservable-address-decomposition",
                        tc_id=tc_id,
                        section="steps",
                        evidence="; ".join(decomposition_findings),
                        message=(
                            "An address-decomposition oracle must select one address "
                            "branch, capture the chosen DaData components, reveal the "
                            "manual fields after selection, and compare visible fields."
                        ),
                    )
                )

        precondition_problem = production_precondition_problem(preconditions)
        if precondition_problem is not None:
            findings.append(
                _finding(
                    finding_id="production-non-reproducible-precondition",
                    tc_id=tc_id,
                    section="preconditions",
                    evidence=precondition_problem,
                    message=(
                        "Preconditions must be the exact `Не требуются` sentinel "
                        "or a numbered action-oriented setup path. Observation-only "
                        "items require an earlier state-producing setup action."
                    ),
                )
            )

        numbered_steps = [
            match.group(1) for match in NUMBERED_LINE_RE.finditer(steps)
        ]
        numbered_actions = [
            step
            for step in numbered_steps
            if ACTION_STEP_RE.search(step)
            or RUSSIAN_INFINITIVE_STEP_RE.search(step)
        ]
        if not numbered_actions:
            findings.append(
                _finding(
                    finding_id="production-missing-numbered-action-step",
                    tc_id=tc_id,
                    section="steps",
                    evidence=steps or "<missing>",
                    message=(
                        "Production TCs require at least one numbered, executable "
                        "action or observation step."
                    ),
                )
            )
        persistence_evidence = persistence_claim(expected_result)
        if (
            not is_calibration_candidate
            and persistence_evidence is not None
            and not (
                has_commit_or_transition_after_mutation(numbered_steps)
                or (
                    UNSAVED_DIALOG_PRECONDITION_RE.search(preconditions)
                    is not None
                    and has_commit_or_transition_after_mutation(
                        numbered_steps,
                        mutation_already_occurred=True,
                        boundary_prompt_already_open=True,
                    )
                )
            )
        ):
            findings.append(
                _finding(
                    finding_id="production-persistence-without-commit-action",
                    tc_id=tc_id,
                    section="steps",
                    evidence=(
                        f"{persistence_evidence}; "
                        + (" | ".join(numbered_steps) or "<no action>")
                    ),
                    message=(
                        "A persistence oracle requires an explicit source-backed "
                        "save, confirmation, transition, submit or blur action. "
                        "Immediate selection/input alone proves only the visible "
                        "current value."
                    ),
                )
            )

    for duplicate_group in execution_paths.values():
        if len(duplicate_group) < 2:
            continue
        related_ids = ", ".join(item[0] for item in duplicate_group)
        for tc_id, preconditions, execution_text in duplicate_group:
            if DADATA_REFERENCE_RE.search(execution_text) is None:
                continue
            if GENERIC_ADDRESS_BLOCK_SETUP_RE.search(preconditions) is None:
                continue
            if SPECIFIC_ADDRESS_BRANCH_RE.search(preconditions) is not None:
                continue
            findings.append(
                _finding(
                    finding_id="production-ambiguous-duplicate-execution-path",
                    tc_id=tc_id,
                    section="preconditions",
                    evidence=f"same steps/oracle as {related_ids}: {preconditions}",
                    message=(
                        "Duplicate DaData execution paths must identify the exact "
                        "address branch in their setup. A generic address block can "
                        "nominally trace a second obligation while exercising the "
                        "first branch again."
                    ),
                )
            )

    return ProductionTcGateResult(
        passed=not findings,
        test_case_count=len(blocks),
        execution_ready_count=len(blocks) - calibration_candidate_count,
        calibration_candidate_count=calibration_candidate_count,
        findings=tuple(findings),
        checked_paths=(checked_path,),
    )


def validate_production_tc_draft(*, draft_path: Path) -> ProductionTcGateResult:
    return validate_production_tc_content(
        draft_path.read_text(encoding="utf-8"),
        checked_path=str(draft_path),
    )
