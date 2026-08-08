# Pack format (normative)

Each pack under `/app/traces` has `meta.json` and `trajectory.jsonl`.

`meta.json` keys: `pack`, `gamma`, `lambda`, `horizon`, `lag_a`, `lag_b`, `init_a`, `init_b`,
`segment_scales`, `is_clip_low`, `is_clip_high`, optional `is_power` (default 1), optional
`scale_lag` (default 0), optional `gamma_lambda` (default equals `gamma`), optional `resid_lag`
(default 0), optional `segment_lambdas`, optional `segment_gammas`. Legacy `bootstrap_value`
may appear and must be ignored.

When `segment_lambdas` is present it overrides pack `lambda` per segment index.
When `segment_gammas` is present it overrides pack `gamma` for the TD residual per segment
index. `gamma_lambda` is never replaced by `segment_gammas`.

`trajectory.jsonl` keys: `index`, `reward`, `critic_a`, `critic_b`, `terminated`, `truncated`,
`segment`, `is_weight`.
