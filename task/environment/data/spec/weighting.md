# Importance weights (normative)

Summary means are weighted over indices with `terminated=false` using each row's
`is_weight`, after clipping into `[meta.is_clip_low, meta.is_clip_high]`:

`mean = sum (clip(is_weight_i) * x_i) / sum clip(is_weight_i)`

If every index is terminated, fall back to the full horizon with the same clipped weights.
Truncated but non-terminated indices stay in the mass.