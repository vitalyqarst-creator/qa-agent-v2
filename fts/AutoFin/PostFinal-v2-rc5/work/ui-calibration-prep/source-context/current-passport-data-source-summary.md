# Source context summary — current passport data

Scope test-case file:

`fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-current-passport-data.md`

UI calibration нужно выполнить только для кейсов со статусом:

```text
candidate-ui-calibration
```

Основные темы калибровки:

- фактическая реакция UI на короткие значения точной длины для серии, номера и кода подразделения;
- фактическая реакция UI на граничные даты выдачи паспорта;
- точный trigger проверки: ввод, blur, сохранение, переход далее или другой UI action;
- точный observable result: сообщение, подсветка, блокировка, сохранение/несохранение.

Не заменяй observed UI reaction предположениями по ФТ.

