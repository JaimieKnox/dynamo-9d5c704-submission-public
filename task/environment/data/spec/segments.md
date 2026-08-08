# Segments and cut bootstraps (normative)

Successor value `V_next` and reverse-time eligibility are constrained by the following
invariants. Registration defines the lagged streams; this file states which bootstrap source
each cut path may read and which cuts zero eligibility.

Termination: if `terminated[t]` then `V_next[t] = 0` and the successor non-terminal factor is 0.
Termination dominates truncation.

Pure mid-segment truncation: when `truncated[t]` holds, the next index exists, and that next
index shares `segment[t]`, read **raw** `critic_b` at a residency index that walks back at most
`resid_lag` steps without leaving the segment (default `resid_lag` is 0). Do not use the lagged
registered bootstrap stream on this path. The non-terminal factor is 1.

Segment-edge / final index: when the next index is missing or belongs to another segment
(including single-index segments), `V_next[t]` equals the **registered** bootstrap critic
frozen at that segment's open index. The non-terminal factor is 1.

Interior continuation: otherwise `V_next[t]` equals the registered bootstrap critic at `t+1`,
non-terminal factor 1.

Reverse-time recurrence:
- Zero the lambda accumulator immediately before updating an index that ends a segment.
- Effective reward scale follows `scale_lag` pads (first `K` indices of a non-initial segment
  inherit the previous segment's scale).
- Eligibility is zero on truncation, on open-freeze seam edges, on scale-lag pads, and on
  value-pad indices from registration.md. Otherwise eligibility equals the successor
  non-terminal factor. Implement these cuts through the shared eligibility helper rather than a
  private disagreeing copy.
- The reverse-time discount is `gamma_lambda`. The TD residual discount is `gamma`.
- When `segment_lambdas` is present, the lambda multiplier at index `t` is
  `segment_lambdas[segment[t]]`; otherwise it is pack `lambda`.
