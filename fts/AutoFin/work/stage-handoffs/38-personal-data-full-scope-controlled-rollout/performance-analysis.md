# Анализ производительности

## Live writer

| metric | value |
| --- | ---: |
| duration | 233.375 s |
| input tokens | 37 859 |
| output tokens | 12 658 |
| total tokens | 50 517 |
| primary context | 96 886 bytes |
| commands / file changes | 0 / 0 |
| generated TC | 47 |

Writer успел сформировать содержательно полный draft; остановка произошла после генерации на дешёвом deterministic gate.

## Подготовка compiler inputs

Отдельная input-preparation exec session `019f5980-cca3-7163-ac0d-3cb2e2166715` израсходовала 2 306 557 input tokens, включая 1 970 176 cached, и 36 769 output tokens. Это примерно в 45,7 раза больше input accounting, чем весь live writer total.

Это неприемлемо для целевого быстрого процесса. Причина — generic agent повторно читал большой набор handoff/design артефактов для механической консолидации. Следующая оптимизация должна перенести такую консолидацию в deterministic compiler/helper либо ограничить агенту компактный нормализованный mapping input.

## Вывод

Structured live execution уже имеет приемлемую форму: одна read-only сессия, без команд и workspace writes. Основной оставшийся performance debt находится до live — в подготовке compiler inputs, а не в `codex exec` writer path.
