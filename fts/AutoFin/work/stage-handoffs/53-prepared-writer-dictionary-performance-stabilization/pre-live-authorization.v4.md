# Pre-Live Authorization V4

## Основание

- User instruction: `Выполняй предложенный тобой план`.
- Offline checkpoint: `c9dcbebe5ddba6215deb55324dfe9b31201022d5`.
- Local and `origin/audit/application-card-personal-data-iteration` SHA были подтверждены как совпадающие до создания этого артефакта.
- Протокол: `benchmark-protocol.v4.md`.

## Неизменяемые привязки

| run | stage package SHA-256 | package digest | input fingerprint | dispatcher config SHA-256 |
| --- | --- | --- | --- | --- |
| `r1` | `2ccfe07793af816cb2269372cb4594b884038cf87f6a8ccf3bc4f5fefb7c09ab` | `0ef00ba00344229211375efcd280e7c3d2940e68e4f2af248d106c8181cb64ae` | `3bb4ae09be3b241aa119e15b3a62d5d8ecf36d556d579cd14f16e7568aff9871` | `e39c755e666f7c719f69b82b6723aaedd921e31d38e11461cc1f65a30f453142` |
| `r2` | `d6bf1bb17b042335991acbc71c5770736dd9668f72b8603098717f040ae923bb` | `1bb41cc63071aa2fa59ba5b9d24b520670310b064052656103c99567097ce95e` | `3166ea14fab09e0d1c77b7539c1505341c3bff8affc205ff61712aebb3921d29` | `b370210c1c02ebc444dd3ad79303c3e5b9d5231fc7cbbffdd8395855cb2bccc8` |
| `r3` | `9b6d231e68fa0412eb4f9881f5aeb470173f33d9d9fe6a2430ade89c416b19d8` | `62e44ec2d22aae3a958f3b05e4ddf45ac9d538a9440a30692596566f851ab596` | `b181ba24a67620534dc2c28b3522536db9ea840fc2bdf6a5d856c61d57fb4ce0` | `018eee45c71b81eb1a1c439474dfff73a69f660c4cc48350b041c5d309585aa8` |

Общий SHA-256 atomic obligations: `6fd49ada148da93d1ad059988b898eeeca70a00ddf16a7eb0b18748c2eb7bd0f`.

## Invocation budgets

| run | initial budget | условие расходования | budget после terminal result |
| --- | ---: | --- | ---: |
| `r1` | 1 | разрешён сразу после push этого authorization checkpoint | 0 |
| `r2` | 1 | только если r1 прошёл все quality и production-boundary gates | 0 |
| `r3` | 1 | только если r2 прошёл все quality и production-boundary gates | 0 |

Повтор, resume, rebind, repair, sharding, SDK fallback и promotion запрещены. Превышение duration target при сохранённом качестве не является quality failure и не останавливает последовательность: для честного median нужны три измерения.
