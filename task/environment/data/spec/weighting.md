# Importance weights (normative)

Summary means average over a mass set drawn from indices with `terminated=false`.

Before drawing the mass set, freeze
`w_snap[t] = clip(is_weight[t] ** meta.is_power, meta.is_clip_low, meta.is_clip_high)`.
If `is_power` is absent, treat it as `1`.

Honor the seam-edge mask from cut-mask construction: exclude any masked index whose
segment-open freeze depended on a lag source that crossed a seam or required an init pad.
Single-index segments are seam edges; they are excluded under the same open-freeze lag rule.

If the mass set is empty after exclusions, fall back to all non-terminated indices, then the
full horizon. Fallback mass uses equal weights of one, not `w_snap`.

Otherwise renormalize surviving `w_snap` values to sum to one and form the weighted mean.
