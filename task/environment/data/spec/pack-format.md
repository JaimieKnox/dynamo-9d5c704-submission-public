# Pack format (normative)

Each pack directory under `/app/traces` has `meta.json` and `trajectory.jsonl`.

`meta.json` keys: `pack`, `gamma`, `lambda`, `horizon`, `lag_a`, `lag_b`, `init_a`, `init_b`,
`segment_scales` (array of floats, one per segment id), `is_clip_low`, `is_clip_high`.
A legacy `bootstrap_value` key may appear; ignore it. Segment-edge and final successors use
the segment-open frozen `critic_b` registration described in `segments.md`.

`trajectory.jsonl` keys: `index`, `reward`, `critic_a`, `critic_b`, `terminated`, `truncated`,
`segment`, `is_weight`.

## Streams

The reverse-time state value at index `t` is the lag-`lag_a` registration of `critic_a`
(with fill `init_a` and seam-invalidated lag pads). Successor bootstraps that need a next
critic read the lag-`lag_b` registration of `critic_b` (with fill `init_b` and the same
seam rule). Do not use one stream for both roles.

## Edges and mass

Edge successor selection, segment-open freezes, reverse-time resets, reward scales, and the
pre-draw clip plus seam-exclusion mass algebra are defined in `segments.md` and
`weighting.md`. This file only defines fields and stream roles.
