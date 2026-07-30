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
| `diagnosis` | object | what the recorded production ledger says about that run |

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

## `diagnosis`

| key | type | meaning |
| --- | --- | --- |
| `first_divergent_step` | integer | first learner step whose recorded digest differs from the contract's, or `-1` when none differs, per `/app/docs/defect-modes.md` |
| `defect` | string | the first mode in candidate order that reproduces the recorded digests, per `/app/docs/defect-modes.md`, one of the seven names that document lists |

## Ledger digests

A step's digest is taken over the eight step fields above and a run's totals digest over the
seven totals fields, both reduced to integers first so that no float is ever formatted. For a
number `x` already rounded to six decimal places as this schema requires, write

    micros(x) = int(round(x * 1000000))

The canonical string of a step is these eight fields joined by `|` with no spaces,

    <step>|<target_epoch>|<slots>|<dropped_nonresident>|<mvt>|<mpa>|<miw>|<psa>

where `<slots>` is the `sampled` slots as decimal integers joined by `,`, the empty string when
`sampled` is empty, and `<mvt>`, `<mpa>`, `<miw>` and `<psa>` are `micros` of
`mean_vtrace_target`, `mean_pg_advantage`, `mean_is_weight` and `priority_sum_after`. The
canonical string of the totals is the seven totals fields joined by `|` in the order

    <transitions_enqueued>|<segments_registered>|<segments_evicted>|<draws>|<draws_accepted>|<unique_segments_drawn>|<micros(priority_sum_final)>

A digest is the first 16 characters of the lowercase hexadecimal SHA-256 of the canonical
string encoded as UTF-8.

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
      },
      "diagnosis": {
        "first_divergent_step": -1,
        "defect": "none"
      }
    }
