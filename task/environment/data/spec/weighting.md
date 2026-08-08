# Importance weights (normative)

Open-frozen weight snapshot: for every index `t`, let `t0` be the open index of `segment[t]`.
`w_snap[t] = clip(is_weight[t0] ** is_power, is_clip_low, is_clip_high)` with `is_power`
defaulting to 1.

Advantage mass membership:
- drop terminated indices
- drop open-freeze seam-edge indices whose open freeze depended on a lag source that crossed a
  seam or required an init pad
- drop `scale_lag` pad indices
- drop value-pad indices

Fallback: if empty, use all non-terminated indices, then the full horizon, with equal weights
of one, averaging raw advantages.

Otherwise: form the importance-weighted mean over the mass set of
`advantage[t] * effective_scale[t]`, using surviving `w_snap` renormalized to sum to one.
Emitted `steps[].advantage` values remain the raw reverse-time accumulator (not scale-scored).

Return mass: average emitted `return` over non-terminated indices that are neither scale-lag
pads nor value pads, with the same empty-set fallback as above. No scale-scoring. No `w_snap`.
