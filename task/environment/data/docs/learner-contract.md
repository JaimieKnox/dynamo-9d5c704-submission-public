# Learner replay contract (normative)

This document fixes every rule that decides an audit document. It applies to every bundle
under `/app/runs`. Where an inequality appears it is the exact comparison the contract uses.

## 1. Global admission order

Every shard line of the bundle belongs to one single stream of transitions. The `seq` field
is a transition's position in that stream and is unique across the bundle. The shard files
are only per actor views of that one stream, so shard file order carries no meaning. The
learner admitted transitions in stream order and in no other order.

## 2. Visibility

The ingest log is an unordered history of cumulative publication facts. An entry becomes
effective only after its recorded `step` plus the bundle `visibility_lag` have both been
reached. Its watermark is inclusive. Replay combines every fact effective for the current
step. JSON position is not chronology. The empty-visibility sentinel and the watermark
reduction are specified in `comparisons.md`.

## 3. Buffer admission and residency

At the start of every learner step, in stream order, every visible transition that has not
yet been admitted is admitted. The `k`-th transition ever admitted, counting from `0`,
receives admission index `k` and occupies slot `k mod buffer_capacity`. Admission overwrites
whatever occupied that slot before, and nothing else ever clears or moves a slot.

A segment is **resident**, meaning still drawable, only while all transitions it spans
survive in the ring. Residency is settled after the step's admission phase and reused for
the whole draw phase. The index that controls this test and its inclusive capacity boundary
are defined in `comparisons.md`.

## 4. Segments

A segment is identified by an episode and a start offset `t0` inside it. Its length is
determined by scanning forward from `t0` within the episode, ordering the episode's
transitions by `t`, and stopping at the first of these conditions:

- the transition has `terminated` true, giving cut kind `terminated`
- the transition has `truncated` true, giving cut kind `truncated`
- the scan has covered `n_step` transitions, giving cut kind `window`

Cut kind is drawn from exactly that closed set of three values. The segment covers the
transitions from `t0` up to and including the stopping transition. A `window` segment whose
stopping transition is the last transition of its episode is never formed and never
registered. Segment transitions are always the episode's own transitions at those offsets.

## 5. Registration

A segment becomes complete at the first learner step by whose admission phase every one of
its transitions has been admitted. It becomes registrable only after the bundle
`register_delay` additional learner steps have elapsed from that completion step, as
detailed in `comparisons.md`. All segments that become registrable in the same step are
registered in ascending order of the admission index of their last transition, breaking
ties by ascending admission index of their first transition.

The learner's priority ledger is append only. A registered segment keeps its ledger
position for the rest of the run and is never removed, even after its transitions leave the
buffer. Ledger positions are assigned in registration order starting at `0`.

A segment is seeded with the largest priority the ledger currently holds. Every ledger entry
counts toward that maximum, whether or not it is still resident. When the ledger is empty,
the seed is `1.0`. A segment registered earlier in the same step is eligible to supply that
maximum.

Registration for a step is complete before that step draws, so a segment registered in a step
can be drawn in that same step. The scoring epoch attached to the segment is the epoch in
force on the insert step.

## 6. Target epoch

The target epoch reported for learner step `s` is

    e(s) = min(s // target_refresh_interval, n_epochs - 1)

using integer floor division, where `n_epochs` is the number of epoch files the bundle
ships. The reported `target_epoch` field always uses `e(s)`. Scoring an accepted draw uses
the attached registration epoch of the drawn segment.

## 7. Sampling

Let `N` be the number of registered segments. Let `P` be the sum of the current pre-draw
priorities of all `N` ledger entries, resident or not. Draws are taken from the sampler
priority vector defined by `sampler_priority_lag` in `comparisons.md`. When that vector's
mass is not greater than `0.0`, or when `N` is `0`, or when current `P` is not greater than
`0.0`, the step makes no draws. Otherwise the step makes exactly `batch_size` draws using
the sampler in `/app/docs/sampler.md` on the sampler priority vector.

Each draw is resolved in draw order against residency under the current ring. Rejected
draws are counted, are not replaced, contribute nothing to aggregates, and leave priorities
untouched. Accepted draws may repeat an entry. Importance weights use the captured current
pre-draw priorities and current `P` from before any draw of the step, not the lagged sampler
vector and not priorities rewritten earlier in the same batch.

## 8. Per segment quantities

For an accepted draw, evaluate values and current-policy log probabilities under the
segment's attached registration epoch. Clip the importance ratio of each transition with the
bundle's `rho_bar` and `c_bar` as the two separate clip bounds. Choose the bootstrap from
the cut kind alone:

- `terminated`: there is no continuation to value
- `truncated`: bootstrap from the observation the environment recorded at the cut
- `window`: bootstrap from the observation of the next transition in that episode, whether
  or not that transition is currently admitted or resident

Value targets and policy-gradient advantages are exactly the truncated importance-weighted
returns produced by `/app/rlaudit/vtrace.py` for that segment's rewards, values, bootstrap,
clipped ratios and the bundle's `gamma`. Do not re-derive a different recursion.

## 9. Importance sampling weight

The step reports a normalized importance weight for its useful samples. Apply the formula
and pool definition in `comparisons.md`. Rejected draws do not enter the normalization pool.

## 10. Priority write back

Accepted draws produce candidate ledger rewrites of

    (mean of the absolute values of its advantages + priority_eps) ** alpha

using the bundle's `alpha` and `priority_eps`. Rejected draws do not produce candidates.
The pre-draw snapshot, the invisibility of in-batch rewrites to later draws, and
repeated-entry commit ordering follow `comparisons.md`. After write-back, the resulting
priority vector becomes the lagged sampler vector for the next step when
`sampler_priority_lag` is greater than `0`.

## 11. Per step aggregates

After write back, the step reports:

- `target_epoch`: `e(s)`
- `sampled`: the buffer slot of the first transition of each accepted draw, in draw order
- `dropped_nonresident`: the number of rejected draws
- `mean_vtrace_target`: the mean of every value target produced by accepted draws, or `0.0`
- `mean_pg_advantage`: the mean of every advantage produced by accepted draws, or `0.0`
- `mean_is_weight`: the weight of section 9
- `priority_sum_after`: the sum of every ledger priority after write back

The four floating aggregates are rounded to six decimal places.

## 12. Totals

At the end of the run the document reports:

- `transitions_enqueued`: how many transitions were admitted
- `segments_registered`: how many segments entered the ledger
- `segments_evicted`: how many ledger entries are not resident after the final step
- `draws`: how many draws were attempted across the run
- `draws_accepted`: how many of those were accepted
- `unique_segments_drawn`: how many distinct ledger positions were accepted at least once
- `priority_sum_final`: the sum of every ledger priority after the final step, rounded to six
  decimal places
