# Pack format (normative)

Each pack directory under `/app/traces` has `meta.json` and `trajectory.jsonl`.

`meta.json` keys: `pack`, `gamma`, `lambda`, `horizon`, `lag_a`, `lag_b`, `init_a`, `init_b`,
`segment_scales`, `is_clip_low`, `is_clip_high`, and optional `is_power` (default 1).
A legacy `bootstrap_value` key may appear; ignore it.

`trajectory.jsonl` keys: `index`, `reward`, `critic_a`, `critic_b`, `terminated`, `truncated`,
`segment`, `is_weight`.

Stream roles, edges, truncation residency, eligibility, and mass algebra are defined in
`registration.md`, `segments.md`, and `weighting.md`.
