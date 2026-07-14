# Prompt: V5 reference fixture canary follow-up

Продолжи только после terminal V5 result.

1. Прочитай `workflow-state.yaml`, V5 live result, performance observation и terminal gate.
2. Не повторяй canary и не исправляй benchmark draft вручную.
3. Если V5 принят, сравни V3/V4/V5 качество, latency и token cost и предложи следующий узкий bottleneck на основе измерений.
4. Если V5 заблокирован, изолируй первый deterministic/reviewer failure и подготовь offline-only remediation.
5. Не меняй FT-first baseline и не выполняй promotion без отдельной задачи пользователя.
