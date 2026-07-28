# Source context summary — contact persons

Scope test-case file:

`fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-contact-persons.md`

UI calibration нужно выполнить только для кейсов со статусом:

```text
candidate-ui-calibration
```

Основные темы калибровки:

- обязательность полей после добавления контактного лица;
- фактическая реакция UI на недопустимые символы в ФИО;
- фактическая реакция UI на некорректный телефон;
- проверка необязательности отчества;
- фактическая реакция UI на будущую дату рождения.

Если в UI обнаружена интеграция с DaData в полях ФИО, зафиксируй это как observation. Не переписывай expected result без отдельной update-задачи.

