# Importance weights (normative)

Summary means average over indices with `terminated=false` (truncated rows stay in the mass).
Raise each retained row `is_weight` to `meta.is_power`, then clip into
`[meta.is_clip_low, meta.is_clip_high]`, renormalize the clipped weights so they sum to one
over the mass set, and form the weighted mean.

If every index is terminated, use the full horizon with the same power-clip-renormalize rule.
