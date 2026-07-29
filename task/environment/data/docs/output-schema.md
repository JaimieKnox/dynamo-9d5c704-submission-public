# Audit document schema (normative)

One document per run bundle, written to `/app/out/<bundle>.json`, where `<bundle>` is the
bundle's directory name under `/app/runs`. UTF-8 JSON object. This schema is normative, the
example below is only an illustration of it.

## Top level

| key | type | meaning |
| --- | --- | --- |
| `bundle` | string | the `bundle` field of the bundle manifest, verbatim |
| `steps` | array | one object per learner step, in ascending step order, covering `0` to `learner_steps - 1` with no gaps |
| `totals` | object | run totals |

No other top level keys are read.

## `steps[]`

| key | type | meaning |
| --- | --- | --- |
| `step` | integer | learner step index |
| `target_epoch` | integer | the epoch in force for the step, per section 6 of the contract |
| `sampled` | array of integers | the buffer slot of the first transition of each accepted draw, in draw order, repeats included, empty when the step accepted no draw |
| `dropped_nonresident` | integer | number of rejected draws in the step |
| `mean_vtrace_target` | number | per contract section 11, rounded to 6 decimal places |
| `mean_pg_advantage` | number | per contract section 11, rounded to 6 decimal places |
| `mean_is_weight` | number | per contract section 11, rounded to 6 decimal places |
| `priority_sum_after` | number | per contract section 11, rounded to 6 decimal places |

## `totals`

All seven keys of contract section 12 are required. `transitions_enqueued`,
`segments_registered`, `segments_evicted`, `draws`, `draws_accepted` and
`unique_segments_drawn` are integers. `priority_sum_final` is a number rounded to 6 decimal
places.

## Example shape

    {
      "bundle": "s01",
      "steps": [
        {
          "step": 0,
          "target_epoch": 0,
          "sampled": [12, 41, 12],
          "dropped_nonresident": 0,
          "mean_vtrace_target": -0.104213,
          "mean_pg_advantage": 0.038117,
          "mean_is_weight": 0.918442,
          "priority_sum_after": 191.446302
        }
      ],
      "totals": {
        "transitions_enqueued": 197,
        "segments_registered": 190,
        "segments_evicted": 0,
        "draws": 72,
        "draws_accepted": 72,
        "unique_segments_drawn": 66,
        "priority_sum_final": 214.882910
      }
    }
