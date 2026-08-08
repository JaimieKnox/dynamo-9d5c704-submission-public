# Importance weights (normative)

`mean_advantage` is an importance-weighted mean over a mass set of non-terminated indices.

Open-frozen weight snapshot: for every index `t`, let `t0` be the open index of `segment[t]`.
Before membership is chosen,
`w_snap[t] = clip(is_weight[t0] ** is_power, is_clip_low, is_clip_high)`
with `is_power` defaulting to 1. Live per-index `is_weight[t]` must not replace the open freeze.

Advantage mass membership (shared mass helper):
- drop terminated indices
- drop open-freeze seam-edge indices whose open freeze depended on a lag source that crossed a
  seam or required an init pad
- drop `scale_lag` pad indices
- drop value-pad indices (registered `critic_a` read init)

Fallback: if advantage membership is empty, use all non-terminated indices, then the full
horizon, with equal weights of one (not `w_snap`).

Otherwise renormalize surviving `w_snap` to sum to one.

Return mass (for `mean_return` only): average emitted `return` over non-terminated indices that
are neither scale-lag pads nor value pads. If that set is empty, fall back to all non-terminated
indices, then the full horizon. `w_snap` and open-freeze seam cuts do not apply to return mass.
