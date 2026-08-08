# Importance weights (normative)

`mean_advantage` is an importance-weighted mean over a mass set of non-terminated indices.

Open-frozen weight snapshot: for every index `t`, let `t0` be the open index of `segment[t]`.
Before membership is chosen,
`w_snap[t] = clip(is_weight[t0] ** is_power, is_clip_low, is_clip_high)`
with `is_power` defaulting to 1. Live per-index `is_weight[t]` must not replace the open freeze.

Advantage mass membership (shared mass helper, not a private disagreeing predicate):
- drop terminated indices
- drop open-freeze seam-edge indices whose open freeze depended on a lag source that crossed a
  seam or required an init pad (including single-index segments)
- drop `scale_lag` pad indices (same membership notion as the scale-pad eligibility cut)

Fallback: if advantage membership is empty, use all non-terminated indices, then the full
horizon, with equal weights of one (not `w_snap`).

Otherwise renormalize surviving `w_snap` to sum to one.

Return mass (for `mean_return` only): average `R_t` over non-terminated indices that are not
inside a `scale_lag` pad. If that set is empty, fall back to all non-terminated indices, then
the full horizon. `w_snap` and open-freeze seam cuts do not apply to return mass.
