# Segments and timeout edges (normative)

Each row has integer `segment`.

1. Reverse-time lambda accumulator resets to zero when `segment[t] != segment[t+1]` before
   updating index `t`.
2. Pure truncation inside a continuing segment (`truncated=true`, `terminated=false`, and
   `t+1` exists with the same segment) uses the registered `critic_b` stream at the same
   index `t` as the successor value, with non-terminal multiplier one.
3. Pure truncation on a segment edge or final index uses `meta.bootstrap_value` with
   non-terminal multiplier one.
4. Non-truncated continuing rows inside a segment use registered `critic_b` at `t+1`.
5. Non-truncated final or segment-edge rows use `meta.bootstrap_value`.
6. `terminated=true` zeros successor value and non-terminal multiplier even when `truncated`
   is also true.
7. Before the TD residual, multiply `reward[t]` by `segment_scales[segment[t]]`.
8. After forming the TD residual, the reverse-time eligibility factor uses non-terminal
   multiplier zero on truncated rows (timeout cuts keep the bootstrap inside the residual
   but do not carry lambda eligibility through the cut). Non-truncated rows use the
   successor non-terminal multiplier from the rules above.
