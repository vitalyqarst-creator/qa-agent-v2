# UI Evidence Index: 4.3 Three Files UI Pass

Scope: `4.3-contact-persons`, `4.3-current-passport-data`, `4.3-personal-data`

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`

Date: 2026-07-30

## Screenshots

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/launch-page.png` - application launch page; `cff` must be selected before `ЗАПУСТИТЬ`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/initial-card.png` - new application card initial state.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-clean-card.png` - clean personal-data block.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-required-after-next.png` - personal-data required validation after `ДАЛЕЕ`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-after-probes.png` - personal-data text/date probes.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-previous-fio-after-next.png` - previous-FIO fields after enabling `Клиент менял ФИО`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-dadata-ivanova.png` - DaData/FIO probe for `Иванова`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-dadata-ivanov.png` - DaData/FIO probe for `Иванов`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/personal-dob-boundaries.png` - personal DOB boundary probes.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/passport-required-after-next.png` - current passport required validation after `ДАЛЕЕ`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/passport-after-probes.png` - current passport format/date probes.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/passport-issued-by-focus-after-code.png` - `Кем выдан` dropdown after department code focus.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/passport-issued-by-selected.png` - `Кем выдан` after selecting first suggestion.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/passport-issued-by-selected-after-blur.png` - `Кем выдан` valid after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/contact-block-current.png` - contacts block before adding contact person.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/contact-person-focused-after-add.png` - contact person row after `ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/contact-person-focused-probes.png` - contact person format/dropdown probes.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/contact-person-after-validation.png` - contacts validation state after `ДАЛЕЕ`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/contact-person-after-delete-attempt.png` - delete attempt context; not reliable for contact-person delete.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-after-add-rerun.png` - contact-person row after rerun add action.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-after-delete-click-rerun.png` - contact-person row deleted after clicking row delete icon; no confirmation dialog observed.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-after-other-rerun.png` - `иное` selected in `Отношение к заявителю`; no extra text field appeared.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-fio-suggestions-rerun.png` - contact FIO suggestion probing.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-manual-fio-after-blur-rerun.png` - contact name/patronymic manual values after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-surname-petrov-boyarov-manual-blur.png` - `Петров-Бояров` manually entered into contact surname and retained after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-surname-petrov-boyarov-select-blur.png` - exact dropdown option `Петров-Бояров` selected and retained after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-contact-persons/contact-surname-suggestion-selected-rerun.png` - surname suggestion selected and retained after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/current-visible-card-before-slow-rerun.png` - visible Chrome application card before the final slow-input DaData rerun.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-surname-ivanova-final-dropdown.png` - slow input `Иванова`; `li.ui-menu-item` options include `Иванов`, `Иванова`, `Ивановская`, `Ивановский`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-surname-ivanova-final-after-select.png` - selected `Иванова`; surname valid after blur and gender set to `Женский`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-surname-ivanov-final-dropdown.png` - slow input `Иванов`; `li.ui-menu-item` options include `Иванов`, `Иванова`, `Ивановская`, `Ивановский`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-surname-ivanov-final-after-select.png` - selected `Иванов`; surname valid after blur and gender set to `Мужской`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-name-ivan-final-dropdown.png` - slow input `Иван`; `li.ui-menu-item` options include `Иван`, `Иванна`, `Ивана`, `Иванка`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-name-ivan-final-after-select.png` - selected `Иван`; name valid after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-patronymic-ivanovich-final-dropdown.png` - slow input `Иванович`; `li.ui-menu-item` options include `Ивановна` and `Иванович`.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-current-patronymic-ivanovich-final-after-select.png` - selected current patronymic `Иванович`; value valid after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-surname-ivanov-final-dropdown.png` - slow input previous surname `Иванов`; `li.ui-menu-item` options visible.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-surname-ivanov-final-after-select.png` - selected previous surname `Иванов`; value valid after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-name-ivan-final-dropdown.png` - slow input previous name `Иван`; `li.ui-menu-item` options visible.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-name-ivan-final-after-select.png` - selected previous name `Иван`; value valid after blur.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-patronymic-ivanovich-final-dropdown.png` - slow input previous patronymic `Иванович`; `li.ui-menu-item` options visible.
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/evidence/screenshots/rerun-personal-dadata/slow-visible-prev-patronymic-ivanovich-final-after-select.png` - selected previous patronymic `Иванович`; value valid after blur.
