# Segments and cut bootstraps (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]` before
   updating index `t`.
2. For non-terminated rows, if `t` is final or `segment[t] != segment[t+1]`, successor value
   is `meta.bootstrap_value` with non-terminal multiplier one.
3. For non-terminated rows continuing inside a segment, successor value is the registered
   `critic_b` stream at `t+1` (lag `lag_b`, fill `init_b`).
4. `terminated=true` zeros successor value and non-terminal multiplier even when `truncated`
   is also true. Pure truncation alone does not zero the successor channels.
5. Before the TD residual, multiply `reward[t]` by `segment_scales[segment[t]]`.
