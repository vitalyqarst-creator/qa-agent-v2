# Search Clear Context V4 Performance Analysis

## Сравнение

| metric | V2 | V3 | V4 | вывод |
| --- | ---: | ---: | ---: | --- |
| terminal result | changes-required | writer blocked | accepted | V4 впервые достиг semantic acceptance |
| total duration | `71.985 s` | `13.453 s` | `66.562 s` | V4 на `5.423 s` (`7.5%`) быстрее V2 |
| writer duration | `34.610 s` | `13.453 s` blocked | `35.078 s` | Почти без изменений |
| reviewer duration | `37.375 s` | not started | `31.484 s` | V4 reviewer на `5.891 s` быстрее V2 |
| total tokens | `42,721` | `20,160` incomplete | `43,535` | V4 на `814` (`1.9%`) дороже V2 |
| uncached input tokens | `40,142` | `20,026` incomplete | `41,458` | Рост `3.3%`; токеновая оптимизация не доказана |
| uncached tokens / OBL | `10,035.5` | n/a | `10,364.5` | Фиксированный overhead остаётся высоким |
| fresh sessions | 2 distinct | writer only | 2 distinct | V4 доказал isolation |
| commands / file changes by stages | `0 / 0` | `0 / 0` | `0 / 0` | Compact read-only boundary сохранился |

## V4 Context

- Primary writer+reviewer context: `58,339` bytes.
- Prompt bytes: `50,917`; instruction bytes: `7,422`.
- Writer: `21,533` tokens; reviewer: `22,002` tokens.
- Four test cases, four testable obligations, one validator invocation from budget `5`.
- Both prompts carried exact V4 version/id/digest identity.

## Вывод

V4 доказал корректность и скорость process path: за `66.6 s` получены draft и accepted reviewer verdict в двух отдельных сессиях. Но токеновая цель не достигнута: стоимость на obligation не снизилась.

Ещё один запуск того же малого scope даст мало новой информации. Следующий benchmark должен взять medium scope на `8–12` TC / `12–25` obligations и проверить, снижается ли стоимость на obligation за счёт амортизации fixed context.
