# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. An ingest entry participates at learner step
`s` only after publication lag `L` has elapsed relative to that entry's recorded
publication step. Among participating entries, the inclusive visibility watermark is
the greatest `seq_watermark`. When none participate, the watermark is the
empty-visibility sentinel `-1` and nothing is admitted. File order in `ingest.json`
is not a timeline.

## Ring residency and delayed registration

After the admission phase, a transition admitted at index `k` is resident exactly when

    admitted_so_far - k <= buffer_capacity

A segment is drawable only while the transition that completed it still owns its ring
slot under that predicate. A segment becomes *complete* on the first learner step whose
admission phase has given every one of its transitions an admission index. Let `R` be
the bundle `register_delay`. The segment may enter the priority ledger only on a later
or equal step `s` satisfying `s >= complete_step + R`. Segments that become eligible in
the same step are registered in the order their final transition was admitted, breaking
ties by the order their first transition was admitted.

## Scoring epoch attachment

When a segment becomes complete, it records the target epoch then in force. That
recorded epoch is what later accepted draws use for values and current-policy log
probabilities, even if ledger insert happens on a later learner step after
`register_delay`. The reported `target_epoch` field for a step still uses `e(s)`.

## Sampler lag and step snapshots

Let `K` be `sampler_priority_lag`. When `K` is `0`, draws use the current pre-draw
priority vector. When `K` is greater than `0`, draws use the priority vector as it
stood after write-back of the previous learner step. If that lagged vector is shorter
than the current ledger, extend it in ledger order by adopting, for each newly known
trailing row, that row's current pre-draw priority.

Before any draw, capture importance-weight length and mass from the ledger rows that
are currently resident under the residency rule above. Candidate priority rewrites
produced during the draw phase become part of the ledger only after every draw of the
step has been resolved. When one ledger position is accepted more than once, the
rewrite from the last such acceptance in draw order remains.

## Priority seeding

A newly inserted ledger row is seeded with the largest priority already present in the
ledger, counting every ledger row whether or not it is still resident. When the ledger
is empty the seed is `1.0`.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted draw
with current pre-draw priority `p`,

    w_raw = (N * (p / P)) ** (-beta)

where `N` and `P` are the resident-only captures from the start of the draw phase. Let
`W` be the multiset of those raw weights from accepted draws only. If `W` is empty,
`mean_is_weight` is `0.0`. Otherwise divide each member by `max(W)` and average.

## Segment and aggregate boundaries

Termination bootstraps with zero. A truncated segment bootstraps from the observation
the environment recorded at the truncation cut. A full window bootstraps from the next
episode observation, and a window that would have to stop on the episode's final
transition is not a segment at all. Floating fields round to six decimals only after
reductions finish.
