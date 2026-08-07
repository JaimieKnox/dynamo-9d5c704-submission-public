# Segments and cut bootstraps (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]`.
2. For a pure truncation at `t`, if `t` is the last index of its segment (next index missing
   or in another segment), the successor value is `meta.bootstrap_value`, not the next row's
   registered critic. Intra-segment truncations still use the next registered critic.
3. Continuing rows that sit on a segment edge likewise use `bootstrap_value` rather than the
   next segment's critic.