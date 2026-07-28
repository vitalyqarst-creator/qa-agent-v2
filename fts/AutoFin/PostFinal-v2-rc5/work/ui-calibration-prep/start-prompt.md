# Start prompt for UI calibration session

Скопируй этот текст в новую Codex-сессию на ПК, где есть доступ к стенду.

```text
Работай как FT Test Case Agent в режиме UI calibration.

Repo/package:
fts/AutoFin/PostFinal-v2-rc5

Перед началом:
1. Проверь, что текущая ветка содержит файл:
   fts/AutoFin/PostFinal-v2-rc5/work/ui-calibration-prep/bundle-manifest.json
2. Открой и используй:
   fts/AutoFin/PostFinal-v2-rc5/AGENT-NOTES.md
   fts/AutoFin/PostFinal-v2-rc5/work/ui-calibration-prep/UI-AGENT-NOTES.md
   fts/AutoFin/PostFinal-v2-rc5/work/ui-calibration-prep/ui-calibration-index.md

Задача:
Пройти на стенде только test-cases со статусом candidate-ui-calibration из ui-calibration-index.md и зафиксировать фактическое UI-поведение.

Ограничения:
- Не запускай source analysis, writer, reviewer, bridge, benchmark или sharding.
- Не генерируй новые test-cases.
- Не меняй файлы fts/AutoFin/PostFinal-v2-rc5/test-cases/*.md напрямую.
- Не выдумывай UI-реакции, сообщения, подсветку, блокировку или save effect.
- Если стенд/данные/доступ не позволяют выполнить кейс, фиксируй blocked-ui-input.

Результаты сохраняй в:
fts/AutoFin/PostFinal-v2-rc5/work/ui-calibration-prep/results/

Для каждого TC-ID используй шаблон:
fts/AutoFin/PostFinal-v2-rc5/work/ui-calibration-prep/evidence-output-template.md

В финальном отчете укажи:
- сколько calibration-кейсов проверено;
- какие confirmed;
- какие требуют обновления тест-кейса;
- какие blocked-ui-input;
- какие evidence-файлы созданы;
- какие точные изменения нужно внести в test-cases после UI-калибровки.
```

