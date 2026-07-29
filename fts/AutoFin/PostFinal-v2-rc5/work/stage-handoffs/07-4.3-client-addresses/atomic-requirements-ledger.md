# Atomic Requirements Ledger

| atom_id | source_property_id | atomic_statement | coverage_status | source_row_id | requirement_codes | constraint_gap_ids |
| --- | --- | --- | --- | --- | --- | --- |
| ATOM-ADDR-001 | PROP-ADDR-001 | Строка заголовков таблицы свойств полей задает контекст колонок и не является самостоятельной UI-проверкой. | not-applicable | SRC-ROW-001 | none_required | none_required |
| ATOM-ADDR-002 | PROP-ADDR-002 | Строка является заголовком блока «Адреса клиента» и не задает самостоятельную исполнимую проверку. | not-applicable | SRC-ROW-002 | none_required | none_required |
| ATOM-ADDR-003 | PROP-ADDR-003 | Поле «Адрес регистрации» всегда видимо. | covered | SRC-ROW-003 | BSR 115 | none_required |
| ATOM-ADDR-004 | PROP-ADDR-004 | Поле «Адрес регистрации» использует интеграцию с DaData. | covered | SRC-ROW-003 | BSR 116 | none_required |
| ATOM-ADDR-005 | PROP-ADDR-005 | Для адреса регистрации должны быть введены регион и номер дома. | covered | SRC-ROW-003 | BSR 117 | none_required |
| ATOM-ADDR-006 | PROP-ADDR-006 | Если в адресе регистрации не указана квартира и не отмечен частный дом, поле подсвечивается красным и отображается подсказка о квартире или частном доме. | covered | SRC-ROW-003 | BSR 117 | none_required |
| ATOM-ADDR-007 | PROP-ADDR-007 | Если DaData не находит адрес регистрации, отображается подсказка «Некорректно указан адрес». | covered | SRC-ROW-003 | BSR 118 | none_required |
| ATOM-ADDR-008 | PROP-ADDR-008 | Если адрес регистрации найден в DaData, он раскладывается по полям блока ручного ввода. | covered | SRC-ROW-003 | BSR 119 | none_required |
| ATOM-ADDR-009 | PROP-ADDR-009 | При ручном заполнении поле «Адрес регистрации» автоматически формируется из ручных адресных полей. | covered | SRC-ROW-003 | BSR 120 | none_required |
| ATOM-ADDR-010 | PROP-ADDR-010 | Признак «Ввести вручную» для адреса регистрации всегда видим. | covered | SRC-ROW-004 | BSR 121 | none_required |
| ATOM-ADDR-011 | PROP-ADDR-011 | Значение по умолчанию для «Ввести вручную» адреса регистрации равно «Нет». | covered | SRC-ROW-004 | BSR 122 | none_required |
| ATOM-ADDR-012 | PROP-ADDR-012 | Поле «Почтовый индекс» адреса регистрации видимо, если «Ввести вручную» = «Да». | covered | SRC-ROW-005 | BSR 123 | none_required |
| ATOM-ADDR-013 | PROP-ADDR-013 | Почтовый индекс адреса регистрации допускает только 6 числовых символов. | covered | SRC-ROW-005 | BSR 124 | GAP-003 |
| ATOM-ADDR-014 | PROP-ADDR-014 | Поле «Регион» адреса регистрации видимо в ручном режиме и использует справочник регионов. | covered | SRC-ROW-006 | BSR 125 | none_required |
| ATOM-ADDR-015 | PROP-ADDR-015 | Поле «Район» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-007 | BSR 126 | none_required |
| ATOM-ADDR-016 | PROP-ADDR-016 | Поле «Населенный пункт» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-008 | BSR 127 | none_required |
| ATOM-ADDR-017 | PROP-ADDR-017 | Поле «Город» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-009 | BSR 128 | none_required |
| ATOM-ADDR-018 | PROP-ADDR-018 | Поле «Улица» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-010 | BSR 129 | none_required |
| ATOM-ADDR-019 | PROP-ADDR-019 | Поле «Дом» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-011 | BSR 130 | none_required |
| ATOM-ADDR-020 | PROP-ADDR-020 | Поле «Корпус» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-012 | BSR 131 | none_required |
| ATOM-ADDR-021 | PROP-ADDR-021 | Поле «Корпус» адреса регистрации допускает ввод только числовых символов. | covered | SRC-ROW-012 | BSR 132 | GAP-003 |
| ATOM-ADDR-022 | PROP-ADDR-022 | Поле «Квартира» адреса регистрации видимо в ручном режиме. | covered | SRC-ROW-013 | BSR 133 | none_required |
| ATOM-ADDR-023 | PROP-ADDR-023 | Поле «Квартира» адреса регистрации допускает ввод только числовых символов. | covered | SRC-ROW-013 | BSR 134 | GAP-003 |
| ATOM-ADDR-024 | PROP-ADDR-024 | Флажок «Клиент зарегистрирован в частном доме» отображается только если в адресе регистрации не указан номер квартиры. | covered | SRC-ROW-014 | BSR 135 | none_required |
| ATOM-ADDR-025 | PROP-ADDR-025 | Значение по умолчанию для «Клиент зарегистрирован в частном доме» равно «Нет». | covered | SRC-ROW-014 | BSR 136 | none_required |
| ATOM-ADDR-026 | PROP-ADDR-026 | Если флажок «Клиент зарегистрирован в частном доме» активирован, подсказка о квартире или частном доме исчезает с поля адреса регистрации. | covered | SRC-ROW-014 | BSR 137 | none_required |
| ATOM-ADDR-027 | PROP-ADDR-027 | Признак совпадения фактического адреса с адресом регистрации всегда видим. | covered | SRC-ROW-015 | BSR 138 | none_required |
| ATOM-ADDR-028 | PROP-ADDR-028 | Значение по умолчанию для признака совпадения фактического адреса с адресом регистрации равно «Да». | covered | SRC-ROW-015 | BSR 139 | none_required |
| ATOM-ADDR-029 | PROP-ADDR-029 | Поле «Адрес фактического места жительства» видимо, если признак совпадения с адресом регистрации = «Нет». | covered | SRC-ROW-016 | BSR 140 | none_required |
| ATOM-ADDR-030 | PROP-ADDR-030 | Поле «Адрес фактического места жительства» использует интеграцию с DaData. | covered | SRC-ROW-016 | BSR 141 | none_required |
| ATOM-ADDR-031 | PROP-ADDR-031 | Для фактического адреса должны быть введены регион и номер дома. | covered | SRC-ROW-016 | BSR 142 | none_required |
| ATOM-ADDR-032 | PROP-ADDR-032 | Если в фактическом адресе не указана квартира и не отмечен частный дом, поле подсвечивается красным и отображается подсказка о квартире или частном доме. | covered | SRC-ROW-016 | BSR 142 | none_required |
| ATOM-ADDR-033 | PROP-ADDR-033 | Если DaData не находит фактический адрес, отображается подсказка «Некорректно указан адрес». | covered | SRC-ROW-016 | BSR 143 | none_required |
| ATOM-ADDR-034 | PROP-ADDR-034 | Если фактический адрес найден в DaData, он раскладывается по полям блока ручного ввода. | covered | SRC-ROW-016 | BSR 144 | none_required |
| ATOM-ADDR-035 | PROP-ADDR-035 | При ручном заполнении поле фактического адреса автоматически формируется из ручных адресных полей. | covered | SRC-ROW-016 | BSR 145 | none_required |
| ATOM-ADDR-036 | PROP-ADDR-036 | Флажок «Клиент проживает в частном доме» видим, если адреса не совпадают и в фактическом адресе не указана квартира. | covered | SRC-ROW-017 | BSR 146 | none_required |
| ATOM-ADDR-037 | PROP-ADDR-037 | Значение по умолчанию для «Клиент проживает в частном доме» равно «Нет». | covered | SRC-ROW-017 | BSR 147 | none_required |
| ATOM-ADDR-038 | PROP-ADDR-038 | Признак «Ввести вручную» для фактического адреса видим, если адреса не совпадают. | covered | SRC-ROW-018 | BSR 148 | none_required |
| ATOM-ADDR-039 | PROP-ADDR-039 | Значение по умолчанию для «Ввести вручную» фактического адреса равно «Нет». | covered | SRC-ROW-018 | BSR 149 | none_required |
| ATOM-ADDR-040 | PROP-ADDR-040 | Поле «Регион» фактического адреса видимо в ручном режиме и использует справочник регионов. | covered | SRC-ROW-019 | BSR 150 | none_required |
| ATOM-ADDR-041 | PROP-ADDR-041 | Поле «Район» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-020 | BSR 151 | none_required |
| ATOM-ADDR-042 | PROP-ADDR-042 | Поле «Населенный пункт» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-021 | BSR 152 | none_required |
| ATOM-ADDR-043 | PROP-ADDR-043 | Поле «Город» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-022 | BSR 153 | none_required |
| ATOM-ADDR-044 | PROP-ADDR-044 | Поле «Улица» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-023 | BSR 154 | none_required |
| ATOM-ADDR-045 | PROP-ADDR-045 | Поле «Дом» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-024 | BSR 155 | none_required |
| ATOM-ADDR-046 | PROP-ADDR-046 | Поле «Корпус» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-025 | BSR 156 | none_required |
| ATOM-ADDR-047 | PROP-ADDR-047 | Поле «Квартира» фактического адреса обязательно, если «Клиент проживает в частном доме» = «Нет». | covered | SRC-ROW-026 | BSR 157 | GAP-003 |
| ATOM-ADDR-048 | PROP-ADDR-048 | Поле «Квартира» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-026 | BSR 158 | none_required |
| ATOM-ADDR-049 | PROP-ADDR-049 | Поле «Квартира» фактического адреса допускает ввод только числовых символов. | covered | SRC-ROW-026 | BSR 159 | GAP-003 |
| ATOM-ADDR-050 | PROP-ADDR-050 | Поле «Почтовый индекс» фактического адреса видимо в ручном режиме. | covered | SRC-ROW-027 | BSR 160 | none_required |
| ATOM-ADDR-051 | PROP-ADDR-051 | Почтовый индекс фактического адреса отклоняет нечисловые символы. | covered | SRC-ROW-027 | BSR 161 | GAP-003 |
| ATOM-ADDR-052 | PROP-ADDR-052 | Почтовый индекс фактического адреса отклоняет значение короче 6 числовых символов. | covered | SRC-ROW-027 | BSR 161 | GAP-003 |
| ATOM-ADDR-053 | PROP-ADDR-053 | Почтовый индекс фактического адреса отклоняет значение длиннее 6 числовых символов. | covered | SRC-ROW-027 | BSR 161 | GAP-003 |
| ATOM-ADDR-054 | PROP-ADDR-054 | Если адрес клиента заполнен посредством запроса DaData, он раскладывается по полям блока ручного ввода. | covered | SRC-ROW-028 | BSR 324 | none_required |
| ATOM-ADDR-055 | PROP-ADDR-055 | Внутреннее заполнение модели данных `kladr` исключено из исполнимого UI scope AutoFin и проверяется отдельно. | not-applicable | SRC-ROW-028 | none_required | none_required |
| ATOM-ADDR-056 | PROP-ADDR-056 | Поле «Населенный пункт» адреса регистрации обязательно, если поле «Город» не заполнено. | covered | SRC-ROW-008 | none_required | GAP-003 |
| ATOM-ADDR-057 | PROP-ADDR-057 | Поле «Город» адреса регистрации обязательно, если поле «Населенный пункт» не заполнено. | covered | SRC-ROW-009 | none_required | GAP-003 |
| ATOM-ADDR-058 | PROP-ADDR-058 | Поле «Дом» адреса регистрации обязательно. | covered | SRC-ROW-011 | none_required | GAP-003 |
| ATOM-ADDR-059 | PROP-ADDR-059 | Поле «Квартира» адреса регистрации обязательно, если «Клиент зарегистрирован в частном доме» = «Нет». | covered | SRC-ROW-013 | none_required | GAP-003 |
| ATOM-ADDR-060 | PROP-ADDR-060 | Поле «Город» фактического адреса обязательно. | covered | SRC-ROW-022 | none_required | GAP-003 |
| ATOM-ADDR-061 | PROP-ADDR-061 | Поле «Улица» фактического адреса обязательно. | covered | SRC-ROW-023 | none_required | GAP-003 |
| ATOM-ADDR-062 | PROP-ADDR-062 | Поле «Дом» фактического адреса обязательно. | covered | SRC-ROW-024 | none_required | GAP-003 |
