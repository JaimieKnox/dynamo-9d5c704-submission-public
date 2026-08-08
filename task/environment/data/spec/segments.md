# Segments and cut bootstraps (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]` before
   updating index `t`.
2. At each segment open index (first row of that segment id), freeze the already-registered
   `critic_b` stream value. Call that freeze the segment-open bootstrap for the segment.
3. For non-terminated rows, if `t` is final or `segment[t] != segment[t+1]`, successor value
   is that segment's segment-open bootstrap (not a live register read at `t+1`, and not a
   pack-level constant), with non-terminal multiplier one.
4. For non-terminated rows continuing inside a segment, successor value is the registered
   `critic_b` stream at `t+1`.
5. `terminated=true` zeros successor value and non-terminal multiplier even when `truncated`
   is also true. Pure truncation alone does not zero the successor channels.
6. Before the TD residual, multiply `reward[t]` by `segment_scales[segment[t]]`.
7. While resolving successors, record a seam-edge mask bit for every non-terminated index
   that used rule (3). The summary mass rules in `weighting.md` consume that same mask.

## Worked example

Horizon indices `0..5`, segments `[0,0,0,1,1,1]`, `lag_b=2`, `init_b=0.25`. After
seam-invalidated registration, segment 1 opens at index 3. The lag source for index 3 is
`3-2=1`, which lies in segment 0, so the registered bootstrap at the open is `init_b=0.25`.
That frozen `0.25` is the successor value for the segment-0 edge at index 2 and for the
final index 5 (segment 1's open freeze), not the raw live critic at those edges.
