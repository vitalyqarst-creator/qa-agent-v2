# TC-DOC-022 text evidence

Action: uploaded transient file big-over-40mb.pdf (41MB) into questionnaire file input.

Observed UI text immediately after recovery from screenshot timeout:

```text
Документы по заявке ПРИКРЕПИТЬ С ТЕЛЕФОНА Анкета клиента Распечатайте, подпишите с клиентом и загрузите скан в заявку Скачать (документ) emptyTranslationsKey big-over-40mb.pdf emptyTranslationsKey dummy-second.pdf Серия Номер emptyTranslationsKey dummy-passport.pdf Тип документа Загран. паспорт Дата выдачи Дата не может быть больше 30.07.2026. Кем выдан Согласия/Проверки Визуальная информация Визуальная информация ДАЛЕЕ Произошла непредвиденная ошибка. Обратитесь к администратору
```

Note: screenshot call timed out after 30s during/after large upload. Transient >40MB file was removed from disk after execution.
