# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. At learner step `s`, an ingest entry participates
only when the learner step has reached that entry's recorded `step` after adding `L`.
Among every participating entry, the inclusive visibility watermark is the greatest
`seq_watermark`. When no entry participates, nothing is visible. File order in
`ingest.json` is not a timeline.

## Ring residency and registration

After the admission phase, a transition admitted at index `k` is resident exactly when

    admitted_so_far - k <= buffer_capacity

Segment residence follows that predicate for the admission index of the segment's
earliest transition. Registration timing follows the admission index of the segment's
latest transition. Ready segments register in ascending `(latest, earliest)` admission
index order.

## Scoring epoch attachment

Each segment carries the target epoch that was in force at the learner step when the
segment entered the priority ledger. Later accepted draws of that segment evaluate values
and current-policy log probabilities under that attached epoch. The ledger field
`target_epoch` for a step still reports the epoch formula for that step index and is not
a license to retarget attached scoring epochs on segments that remain drawable.

## Step snapshots

Before any draw of a step, capture registry length `N` and priority mass `P` from the
complete ledger, including nonresident entries. Every draw of the step, and every raw
importance weight of the step, must be computed from that captured snapshot and from the
pre-draw priority vector. Candidate priority rewrites produced by accepted draws become
visible to later draws only after the step's entire batch has been resolved. When one
ledger position is accepted more than once in the batch, the rewrite from the last such
acceptance in draw order is the one that remains.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted draw with
pre-draw priority `p`,

    w_raw = (N * (p / P)) ** (-beta)

with the snapshot `N` and `P` from above. Let `W` be the multiset of those raw weights from
accepted draws only. If `W` is empty, `mean_is_weight` is `0.0`. Otherwise divide each
member by `max(W)` and average. Rejected draws increment `dropped_nonresident` only.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation uses the recorded cut observation. A full
window bootstraps from the next episode observation, and a window that would have to stop
on the episode's final transition is not a segment at all. All target and advantage values
from all accepted segments participate in their step means. Floating fields round to six
decimals only after reductions finish.
