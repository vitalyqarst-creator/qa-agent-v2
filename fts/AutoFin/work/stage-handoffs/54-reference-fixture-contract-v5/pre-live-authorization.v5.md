# Pre-Live Authorization V5

## Основание

- User instruction: `Продолжай`.
- Offline checkpoint: `25ba4a45cb0edfb7cf6574fbd9bbd182d02b16b1`.
- Local и `origin/audit/application-card-personal-data-iteration` SHA подтверждены как совпадающие до создания этого артефакта.
- Protocol: `benchmark-protocol.v5.md`.

## Immutable binding

| artifact | identity |
| --- | --- |
| stage package SHA-256 | `3217d9b90906250c817fd467c61c7af5c003f4452d08cc55b19903cf9f33a30e` |
| package digest | `83ee169e8e5d338f8dfd9cd977d8c3bf2443538b553a47b7365d40d083fe51ab` |
| input fingerprint | `7c59d70707bc2156c5adc93e8391bff3a55dc4e1e360a82db515149b54913cb3` |
| atomic obligations SHA-256 | `8695ec41e98f02da98e1cb5e6390a534a3d5e5b9abdc07bcc3cf153fd4ffb0e3` |
| dispatcher config SHA-256 | `4bb7736d12cbf8df2cad6ba97916becdc088fdc2db800b24b27b80e49b24ec5e` |

## Invocation budget

Ровно один dispatcher invocation для V5 cycle. После terminal result budget становится 0 независимо от результата.

Повтор, resume, rebind, repair, sharding, SDK fallback, ручная правка draft и promotion запрещены. Duration или token result публикуется как observation и не разрешает retry.

## Production boundary

Protected hashes: visual assessment `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`; personal data `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`; section 4.2 `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`. Promotion target должен оставаться отсутствующим.
