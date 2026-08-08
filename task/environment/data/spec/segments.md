# Segments and cut bootstraps (normative)

Properties the successor value `V_next` and eligibility must satisfy for every index `t`:

- If `terminated[t]` is true, both `V_next[t]` and the successor non-terminal factor are zero.
  Termination dominates truncation when both flags are set.
- Otherwise, if the row is a pure truncation that still continues inside the same segment,
  `V_next[t]` equals the registered bootstrap critic at that same index `t`, and the
  non-terminal factor is one.
- Otherwise, if the row ends a segment (final index, or next index has a different segment,
  including single-index segments), `V_next[t]` equals the registered bootstrap critic frozen
  at that segment's open index, and the non-terminal factor is one.
- Otherwise `V_next[t]` equals the registered bootstrap critic at `t+1`, non-terminal factor one.

Reverse-time recurrence properties:
- The lambda accumulator is zero immediately before updating an index that ends a segment.
- The reward entering the TD residual is the raw reward multiplied by an effective segment
  scale. With `scale_lag = K` (default 0), the first `K` indices of a segment use the previous
  segment's scale; later indices use the current segment's scale. Segment 0 always uses its own
  scale.
- Truncation leaves the bootstrap inside the TD residual, but the reverse-time eligibility
  factor for carrying the lambda state through a truncated index is zero.
- An index whose `V_next` was resolved by the segment-open freeze path also zeros that same
  reverse-time eligibility factor. This cut is independent of the truncation cut and applies
  even when the non-terminal factor is one.
