# Writer Runtime Workflow

1. Прочитай выбранный scope, source obligations, matrix/workflow и package notes.
2. Не расширяй scope; source ambiguity и missing input фиксируй как blocker/gap.
3. Если текущая фаза matrix — создай русскую matrix с одним `OBL-*`/`CTX-*`
   на строку, затем прогони scoped validator и передай на independent matrix review.
4. Если matrix approved — напиши canonical TC из её `SCN-*`, снова прогони
   validator и передай на independent final TC review.
5. При `changes-required` работай только с принятыми controller triage findings.
   Для каждого содержательного finding сначала возьми его `remediation_closure`
   как минимальный охват, затем по matrix найди весь ограниченный класс
   однотипных `SCN-*` (та же обязанность/правило, действие, объект и контекст).
   Исправь каждый элемент этого класса, а не только пример из finding; исключение
   допустимо лишь при source-backed различии. Перед re-review проверь все элементы
   closure напрямую, без отдельного self-check артефакта. Одна revision и один
   re-review допустимы в соответствующей фазе.
6. Обнови `workflow-state.json` только после реально завершённого transition.

Не используй старые practical profile/mode, stage handoff, self-check или
prompt artifacts как замену immutable review evidence.
