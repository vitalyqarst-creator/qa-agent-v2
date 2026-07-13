# V8 Terminal Stop Gate

## Статус

`STOP — V8 terminal changes-required`

## Запрещено

- retry/resume writer или reviewer V8;
- второй dispatcher V8;
- SDK fallback или ручное исправление reviewer result;
- считать `TC-ACPD-011` дефектным по ложной projection;
- создавать production shadow или изменять FT-first baseline.

## Разрешённый successor

Только новый immutable H46/V9 после:

1. canonical parsing/structured transport для `DICT-* active_values`;
2. regression на точную compiler-produced форму `Мужчина`; `Женщина`;
3. gate, запрещающего punctuation-only/empty projected values;
4. hash-bound reviewer-only rebind с повтором всех deterministic gates либо явного доказательства, что такой route безопасно невозможен;
5. нового checkpoint/push и отдельной live authorization.

V8 draft может использоваться только как unsigned hash-bound recovery input, не как requirements evidence и не как sign-off.
