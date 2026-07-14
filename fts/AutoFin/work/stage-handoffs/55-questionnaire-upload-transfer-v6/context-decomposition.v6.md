# Context Decomposition V6

## Итог

V5 prompt разложен по фактическим секциям. Единственное доказанное нерелевантное содержимое — полный package-note раздел DaData в обеих независимых сессиях. Source-backed obligations, oracles, fixtures, writer draft и role profiles не сокращаются.

## Exact Prompt Bytes

| role | V5 prompt | irrelevant DaData block | projected prompt after guarded projection |
| --- | ---: | ---: | ---: |
| writer | 43947 | 5331 | 38682 |
| reviewer | 55660 | 5331 | 50395 |

- net exact prompt bytes removed: `10530`.
- guard: DaData section remains intact when selected evidence outside the note references DaData.
- V5 uncached input tokens: `53028`; backend bootstrap/system tokens не имеют section attribution, поэтому их нельзя честно приписать repo prompt sections.

## Writer Sections

{
  "outer_contract": 1048,
  "metadata_profile_rule_card": 6787,
  "source_evidence": 23533,
  "obligation_transport": 1532,
  "draft_seed_and_final_contract": 11047
}

## Reviewer Sections

{
  "outer_contract": 633,
  "metadata_profile_rule_card": 4419,
  "shared_source_evidence": 6511,
  "semantic_obligation_projection": 12457,
  "gate_and_calibration_summaries": 2355,
  "immutable_draft": 28560,
  "final_contract": 725
}

## Не сокращать

- semantic obligation projection и exact observable oracle;
- portable fixture contracts;
- immutable draft для независимого reviewer;
- runtime profile каждой отдельной exec session.
