# Performance Analysis: V1-V3

## Summary

V3 is the first cycle in this series that completes both writer and reviewer. Its higher total cost is caused by actually running the missing reviewer stage, not by a regression in writer cost.

| cycle | completed stages | duration | total tokens | result |
| --- | ---: | ---: | ---: | --- |
| V1 | 1 | 233 375 ms | 50 517 | writer blocked by the former gate defect |
| V2 | 1 | 220 125 ms | 49 768 | writer draft-ready; reviewer never started because old prompt exceeded context |
| V3 | 2 | 380 312 ms | 105 983 | writer draft-ready; reviewer changes-required |

## V3 stage attribution

| role | duration | input | output | total |
| --- | ---: | ---: | ---: | ---: |
| writer | 229 718 ms | 37 859 | 12 487 | 50 346 |
| reviewer | 150 594 ms | 47 651 | 7 986 | 55 637 |

- Writer V3 vs V2: +578 total tokens (+1.2%) and +9 593 ms (+4.4%); effectively stable for the same 47-case scope.
- Reviewer adds 55 637 tokens and 150 594 ms, but replaces the previous transport blocker with a real semantic decision.
- Uncached input per obligation for the full two-stage V3 cycle: 1 315.54 tokens.
- Both stages executed zero shell commands and changed zero workspace files; all runtime artifacts were runner-owned.

## Interpretation

The immediate bottleneck is now quality of prepared execution detail, not reviewer transport. Token reduction alone would not make the unsigned draft acceptable. The next optimization must prevent known non-executable intents before paying for another live reviewer.
