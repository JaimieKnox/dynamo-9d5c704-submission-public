# Segments and cut bootstraps (normative)

Successor value `V_next` and reverse-time eligibility are constrained by the following
invariants. Registration (registration.md) defines the lagged streams; this file states which
bootstrap source each cut path may read.

Termination: if `terminated[t]` then `V_next[t] = 0` and the successor non-terminal factor is 0.
Termination dominates truncation.

Pure mid-segment truncation: when `truncated[t]` holds, the next index exists, and that next
index shares `segment[t]`, `V_next[t]` equals the **raw** `critic_b` at residency index
`t* = max(segment_open(t), t - resid_lag)` with `resid_lag` defaulting to 0 (so `t* = t`).
The non-terminal factor is 1. Do not read the lagged registered bootstrap stream for this path.

Segment-edge / final index: when the next index is missing or belongs to another segment
(including single-index segments), `V_next[t]` equals the **registered** bootstrap critic
frozen at that segment's open index. The non-terminal factor is 1.

Interior continuation: otherwise `V_next[t]` equals the registered bootstrap critic at `t+1`,
non-terminal factor 1.

Reverse-time recurrence:
- The lambda accumulator is zero immediately before updating an index that ends a segment.
- Effective reward scale uses `scale_lag = K` (default 0): the first `K` indices of a segment
  with a previous segment inherit that previous segment's scale; later indices use the current
  segment's scale. Segment 0 always uses its own scale. See the shared scale helper contract.
- Truncation leaves the bootstrap inside the TD residual, but reverse-time eligibility through
  a truncated index is zero.
- An index whose `V_next` used the segment-open freeze path also zeros reverse-time eligibility,
  even when the non-terminal factor is 1.
- An index that is inside a `scale_lag` pad (inherits previous-segment scale) also zeros
  reverse-time eligibility. This cut is independent of truncation and open-freeze cuts.
- Otherwise (no truncation cut, no open-freeze cut, no scale-lag pad cut),
  `eligibility_t` equals the successor non-terminal factor `next_nonterminal_t`.
- The reverse-time lambda multiplier uses `gamma_lambda` (default `gamma`), not `gamma`.
