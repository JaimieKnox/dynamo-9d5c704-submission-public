# Importance weights (normative)

Summary means average over indices with `terminated=false` (truncated rows stay in the mass).
Clip each row `is_weight` into `[meta.is_clip_low, meta.is_clip_high]`, renormalize the
clipped weights so they sum to one over the mass set, then form the weighted mean.

If every index is terminated, use the full horizon with the same clip-then-renormalize rule.
