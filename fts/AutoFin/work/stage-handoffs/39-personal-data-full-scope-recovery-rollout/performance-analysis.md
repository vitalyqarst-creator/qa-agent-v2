# V2 Performance Analysis

## Writer Comparison

| metric | V1 blocked writer | V2 recovery writer | delta |
| --- | ---: | ---: | ---: |
| duration | 233.375 s | 220.125 s | -13.250 s (-5.7%) |
| input tokens | 37 859 | 37 862 | +3 |
| output tokens | 12 658 | 11 906 | -752 (-5.9%) |
| total tokens | 50 517 | 49 768 | -749 (-1.5%) |
| commands / file changes | 0 / 0 | 0 / 0 | unchanged |
| deterministic writer gates | structure blocked | all pass | improved |

V2 produces 47 cases at 582.49 uncached input tokens per obligation.

## Input Preparation

This iteration did not launch the generic compiler-input preparation agent. Existing verified inputs were compiled deterministically in about 1.5 seconds. Therefore the previously observed 2.306M input-token preparation cost was completely avoided for recovery.

## Reviewer

No reviewer session ran, so no reviewer token/duration metrics exist. Post-fix context replay is 117 439 / 131 072 bytes but is not a live performance result.

## Conclusion

Direct reuse of verified compiler inputs is already the correct fast recovery path. A broader deterministic input-builder replacement remains deferred until a complete writer/reviewer cycle is accepted.
