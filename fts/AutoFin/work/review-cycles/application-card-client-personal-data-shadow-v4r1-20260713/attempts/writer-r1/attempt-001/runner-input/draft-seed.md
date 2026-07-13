# Тест-кейсы

<!-- PREPARED-DRAFT-SEED: replace all [SEED:*] values before completion -->

## TC-ACPD-001

**Название:** [SEED:title:ATOM-001+ATOM-002+ATOM-007+ATOM-012]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-001; ATOM-001; SRC-001; SRC-001.P01; OBL-002; ATOM-002; SRC-002; SRC-002.P01; OBL-009; ATOM-007; SRC-003; SRC-003.P01; OBL-016; ATOM-012; SRC-004; SRC-004.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Блок `Персональные данные` отображается в карточке заявки.; Поле `Фамилия` отображается всегда.; Поле `Имя` отображается всегда.; Поле `Отчество` отображается всегда.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-002

**Название:** [SEED:title:ATOM-004+ATOM-009+ATOM-014]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-004; ATOM-004; SRC-002; SRC-002.P03; OBL-011; ATOM-009; SRC-003; SRC-003.P03; OBL-018; ATOM-014; SRC-004; SRC-004.P03

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Фамилия` доступно для редактирования.; Поле `Имя` доступно для редактирования.; Поле `Отчество` доступно для редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-003

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-005; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Фамилия` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-004

**Название:** [SEED:title:ATOM-006]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-008; ATOM-006; SRC-002; SRC-002.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Фамилия` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-005

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-012; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Имя` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-006

**Название:** [SEED:title:ATOM-011]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-015; ATOM-011; SRC-003; SRC-003.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Имя` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-007

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-019; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Отчество` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-008

**Название:** [SEED:title:ATOM-016]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-022; ATOM-016; SRC-004; SRC-004.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Отчество` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-009

**Название:** [SEED:title:ATOM-017]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-023; ATOM-017; SRC-005; SRC-005.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `ID клиента` отображается всегда и недоступен для ручного редактирования.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-010

**Название:** [SEED:title:ATOM-018]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-024; ATOM-018; SRC-005; SRC-005.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] После save видимый `ID клиента` изменился с пустого на непустой; значение записано, ABS-атрибуция не утверждается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-011

**Название:** [SEED:title:ATOM-019]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-025; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле `Пол` отображается, редактируемо и использует активные значения `DICT-001`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-012

**Название:** [SEED:title:ATOM-020]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-027; ATOM-020; SRC-006; SRC-006.P02
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Видимый `Пол` совпал с expected fixture; до/после записаны, provider-attribution не утверждается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-013

**Название:** [SEED:title:ATOM-021]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-028; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Поле видимо, редактируемо и отображает введённую логическую дату `D-30 лет`; формат/виджет не утверждаются.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-014

**Название:** [SEED:title:ATOM-022+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-030; ATOM-022; SRC-007; SRC-007.P02; OBL-035; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Дата `D-18 лет` соответствует верхней возрастной границе.; Граница `D-18 лет` вычисляется относительно текущей даты приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-015

**Название:** [SEED:title:ATOM-024+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-033; ATOM-024; SRC-007; SRC-007.P04; OBL-036; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Дата `D-100 лет` соответствует нижней возрастной границе.; Граница `D-100 лет` вычисляется относительно текущей даты приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-016

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-006; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-017

**Название:** [SEED:title:ATOM-005]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-007; ATOM-005; SRC-002; SRC-002.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-018

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-013; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-019

**Название:** [SEED:title:ATOM-010]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-014; ATOM-010; SRC-003; SRC-003.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-020

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-020; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-021

**Название:** [SEED:title:ATOM-015]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-021; ATOM-015; SRC-004; SRC-004.P04
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-022

**Название:** [SEED:title:ATOM-003]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-003; ATOM-003; SRC-002; SRC-002.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Evidence содержит control/action/empty `Фамилия`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-023

**Название:** [SEED:title:ATOM-008]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-010; ATOM-008; SRC-003; SRC-003.P02
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Evidence содержит control/action/empty `Имя`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-024

**Название:** [SEED:title:ATOM-019]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-026; ATOM-019; SRC-006; SRC-006.P01; DICT-001
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Evidence содержит control/action/empty `Пол`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-025

**Название:** [SEED:title:ATOM-021]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-029; ATOM-021; SRC-007; SRC-007.P01
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Evidence содержит control/action/empty `Дата рождения`/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-026

**Название:** [SEED:title:ATOM-022+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-031; ATOM-022; SRC-007; SRC-007.P02; OBL-037; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Дата позже `D-18 лет` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения позже `D-18 лет` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-027

**Название:** [SEED:title:ATOM-023+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-032; ATOM-023; SRC-007; SRC-007.P03; OBL-038; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Дата больше текущей даты `D` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения больше `D` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-028

**Название:** [SEED:title:ATOM-024+ATOM-025]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-034; ATOM-024; SRC-007; SRC-007.P04; OBL-039; ATOM-025; SRC-007.P05
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Дата раньше `D-100 лет` не соответствует ограничению; точная UI-реакция не определена.; Проверка значения раньше `D-100 лет` использует текущую дату приложения `D`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-029

**Название:** [SEED:title:ATOM-026]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-040; ATOM-026; SRC-008; SRC-008.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Клиент менял ФИО` отображается всегда как переключатель `Да/Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-030

**Название:** [SEED:title:ATOM-027]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-041; ATOM-027; SRC-008; SRC-008.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение по умолчанию `Клиент менял ФИО` равно `Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-031

