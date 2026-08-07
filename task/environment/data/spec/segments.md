# Segments and cut bootstraps (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]`.
2. Pure truncation inside a segment (`t+1` exists and shares `segment[t]`): successor value
   is the **raw** `value[t+1]` column (not the registered critic at `t+1`).
3. Pure truncation on a segment edge (no next index, or next index in another segment):
   successor value is `meta.bootstrap_value`.
4. Continuing rows inside a segment use the **registered** critic at `t+1`.
5. Continuing rows on a segment edge use `meta.bootstrap_value`.