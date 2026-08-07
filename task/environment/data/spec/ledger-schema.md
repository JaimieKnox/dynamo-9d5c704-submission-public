# Pulse ledger schema (normative)

One document per recording pack, written to `/app/ledgers/<pack>.json`, where `<pack>`
is the pack directory name under `/app/recordings`. UTF-8 JSON object. This schema is
normative; the example below is only an illustration of it.

## Top level

| key | type | meaning |
| --- | --- | --- |
| `recording` | string | the `bundle` field of the pack manifest, verbatim |
| `ticks` | array | one object per learner tick, in ascending order, covering `0` to `learner_steps - 1` with no gaps |
| `summary` | object | run aggregates |

No other top level keys are read.

## `ticks[]`

| key | type | meaning |
| --- | --- | --- |
| `t` | integer | learner tick index |
| `active_epoch` | integer | the epoch in force for the tick, per the pulse contract |
| `accepted_slots` | array of integers | buffer slot of the first transition of each accepted draw, in draw order, repeats included |
| `rejected_count` | integer | number of rejected draws in the tick |
| `mean_bootstrap_target` | number | per pulse contract, rounded to 6 decimal places |
| `mean_policy_advantage` | number | per pulse contract, rounded to 6 decimal places |
| `mean_importance` | number | per pulse contract, rounded to 6 decimal places |
| `priority_mass_after` | number | per pulse contract, rounded to 6 decimal places |

## `summary`

Required keys: `enqueued_transitions`, `segments_formed`, `segments_dropped`,
`draw_attempts`, `draw_accepts`, `unique_segments_used` (integers) and
`priority_mass_final` (number rounded to 6 decimal places).