**Название:** [SEED:title:ATOM-028+ATOM-033+ATOM-038]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-042; ATOM-028; SRC-009; SRC-009.P01; OBL-050; ATOM-033; SRC-010; SRC-010.P01; OBL-058; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` отображается при `Клиент менял ФИО=Да`.; `Предыдущее имя` отображается при `Клиент менял ФИО=Да`.; `Предыдущее отчество` отображается при `Клиент менял ФИО=Да`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-032

**Название:** [SEED:title:ATOM-028+ATOM-033+ATOM-038]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-043; ATOM-028; SRC-009; SRC-009.P01; OBL-051; ATOM-033; SRC-010; SRC-010.P01; OBL-059; ATOM-038; SRC-011; SRC-011.P01

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` не отображается при `Клиент менял ФИО=Нет`.; `Предыдущее имя` не отображается при `Клиент менял ФИО=Нет`.; `Предыдущее отчество` не отображается при `Клиент менял ФИО=Нет`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-033

**Название:** [SEED:title:ATOM-029+ATOM-034+ATOM-039]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-044; ATOM-029; SRC-009; SRC-009.P02; OBL-052; ATOM-034; SRC-010; SRC-010.P02; OBL-060; ATOM-039; SRC-011; SRC-011.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` редактируема при выполнении условия видимости.; `Предыдущее имя` редактируемо при выполнении условия видимости.; `Предыдущее отчество` редактируемо при выполнении условия видимости.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-034

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-045; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущая фамилия` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-035

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-046; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-036

**Название:** [SEED:title:ATOM-030]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-047; ATOM-030; SRC-009; SRC-009.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущая фамилия`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-037

**Название:** [SEED:title:ATOM-032]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-049; ATOM-032; SRC-009; SRC-009.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Предыдущая фамилия` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-038

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-053; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущее имя` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-039

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-054; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-040

**Название:** [SEED:title:ATOM-035]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-055; ATOM-035; SRC-010; SRC-010.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее имя`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-041

**Название:** [SEED:title:ATOM-031+ATOM-036+ATOM-041]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-048; ATOM-031; SRC-009; SRC-009.P04; OBL-056; ATOM-036; SRC-010; SRC-010.P04; OBL-064; ATOM-041; SRC-011; SRC-011.P04
**Coverage gap:** GAP-002
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Evidence содержит control/action/condition/empty previous-FIO/post-state/persistence; UI-механизм не предписывается.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-042

**Название:** [SEED:title:ATOM-037]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-057; ATOM-037; SRC-010; SRC-010.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Предыдущее имя` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-043

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-061; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] `Предыдущее отчество` допускает текстовые символы и символ `-`.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-044

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-062; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение с цифрой не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-045

**Название:** [SEED:title:ATOM-040]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-063; ATOM-040; SRC-011; SRC-011.P03
**Coverage gap:** GAP-001
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Значение со спецсимволом кроме `-` не является допустимым для `Предыдущее отчество`; механизм UI-отклонения не задан.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-046

**Название:** [SEED:title:ATOM-042]
**Тип:** негативный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-065; ATOM-042; SRC-011; SRC-011.P05
**Coverage gap:** GAP-003
**Статус oracle:** ui-calibration-required
**Статус тест-кейса:** candidate-ui-calibration

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Для `Предыдущее отчество` допускаются подсказки DaData при доступной интеграции.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]

## TC-ACPD-047

**Название:** [SEED:title:ATOM-013]
**Тип:** позитивный
**Приоритет:** средний
**package_id:** [SEED:package_id]
**Трассировка:** OBL-017; ATOM-013; SRC-004; SRC-004.P02

### Предусловия

1. [SEED:reproducible setup]

### Тестовые данные

- [SEED:concrete permitted data or parameter]

### Шаги

1. [SEED:user action]

### Итоговый ожидаемый результат

[SEED:observable oracle] Save завершён; после повторного открытия `Отчество` пусто и не блокировало сохранение.

### Постусловия

- [SEED:postcondition or explicit not-applicable reason]
