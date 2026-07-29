# Learner replay contract (normative)

This document fixes every rule that decides an audit document. It applies to every bundle
under `/app/runs`, whether or not that bundle ships an `expected.json`. Where an inequality
appears it is the exact comparison the contract uses.

## 1. Global admission order

The bundle's transitions form one sequence, all shard lines from all shard files ordered by
ascending `seq`. Shard file order carries no meaning. This single ascending sequence is the
only order in which transitions may enter the buffer.

## 2. Visibility watermark

For learner step `s`, the watermark is

    W(s) = max({a.seq_watermark for a in admissions if a.step <= s} union {0})

The comparison is `a.step <= s`, so an admission recorded at step `s` is already visible at
step `s`. When no admission satisfies `a.step <= s` the watermark is `0`. A transition is
visible at step `s` when `seq <= W(s)`.

## 3. Buffer admission

At the start of every learner step, in ascending `seq` order, every visible transition that
has not yet been admitted is admitted. The `k`-th transition ever admitted, counting from
`0`, receives admission index `k` and occupies slot `k mod buffer_capacity`. Admission
overwrites whatever occupied that slot before.

Let `n` be the number of transitions admitted so far, measured after the admission phase of
the current step. A transition admitted at index `i` is **resident** when

    n - i <= buffer_capacity

A segment is resident exactly when its first transition is resident, that being the one of
its transitions with the lowest admission index. Residency is evaluated once per learner
step, after that step's admission phase, and the same value is used for the whole step.

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

A segment becomes registrable at the first learner step by whose admission phase every one
of its transitions has been admitted. All segments that become registrable in the same step
are registered in ascending order of the admission index of their last transition, breaking
ties by ascending admission index of their first transition.

The learner's priority ledger is append only. A registered segment keeps its ledger
position for the rest of the run and is never removed, even after its transitions leave the
buffer. Ledger positions are assigned in registration order starting at `0`.

A segment is seeded with the largest priority currently held by a **resident** registered
segment, using the residency of the current step. When no registered segment is resident,
the seed is `1.0`. A segment registered earlier in the same step is eligible to supply that
maximum.

## 6. Target epoch

The target epoch in force for learner step `s` is

    e(s) = min(s // target_refresh_interval, n_epochs - 1)

using integer floor division, where `n_epochs` is the number of epoch files the bundle
ships. Every value and every current policy log probability used at step `s` is evaluated
under the epoch `e(s)` snapshot. Nothing evaluated at an earlier step is carried forward.

## 7. Sampling

Let `N` be the number of registered segments and `P` the sum of the priorities of all `N`
ledger entries, resident or not. When `N` is `0` or `P` is not greater than `0.0`, the step
makes no draws. Otherwise the step makes exactly `batch_size` draws using the sampler in
`/app/docs/sampler.md`.

Each draw is resolved in draw order. A draw landing on a ledger entry whose segment is not
resident at this step is rejected. Rejected draws are counted, are not replaced by another
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

- `terminated`: `0.0`
- `truncated`: the value of `cut_obs_id` of the stopping transition
- `window`: the value of the observation of the next transition in the episode, whether or
  not that transition is currently admitted or resident

Value targets and advantages are

    target[L]   = v[L]
    delta[k]    = rho[k] * (reward[k] + gamma * v[k+1] - v[k])
    target[k]   = v[k] + delta[k] + gamma * c[k] * (target[k+1] - v[k+1])
    advantage[k] = rho[k] * (reward[k] + gamma * target[k+1] - v[k])

evaluated for `k` from `L - 1` down to `0`. Note that `delta[k]` uses the raw snapshot value
`v[k+1]` while `advantage[k]` uses the corrected `target[k+1]`.

## 9. Replay correction weight

For an accepted draw on ledger position `p`, using the priority `P_p` that entry held at the
start of the step and the same `N` and `P` the sampler used,

    w_raw = (N * (P_p / P)) ** (-beta)

The reported weight is `w_raw` divided by the largest `w_raw` among the accepted draws of
that same step. Rejected draws take no part in that maximum.

## 10. Priority write back

For each accepted draw the new priority of the segment is

    p_new = (mean(|advantage[k]|) + priority_eps) ** alpha

with the mean taken over the segment's own transitions. All priority write backs of a step
are applied after every draw of that step has been resolved, so the priorities the sampler
and the weights use are the values held at the start of the step. When an entry is drawn
more than once in a step, the value written is the same and is written once.

## 11. Step aggregates

- `mean_vtrace_target` is the mean of `target[k]` pooled over every accepted draw of the
  step and every `k` in the drawn segment, counting repeated draws separately.
- `mean_pg_advantage` is the mean of `advantage[k]` pooled the same way.
- `mean_is_weight` is the mean of the normalised weight of section 9 over the accepted draws
  of the step, counting repeated draws separately.
- `priority_sum_after` is the sum of the priorities of all `N` ledger entries after the
  step's write backs.

When a step makes no accepted draw, `mean_vtrace_target`, `mean_pg_advantage` and
`mean_is_weight` are all `0.0`. When a step makes no draw at all, the count of rejected
draws is `0` and `priority_sum_after` is the ledger sum, which is `0.0` while the ledger is
empty.

## 12. Run totals

- `transitions_enqueued`: transitions admitted to the buffer over the whole run.
- `segments_registered`: ledger entries created over the whole run.
- `segments_evicted`: ledger entries whose segment is not resident at the end of the final
  learner step, using the residency rule of section 3 with the final admitted count.
- `draws`: draws attempted over the whole run, accepted and rejected together.
- `draws_accepted`: draws accepted over the whole run.
- `unique_segments_drawn`: distinct ledger positions accepted at least once over the run.
- `priority_sum_final`: ledger priority sum after the final learner step.
