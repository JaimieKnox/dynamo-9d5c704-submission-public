# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. At learner step `s`, an ingest entry participates
only when the learner step has reached that entry's recorded `step` after adding `L`.
Among every participating entry, the inclusive visibility watermark is the greatest
`seq_watermark`. When no entry participates, the watermark is the empty-visibility
sentinel `-1` and nothing is admitted. File order in `ingest.json` is not a timeline.

## Ring residency and delayed registration

After the admission phase, a transition admitted at index `k` is resident exactly when

    admitted_so_far - k <= buffer_capacity

Segment residence follows that predicate for the admission index of the segment's
earliest transition. A segment becomes *complete* on the first learner step whose
admission phase has given every one of its transitions an admission index. Let `R` be
the bundle `register_delay`. The segment may enter the priority ledger only on a later
or equal step `s` satisfying `s >= complete_step + R`. Registration order among segments
that become eligible on the same step is ascending `(latest, earliest)` admission index.
The attached scoring epoch is the target epoch in force on the step of actual ledger
insert, not the step of completion when those differ.

## Scoring epoch attachment

Each segment carries the target epoch attached at ledger insert. Later accepted draws
evaluate values and current-policy log probabilities under that attached epoch. The
reported `target_epoch` field for a step uses the step formula and does not rewrite
attachments on segments that remain drawable.

## Sampler lag and step snapshots

Let `K` be `sampler_priority_lag`. When `K` is `0`, draws use the current pre-draw
priority vector. When `K` is greater than `0`, draws use the priority vector as it stood
after write-back of the previous learner step, extended with the current priorities of
any ledger rows that did not yet exist then. Importance weights always use the current
pre-draw priority vector and its mass `P`, together with registry length `N`, never the
lagged sampler vector.

Before any draw, capture `N` and the current `P` from the complete ledger, including
nonresident entries. Candidate priority rewrites become visible to later draws only after
the step's entire batch has been resolved. When one ledger position is accepted more than
once, the rewrite from the last such acceptance in draw order remains.

## Priority seeding

A newly inserted ledger row is seeded with the largest priority already present in the
ledger, counting every ledger row whether or not it is still resident. When the ledger
is empty the seed is `1.0`.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted draw
with current pre-draw priority `p`,

    w_raw = (N * (p / P)) ** (-beta)

Let `W` be the multiset of those raw weights from accepted draws only. If `W` is empty,
`mean_is_weight` is `0.0`. Otherwise divide each member by `max(W)` and average.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation uses the recorded cut observation. A full
window bootstraps from the next episode observation, and a window that would have to stop
on the episode's final transition is not a segment at all. Floating fields round to six
decimals only after reductions finish.
