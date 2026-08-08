# Importance weights (normative)

Summary means are taken over a mass set of non-terminated indices.

Weight snapshot property: before membership is chosen,
`w_snap[t] = clip(is_weight[t] ** is_power, is_clip_low, is_clip_high)` with `is_power`
defaulting to 1.

Membership property: an index whose successor used an open-freeze path is excluded from the
mass set when that freeze depended on a lag source that crossed a seam or required an init
pad. This includes single-index segments. Do not invent a private edge predicate that
disagrees with the successor open-freeze path.

Fallback property: if membership is empty, use all non-terminated indices, then the full
horizon, with equal weights of one (not `w_snap`).

Otherwise the mean uses `w_snap` renormalized to sum to one on the surviving membership.
