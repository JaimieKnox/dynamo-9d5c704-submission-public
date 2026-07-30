# Production defect modes (normative)

Every bundle under `/app/runs` records the ledger digests the **production** learner emitted
for that run, in `production/ledger-digest.json`. The production learner ran the same replay
the contract in `/app/docs/learner-contract.md` describes, except that exactly one entry of
the closed set below was in force for the whole of that run. No other deviation occurred, and
no run had two of them in force at once.

Each mode names one deviation and nothing else. Everything the contract states outside the
sentence describing the mode still held for that run.

## Candidate order

The modes are listed here in **candidate order**. That order is part of this document and the
reported diagnosis depends on it.

| # | mode | contract section | deviation in force |
| --- | --- | --- | --- |
| 1 | `none` | - | no deviation at all, the production ledger is the ledger the contract produces |
| 2 | `shard_local_order` | 1 | at the start of a step, the visible transitions that have not yet been admitted are admitted in ascending `actor_id` and then ascending `seq`, instead of in stream order. Which transitions are visible is unchanged |
| 3 | `watermark_last_entry` | 2 | the highest sequence number visible at a step is the `seq_watermark` of the last in force entry in the order `ingest.json` lists them, instead of the greatest `seq_watermark` among the in force entries |
| 4 | `residency_by_last_transition` | 3 | residency is decided by the admission index of the segment's **last** transition, instead of by its first |
| 5 | `truncated_bootstrap_acting_obs` | 8 | a segment whose cut kind is `truncated` bootstraps from the value of the `obs_id` the cut transition acted from, instead of from the value of its `cut_obs_id` |
| 6 | `seed_constant_one` | 5 | a segment is registered with priority `1.0`, instead of with the largest priority the ledger currently holds |
| 7 | `weight_norm_over_all_draws` | 9 | the reported weight is divided by the largest `w_raw` among **all** draws of the step, rejected draws included, instead of among that step's accepted draws only. Rejected draws still contribute nothing to the step's aggregates |

## Reading a recorded digest file

`production/ledger-digest.json` is

    {"bundle": <string>, "step_digests": [<string>, ...], "totals_digest": <string>}

`step_digests` holds one digest per learner step, in ascending step order, and `totals_digest`
is the digest of the run totals. Both are formed exactly as `/app/docs/output-schema.md`
specifies. A digest commits to a ledger and cannot be read back into one.

## What has to be reported

Two things, in the `diagnosis` object of the audit document.

`first_divergent_step` is the smallest learner step whose recorded digest in `step_digests`
differs from the digest of the step the contract produces, or `-1` when no step digest differs.
`totals_digest` takes no part in this, so a run whose production ledger differs from the
contract only in its totals has `first_divergent_step` equal to `-1`.

`defect` is the **first** mode in candidate order whose replay reproduces every entry of
`step_digests` and also reproduces `totals_digest`. A mode that reproduces every step digest
but not the totals digest is not reproducing the run and is not eligible. Because more than one
mode can leave a given run untouched, candidate order is what makes the answer single valued,
and it is the reason `none` is listed first.
