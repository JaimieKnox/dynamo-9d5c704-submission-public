# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

An ingest entry becomes eligible to contribute only after the learner has waited the
bundle's configured publication lag past that entry's recorded step. Among every entry
eligible at the current learner step, the inclusive visibility watermark is the greatest
`seq_watermark`. When no entry is eligible, the watermark is the empty-visibility
sentinel `-1` and nothing is admitted. File order in `ingest.json` is not a timeline.

## Ring residency and delayed registration

After the admission phase, a transition admitted at index `k` is resident exactly when

    admitted_so_far - k <= buffer_capacity

Segment residence follows that predicate for the admission index of the transition that
first entered the buffer for the segment. A segment becomes *complete* on the first
learner step whose admission phase has given every one of its transitions an admission
index. Let `R` be the bundle `register_delay`. The segment may enter the priority ledger
only on a later or equal step `s` satisfying `s >= complete_step + R`. Segments that
become eligible on the same step are registered in the order their final transition was
admitted, breaking ties by the order their first transition was admitted. The scoring
epoch stored on the ledger entry is `e(s)` for the insert step.

## Scoring epoch attachment

Each ledger entry stores a scoring epoch at insert. Accepted draws evaluate values and
current-policy log probabilities under the epoch stored on that entry. The reported
`target_epoch` field for a step uses `e(s)` and does not rewrite stored epochs on
drawable entries.

## Sampler lag and step snapshots

Let `K` be `sampler_priority_lag`. When `K` is `0`, draws use the current pre-draw
priority vector. When `K` is greater than `0`, draws use the priority vector as it stood
after write-back of the previous learner step. If that lagged vector is shorter than the
current ledger, extend it in ledger order by adopting, for each newly present trailing
row, the priority that row holds in the current pre-draw vector.

Before any draw, capture `N` as the number of registered ledger rows and `P` as the sum
of current pre-draw priorities over those same rows, including rows that are no longer
resident. Importance weights for accepted draws use those captured values. Candidate
priority rewrites are committed after the step's entire batch has been resolved. When one
ledger position is accepted more than once, the rewrite from the last such acceptance in
draw order remains.

## Priority seeding

A newly inserted ledger row is seeded with the largest priority already present in the
ledger, counting every ledger row whether or not it is still resident. When the ledger
is empty the seed is `1.0`.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted draw
with current pre-draw priority `p`,

    w_raw = (N * (p / P)) ** (-beta)

with the captured `N` and `P` from before the batch. Let `W` be the multiset of those raw
weights from accepted draws only. If `W` is empty, `mean_is_weight` is `0.0`. Otherwise
divide each member by `max(W)` and average.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation bootstraps from the observation the
environment recorded at the cut. A full window bootstraps from the next episode
observation, and a window that would have to stop on the episode's final transition is
not a segment at all. Floating fields round to six decimals only after reductions finish.
