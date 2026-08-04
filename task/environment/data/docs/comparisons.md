# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

Let `L` be the bundle `visibility_lag`. At learner step `s`, define the active ingest
entries as

    A(s) = {entry | s >= entry.step + L}

If `A(s)` is empty, no transition is visible. Otherwise the inclusive visibility
watermark is

    max(entry.seq_watermark for entry in A(s))

The reduction ranges over every entry of `ingest.json` that satisfies the predicate,
wherever that entry sits in the file.

## Ring residency and registration

After the admission phase, a transition admitted at index `k` is resident exactly
when

    admitted_so_far - k <= buffer_capacity

A segment is resident exactly when the predicate holds for the admission index of its
earliest transition. The admission index of its latest transition decides registration
timing and never decides residency. Registration occurs at the first step when all
segment transitions have admission indices. Ready segments are ordered by
`(last_admission_index, first_admission_index)`. A newly registered entry is seeded with
the maximum over the ledger's priorities as they stand at that insertion, or with `1.0`
when the ledger is still empty.

## Frozen scoring epoch

When a segment is registered at learner step `r`, freeze

    e_reg = min(r // target_refresh_interval, n_epochs - 1)

on that segment. Every later accepted draw of that segment evaluates values and current
policy log probabilities under epoch `e_reg`, even when the draw occurs at a later step
whose reported `target_epoch` differs. `e_reg` is written once, at registration, and
every later target refresh leaves it alone.

## Step snapshots

The reported target epoch for step `s` is

    min(s // target_refresh_interval, n_epochs - 1)

Before drawing, take `N` from the complete registry length and `P` from the sum of every
registry priority, including nonresident entries and including every entry the same step
just registered. Both come from the state that stands once this step's admission and
registration phases are finished. All draws in the step use those same values and the same
pre-write-back priorities. Updates are applied only after the entire batch has been
resolved, so a draw never sees a priority another draw of the same step wrote. Every
accepted draw of one entry within a step yields the same candidate for that entry, so the
entry ends the step holding that value.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted
draw with pre-step priority `p`, compute

    w_raw = (N * (p / P)) ** (-beta)

where `N` is the full registry length from the pre-draw snapshot, counting resident
and nonresident entries alike, and `P` is that same snapshot's priority mass. Let `W`
be the multiset of raw weights from accepted draws only. Rejected attempts have no raw
weight in this reduction. If `W` is empty, `mean_is_weight` is `0.0`. Otherwise the
correction is capped at one before averaging:

    mean_is_weight = mean(min(1.0, w) for w in W)

Accepted draws alone contribute targets, advantages, sampled slots, and priority
updates. Rejected draws alone increment `dropped_nonresident`.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation uses the recorded cut observation.
A full window uses the next episode observation, regardless of current admission or
residency. All target and advantage values from all accepted segments participate
in their respective step means. Floating output fields are rounded to six decimal
places only after their full reductions are complete.
