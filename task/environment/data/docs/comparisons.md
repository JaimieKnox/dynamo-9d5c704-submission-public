# Replay comparisons and reductions (normative)

This appendix is the source of truth whenever replay state depends on a boundary,
ordering reduction, or normalization pool. Symbols below have the meanings assigned
by `learner-contract.md`.

## Admission and visibility

At learner step `s`, define the active ingest entries as

    A(s) = {entry | entry.step <= s}

If `A(s)` is empty, no transition is visible. Otherwise the inclusive visibility
watermark is

    max(entry.seq_watermark for entry in A(s))

The order of records in `ingest.json` does not participate in this reduction.

## Ring residency and registration

After the admission phase, a transition admitted at index `k` is resident exactly
when

    admitted_so_far - k <= buffer_capacity

A segment is resident exactly when the predicate holds for its earliest transition.
Registration occurs at the first step when all segment transitions have admission
indices. Ready segments are ordered by `(last_admission_index,
first_admission_index)`.

## Step snapshots

The target epoch is

    min(s // target_refresh_interval, n_epochs - 1)

Before drawing, take `N` from the complete registry and `P` from the sum of every
registry priority, including nonresident entries. All draws in the step use those
same values and the same pre-write-back priorities. Updates are applied only after
the entire batch has been resolved; when an entry appears repeatedly, its final
accepted update in draw order wins.

## Draw acceptance and importance weights

A sampled nonresident segment is rejected without replacement. For each accepted
draw with pre-step priority `p`, compute

    w_raw = (N * (p / P)) ** (-beta)

Let `W` be the multiset of raw weights from accepted draws only. Rejected attempts
have no raw weight in this reduction. If `W` is empty, `mean_is_weight` is `0.0`.
Otherwise:

    w_max = max(W)
    mean_is_weight = mean(w / w_max for w in W)

Accepted draws alone contribute targets, advantages, sampled slots, and priority
updates. Rejected draws alone increment `dropped_nonresident`.

## Segment and aggregate boundaries

Termination bootstraps with zero. Truncation uses the recorded cut observation.
A full window uses the next episode observation, regardless of current admission or
residency. All target and advantage values from all accepted segments participate
in their respective step means. Floating output fields are rounded to six decimal
places only after their full reductions are complete.
