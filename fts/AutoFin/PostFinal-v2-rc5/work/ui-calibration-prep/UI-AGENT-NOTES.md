# UI calibration notes

Работай только как UI-калибровщик готовых FT-first test cases.

## Запрещено

- Не запускать `ft-source-locator`, `ft-scope-analyzer`, writer/reviewer iteration, bridge, benchmark или sharding.
- Не генерировать новые тест-кейсы.
- Не менять `fts/AutoFin/PostFinal-v2-rc5/test-cases/*.md` напрямую.
- Не додумывать UI-реакцию, если она не была увидена на стенде.
- Не заменять фактическое поведение предположениями из ФТ.

## Разрешено

- Открывать стенд и выполнять только calibration-кейсы из `ui-calibration-index.md`.
- Делать скриншоты, сохранять URL/route, роль пользователя, тестовые данные, observed UI reaction.
- Создавать файлы evidence в `work/ui-calibration-prep/results/`.
- Если кейс невозможно выполнить из-за отсутствия данных/доступа, фиксировать `blocked-ui-input`, а не менять expected result.

## Формат результата по каждому TC

Для каждого `TC-ID` зафиксируй:

- `tc_id`;
- исходный файл test-cases;
- роль/учетка, если применимо;
- точные тестовые данные;
- точный action/trigger, которым запускалась проверка;
- observed UI reaction;
- screenshot/evidence path;
- вывод: `confirmed`, `needs-test-case-update`, `blocked-ui-input`, `not-reproducible`;
- что нужно внести в test-case после калибровки.

## Главный критерий

После калибровки должно стать понятно, можно ли перевести `candidate-ui-calibration` case в executable/automation-ready без выдумывания поведения.

