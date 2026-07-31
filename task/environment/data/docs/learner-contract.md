# Learner replay contract (normative)

This document fixes every rule that decides an audit document. It applies to every bundle
under `/app/runs`. Where an inequality appears it is the exact comparison the contract uses.

## 1. Global admission orde

Every shard line of the bundle belongs to one single stream of transitions. The `seq` field
is a transition's position in that stream and is unique across the bundle. The shard files
are only per actor views of that one stream, so shard file order carries no meaning. The
learner admitted transitions in stream order and in no other order.

## 2. Visibility

The ingest log records when recorded material became visible to the learner. Each entry
states that from its `step` onward the learner could see every transition up to and including
its `seq_watermark`. An entry recorded at a step is already in force at that step. Visibility
is cumulative and only ever grows as the run proceeds. When more than one entry is in force,
the learner sees as far as the furthest watermark any of them grants. Entries are not
required to be sorted and more than one entry may share a step. Before any entry is in force
the learner sees nothing at all.

## 3. Buffer admission and residency

At the start of every learner step, in stream order, every visible transition that has not
yet been admitted is admitted. The `k`-th transition ever admitted, counting from `0`,
receives admission index `k` and occupies slot `k mod buffer_capacity`. Admission overwrites
whatever occupied that slot before, and nothing else ever clears or moves a slot.

A segment is **resident**, meaning still drawable, only while the buffer still holds every
transition the segment covers. A transition admitted at index `k` remains in the buffer
exactly while `admitted_so_far - k <= buffer_capacity`, where `admitted_so_far` is the number
of transitions admitted by the end of the step's admission phase. Because the ring
overwrites oldest first, a segment is resident exactly while its earliest admitted transition
still occupies its slot. Whether that holds is settled once per learner step, after that
step's admission phase, and the same answer is used for the whole of that step. Admission
for a step is complete before that step decides residency, and residency is settled before
that step draws. Admission for a step is complete before
that step decides residency, and residency is settled before that step draws.

## 4. Segments

A segment is identified by an episode and a start offset `t0` inside it. Its length is
determined by scanning forward from `t0` within the episode, ordering the episode's
transitions by `t`, and stopping at the first of these conditions:

- the transition has `terminated` true, giving cut kind `terminated`
- the transition has `truncated` true, giving cut kind `truncated`
- the scan has covered `n_step` transitions, giving cut kind `window`

Cut kind is drawn from exactly that closed set of three values. The segment covers the
transitions from `t0` up to and including the stopping transition. A `window` segment whose
stopping transition is the last transition of its episode is never formed and neve
registered. Segment transitions are always the episode's own transitions at those offsets.

## 5. Registration

A segment becomes registrable at the first learner step by whose admission phase every one
of its transitions has been admitted. All segments that become registrable in the same step
are registered in ascending order of the admission index of their last transition, breaking
ties by ascending admission index of their first transition.

The learner's priority ledger is append only. A registered segment keeps its ledge
position for the rest of the run and is never removed, even after its transitions leave the
buffer. Ledger positions are assigned in registration order starting at `0`.

A segment is seeded with the largest priority the ledger currently holds. Every ledger entry
counts toward that maximum, whether or not it is still resident. When the ledger is empty, the seed is `1.0`. A segment
registered earlier in the same step is eligible to supply that maximum.

Registration for a step is complete before that step draws, so a segment registered in a step
can be drawn in that same step.

## 6. Target epoch

The target epoch in force for learner step `s` is

    e(s) = min(s // target_refresh_interval, n_epochs - 1)

using integer floor division, where `n_epochs` is the number of epoch files the bundle
ships. Every value and every current policy log probability used at step `s` is evaluated
under the epoch `e(s)` snapshot.

## 7. Sampling

Let `N` be the number of registered segments and `P` the sum of the priorities of all `N`
ledger entries, resident or not. When `N` is `0` or `P` is not greater than `0.0`, the step
makes no draws. Otherwise the step makes exactly `batch_size` draws using the sampler in
`/app/docs/sampler.md`.

Each draw is resolved in draw order. A draw landing on a ledger entry whose segment is not
resident at this step is rejected. Rejected draws are counted, are not replaced by anothe
draw, contribute nothing to the step's aggregates, and leave that entry's priority
untouched. A draw landing on a resident entry is accepted. The same entry may be drawn more
than once in one step, and every accepted draw counts separately.

## 8. Per segment quantities

For an accepted draw on a segment of length `L`, with transitions indexed `k` from `0` to
`L - 1` in episode order, under the epoch `e(s)` snapshot:

    v[k]     = value of the transition's own observation
    ratio[k] = exp(current policy log probability of the recorded action - behavior_logp)
    rho[k]   = min(rho_bar, ratio[k])
    c[k]     = min(c_bar, ratio[k])

The bootstrap value `v[L]` depends only on the cut kind:

- `terminated`: the episode ended in the environment, so there is no continuation to value
- `truncated`: the episode was cut by a time limit while it was still live, so the bootstrap
  is the value of the observation the environment recorded at the cut
- `window`: the segment ended part way through a live episode, so the bootstrap is the value
  of the observation of the next transition in that episode, whether or not that transition
  is currently admitted or resident

Value targets and advantages are

    target[L]   = v[L]
    delta[k]    = rho[k] * (reward[k] + gamma * v[k+1] - v[k])
    target[k]   = v[k] + delta[k] + gamma * c[k] * (target[k+1] - v[k+1])
    advantage[k] = rho[k] * (reward[k] + gamma * target[k+1] - v[k])

computed from `k = L - 1` down to `k = 0`.

## 9. Importance sampling weight

For an accepted draw whose ledger priority before the step's write back is `p`, with `N` and
`P` as in section 7 and with the bundle's `beta`,

    w_raw = (N * (p / P)) ** (-beta)

The reported weight for a step is the mean of `w_raw / w_max` over that step's accepted
draws, where `w_max` is the largest raw weight among the draws that step accepted. When the
step accepted no draw the reported weight is `0.0`. Rejected draws contribute nothing.

## 10. Priority write back

After every draw of a step has been resolved, each accepted draw's ledger entry is rewritten
to

    (mean of the absolute values of its advantages + priority_eps) ** alpha

using the bundle's `alpha` and `priority_eps`. When the same entry is accepted more than once
in one step, the last rewrite of that step wins. Rejected draws leave their entry untouched.
Write backs from one step are not visible to that same step's draws.

## 11. Per step aggregates

After write back, the step reports:

- `target_epoch`: `e(s)`
- `sampled`: the buffer slot of the first transition of each accepted draw, in draw orde
- `dropped_nonresident`: the number of rejected draws
- `mean_vtrace_target`: the mean of every `target[k]` produced by accepted draws, or `0.0`
- `mean_pg_advantage`: the mean of every `advantage[k]` produced by accepted draws, or `0.0`
- `mean_is_weight`: the weight of section 9
- `priority_sum_after`: the sum of every ledger priority after write back

The four floating aggregates are rounded to six decimal places.

## 12. Totals

At the end of the run the document reports:

- `transitions_enqueued`: how many transitions were admitted
- `segments_registered`: how many segments entered the ledge
- `segments_evicted`: how many ledger entries are not resident after the final step
- `draws`: how many draws were attempted across the run
- `draws_accepted`: how many of those were accepted
- `unique_segments_drawn`: how many distinct ledger positions were accepted at least once
- `priority_sum_final`: the sum of every ledger priority after the final step, rounded to six
  decimal places
