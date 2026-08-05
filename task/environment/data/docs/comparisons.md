# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. At learner step `s`, an ingest entry participates
only when `s` has reached the entry's recorded `step` after adding `L`. Among every
participating entry, the inclusive visibility watermark is the greatest `seq_watermark`.
When no entry participates, the watermark is the empty-visibility sentinel `-1` and
nothing is admitted. File order in `ingest.json` is not a timeline.

## Ring residency and delayed registration

After the admission phase, a transition admitted at index `k` is resident exactly when

    admitted_so_far - k <= buffer_capacity

Segment residence follows that predicate for the admission index of the segment's
first-admitted transition. A segment becomes *complete* on the first learner step whose
admission phase has given every one of its transitions an admission index. Let `R` be
the bundle `register_delay`. The segment may enter the priority ledger only on a later
or equal step `s` satisfying `s >= complete_step + R`. Registration order among segments
that become eligible on the same step is ascending by the admission index of the
segment's last-admitted transition, then by the admission index of its first-admitted
transition. The scoring epoch attached at registration is `e(s)` for the insert step.

## Scoring epoch attachment

Each registered segment carries a scoring epoch fixed at ledger insert. Accepted draws
evaluate values and current-policy log probabilities under that carried epoch. The
reported `target_epoch` field for a step uses `e(s)` and does not rewrite carried epochs
on drawable segments.

## Sampler lag and step snapshots

Let `K` be `sampler_priority_lag`. When `K` is `0`, draws use the current pre-draw
priority vector. When `K` is greater than `0`, draws use the priority vector as it stood
after write-back of the previous learner step. If that lagged vector is shorter than the
current ledger, extend it in ledger order by the current pre-draw priorities of the
missing trailing rows.

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

Termination bootstraps with zero. Truncation uses the recorded cut observation. A full
window bootstraps from the next episode observation, and a window that would have to stop
on the episode's final transition is not a segment at all. Floating fields round to six
decimals only after reductions finish.
