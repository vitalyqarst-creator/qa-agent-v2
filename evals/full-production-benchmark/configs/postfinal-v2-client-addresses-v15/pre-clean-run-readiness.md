# Готовность clean benchmark v15

Статус: `ready-for-clean-run`.

Подготовлен один независимый schema-v2 observation-run для scope `application-card-client-addresses`. Он выпускает только новый shadow-файл и не читает/не перезаписывает действующий canonical.

## Проверено

- schema-v2 config прошёл `--validate-only` без model-вызовов;
- environment probe этого компьютера сохранён отдельно, поэтому новый turn может начать измерение с Codex metadata без предварительной shell-команды;
- SHA-256 DOCX, XHTML, PDF, mockup, DaData reference, package notes и approved clarifications совпадают с registry;
- handoff `96`, cycle и shadow destination отсутствуют и свободны;
- устранено дублирование номера handoff `95` с завершённой canonical reconciliation;
- 477 целевых тестов bootstrap/source/semantic/review/promotion прошли за 141,505 с;
- после исправления стартового контракта прошли 41 protocol/bootstrap-тест и
  108 соседних timing/execution/architecture-тестов;
- instruction context `iteration.checked_in_observation` занимает 57,4 из
  75,0 KiB, архитектурный аудит: 63 проверки, 0 findings;
- UI-калибровка исключена из запуска по решению пользователя;
- шардирование остаётся последовательным;
- retry, fallback, resume и исправления внутри clean benchmark запрещены.

Первая передача запуска была остановлена до benchmark, потому что metadata
прочитал subagent. Вторую выполнял primary root-agent, но она выявила реальное
противоречие инструкций: обязательное чтение project/skill-контекста было
несовместимо со старым требованием сделать metadata первым инструментальным
действием. Ни в одном task wrapper и outputs не создавались, поэтому v15 не
израсходован.

Контракт теперь разрешает ограниченный pre-bootstrap preflight только для routing,
обязательных инструкций и сохранённого environment probe. Затем primary root-agent
без промежуточных task actions выполняет пару metadata-bootstrap. Timer открывается
от исходного timestamp запроса, поэтому подготовка остаётся внутри
`routing-preflight`.

## Защищённый baseline

`fts/AutoFin/test-cases/14-application-card-client-addresses.md`

SHA-256: `dc51b317ab4547576f1d72674a50445dbe9e81d03c26b2ede317f924c98020af`, 109 тест-кейсов.

## Запуск

В новой сессии передать агенту без изменений содержимое `launch-new-session.md`.
Агент сначала выполняет явно разрешённый ограниченный pre-bootstrap preflight,
затем получает фактические metadata нового Codex turn и выполняет ровно один
`start_full_process_observation.py --execute`.

Разработка, диагностика и сравнение с canonical выполняются только после terminal result и вне clean benchmark-сессии.
