# Importance weights (normative)

Summary means average over a mass set drawn from indices with `terminated=false`
(truncated rows may stay in). Build the mass set only after successor resolution.

Before drawing the mass set, freeze a clipped snapshot of every row weight:
`w_snap[t] = clip(is_weight[t], meta.is_clip_low, meta.is_clip_high)`.
Later renormalization must use `w_snap`, not a second live clip pass.

Cut-mask construction records a per-index seam-edge mask for non-terminated final or
segment-boundary rows that took a segment-open bootstrap. The ledger must honor that mask
when building the mass set: exclude any masked index whose segment-open freeze depended on
a lag source that crossed a seam or required an init pad (`open_index - lag_b` out of range
or in another segment). Do not re-derive a private edge predicate that can disagree with
the mask used for successors. Those rows still emit per-index advantages and returns; they
only leave the summary weight pool.

Renormalize the surviving `w_snap` values so they sum to one over the mass set, then form
the weighted mean. If the mass set is empty after exclusions, fall back to all
non-terminated indices (then the full horizon if every index terminated), still using the
pre-draw `w_snap` values.
