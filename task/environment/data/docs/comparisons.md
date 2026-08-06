# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. At learner step `s`, an ingest entry participates
only when the learner step has reached that entry's recorded `step` delayed by `L` in the
direction that postpones effectiveness (waiting past the recorded step, not advancing it).
Among every participating entry, the inclusive visibility watermark is the greatest
`seq_watermark`. When no entry participates, the watermark is the empty-visibility
sentinel `-1` and nothing is admitted. File order in `ingest.json` is not a timeline.

## Ring residency and delayed registration

A transition remains drawable until the ring has advanced one full capacity past its
admission index. The admission itself still owns its slot at the inclusive capacity
boundary; dropping it one revolution early is wrong. Segment residence applies that ring
predicate to the admission index that anchors the segment under the contract: the opening
edge of its covered span in admission order.

A segment becomes complete on the first learner step whose admission phase has given
every one of its transitions an admission index. Let `R` be the bundle `register_delay`.
The segment may enter the priority ledger only after exactly `R` full learner steps have
elapsed from that completion step, counting the completion step as step zero of the wait
(so when `R` is `0` the segment may register on the completion step itself). Among segments
that become eligible on the same step, register in ascending order of the latest admission
index, breaking ties by ascending earliest admission index. The smaller latest-admission
index registers first; descending latest-admission order is wrong.

The scoring epoch attached to a segment is the reported target epoch of the learner step
on which that segment actually enters the priority ledger under the delay rule above.
Completing the segment on an earlier step must not freeze its scoring epoch.

## Sampler lag and step snapshots

Let `K` be `sampler_priority_lag`. When `K` is `0`, draws use the current pre-draw
priority vector. When `K` is greater than `0`, draws use the priority vector as it stood
after write-back of the previous learner step, extended with the current priorities of
any ledger rows that did not yet exist then. Freezing that lag vector before write-back
is wrong. Importance weights are a correction against the ledger state captured at the draw gate:
the current pre-draw priority of the drawn row, registry length `N`, and the full-ledger
sum `P` from `learner-contract.md`. Sampler lag may change which rows are proposed, but it
does not redefine the correction distribution, and non-resident rows still contribute to `P`.

Before any draw, capture `N` and that current `P`. Candidate priority rewrites become
visible to later draws only after the step's entire batch has been resolved. Repeated
acceptances of one ledger position in a batch reduce to a single committed rewrite for
that position according to draw order.

## Priority seeding

A newly inserted ledger row is seeded with the largest priority already present in the
ledger, counting every ledger row whether or not it is still resident. When the ledger
is empty the seed is `1.0`.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted draw
with current pre-draw priority `p`,

    w_raw = (N * (p / P)) ** (-beta)

with the captured `P`. Let `W` be the multiset of those raw weights from accepted draws
only. If `W` is empty, `mean_is_weight` is `0.0`. Otherwise divide each member by
`max(W)` and average.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation bootstraps from the continuation observation
the environment recorded at the cut — distinct from the truncated transition's own
observation. A full window bootstraps from the next episode observation, and a window that
would have to stop on the episode's final transition is not a segment at all. Floating
fields round to six decimals only after reductions finish.
